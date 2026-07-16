# Cookbook: baking a live browser into a ready-state template

Most environments only need a **warm** ready state — imports resolved, caches hot,
so a fork skips the install/import tax. A *live-service* environment goes one step
further: a long-running process (a browser, a Jupyter kernel, a database) is started
**at bake time and left running**, so the ready-state snapshot captures it alive.
Every fork then wakes with that service already up — a rollout **attaches** to it
instead of launching it.

This is the recipe for the `browser` environment. Use it as a template for any
live-service environment.

## The idea

```
bake:  boot guest → run warm command → SNAPSHOT (service is running) → publish
fork:  restore snapshot → service is already alive → rollout attaches
```

The warm command must (1) start the service **detached** so it survives the command
returning, and (2) **block until the service is actually serving**, so the snapshot
is taken only once it is ready — not merely spawned.

## The warm script

The whole recipe is one baked script, `/usr/local/bin/collimate-warm`
([Dockerfile](../../environments/browser/Dockerfile)). Five details matter, and
each is a common way to get this wrong:

```sh
#!/bin/sh
set -e

# 1. Bring loopback up. At bake time the guest's `lo` is not yet up; the CDP
#    server binds to it, so without this the endpoint is unreachable.
ip link set lo up 2>/dev/null || true

# 2. Resolve Chromium's real binary via Playwright — never hard-code the path,
#    it moves between releases (e.g. .../chromium-1228/chrome-linux64/chrome).
CH=$(python3 -c "from playwright.sync_api import sync_playwright as x; p=x().start(); print(p.chromium.executable_path); p.stop()")

# 3. Launch DETACHED (setsid) so it outlives this script and lands in the snapshot.
#    Chromium ≥132 has ONLY the new headless mode: --remote-debugging-address is
#    ignored and the CDP server always binds 127.0.0.1:9222. Don't fight it with
#    bind flags — publish the endpoint with a relay (next step).
setsid "$CH" --headless --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/cdp-profile about:blank \
  >/var/log/cdp.log 2>&1 < /dev/null &

# 4. Publish the loopback-only CDP endpoint on the guest NIC (10.0.2.15) so
#    connect-from-outside (`ready.exposePorts` → per-fork DNAT → NIC) reaches it.
#    cdp-relay is a ~40-line baked stdlib TCP relay: NIC:9222 → 127.0.0.1:9222,
#    detached like Chromium so it lives in the snapshot, retrying its bind while
#    the NIC comes up. Version-proof: no dependency on Chromium bind behavior.
setsid /usr/local/bin/cdp-relay 10.0.2.15:9222 127.0.0.1:9222 \
  >/var/log/cdp-relay.log 2>&1 < /dev/null &

# 5. Block until CDP actually answers, so the snapshot captures a READY browser.
for i in $(seq 1 60); do
  if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9222/json/version', timeout=1)" 2>/dev/null; then
    echo cdp-ready; exit 0
  fi
  sleep 1
done
echo cdp-timeout >&2; exit 1
```

Point the environment's ready command at it (`env.yaml`):

```yaml
ready:
  cmd: /usr/local/bin/collimate-warm
  exposePorts: [9222]          # DNAT the CDP port into each fork's netns
cdp_endpoint: http://127.0.0.1:9222
```

The image **runs this script at build time as a self-test**, so a green build
proves Chromium launches and CDP answers before the image is ever baked — and it
fetches `/json/version` **through the relay** too, so the NIC-side publish path is
proven, not assumed. (That last check exists because the loopback-only poll used
to pass while Chromium silently ignored its bind flag.)

## Using it from the SDK

A rollout **attaches** to the already-running browser — it does not launch one.
There are two ways to attach: the **raw-CDP fast path** (fastest — no Node driver)
and **Playwright** (convenient). Both talk to the same live browser on `:9222`.

### Fast path: raw CDP (`cdp-nav`)

The image bakes a tiny, dependency-free (Python-stdlib-only) CDP client at
`/usr/local/bin/cdp-nav` ([Dockerfile](../../environments/browser/Dockerfile)). It
speaks the Chrome DevTools Protocol websocket directly — connects to the resident
browser, sends `Page.navigate`, waits for the load event, and prints the page title
and final URL. Because it starts **no Node driver**, attach-and-navigate is an order
of magnitude faster than Playwright (see [latency](#a-note-on-latency) below).

```python
from collimate_rl import connect

client = connect(api_key="col_...")

sb = client.create_sandbox("browser")
# Drive the live browser directly over CDP — no per-fork launch, no Node driver.
result = client.exec(
    sb["id"],
    commands=[["cdp-nav", "https://example.com"]],
    timeout_seconds=60,
)
print(result["stdout"])          # -> "Example Domain\thttps://example.com/"
client.delete_sandbox(sb["id"])
```

Pass `--expr <js>` to evaluate JavaScript in the loaded page instead of the default
title/URL (e.g. `["cdp-nav", "https://example.com", "--expr", "document.body.innerText"]`),
or `--port` / `--timeout` to override the defaults (`9222` / `30s`).

### Convenient: Playwright

`connect_over_cdp` gives you the full Playwright API — worth its extra latency when
you need rich page interaction (selectors, waits, screenshots) rather than a single
navigate.

```python
# The rollout body runs inside the sandbox. It connects to the live browser that
# the ready-state snapshot is already running — no per-fork browser launch.
ROLLOUT = """
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = browser.new_context().new_page()   # isolated context per rollout
    page.goto("https://example.com")
    print(page.title())
    browser.close()                            # closes the connection, not the browser
"""

result = client.exec(sb["id"], commands=[["python3", "-c", ROLLOUT]], timeout_seconds=60)
```

Give each rollout its own `new_context()` (fresh cookies/storage) and close the
**context**, not the browser — the browser is the shared warm service.

### Fan out with fork

Fan a warmed parent out across many rollouts with `fork` — every child inherits the
same live browser and can drive it via either path:

```python
children = client.fork(sb["id"], count=64)["children"]
for child in children:
    client.exec(child["id"], commands=[["cdp-nav", "https://example.com"]], timeout_seconds=60)
```

## A note on latency

Attaching to the pre-running browser skips the ~2s Chromium spawn a cold
`chromium.launch()` pays. The two attach paths differ by roughly another order of
magnitude. Measured in a `browser` sandbox on Collimate prod (median of 3 runs,
server-side in-guest exec time, navigating to a fixed page so the number reflects
attach + navigate, not network variance):

| Attach path | Command | Median attach + navigate |
|---|---|---|
| **Raw CDP** (`cdp-nav`) | `["cdp-nav", url]` | **~235 ms** |
| **Playwright** `connect_over_cdp` | `["python3", "-c", rollout]` | **~1350 ms** |

That is **~5.7× faster** for the raw path. Almost all of Playwright's ~1.35s is its
Node driver booting on every call; the raw-CDP path pays only Python startup plus the
CDP round-trip (the attach + `Page.navigate` itself is well under 100 ms). Reach for
`cdp-nav` when per-rollout latency is the bottleneck; reach for Playwright when you
need its full page-interaction API.

## Pro browser-RL: authentication & secrets

The ready-state snapshot is a **shared artifact**, so it must never contain
credentials — never bake cookies, tokens, or a logged-in profile into the image or
the warm state. Two patterns keep auth per-tenant and per-fork:

- **Per-fork login + `storage_state`.** Log in inside the rollout on first use and
  persist Playwright's `storage_state` to the fork's own disk (per-fork, never
  shared), so later steps in the same episode reuse the session:

  ```python
  import os
  ctx = browser.new_context(
      storage_state="/tmp/state.json" if os.path.exists("/tmp/state.json") else None
  )
  # ...perform the login flow using a runtime-injected credential...
  ctx.storage_state(path="/tmp/state.json")   # persist for subsequent steps in this fork
  ```

- **Runtime credential injection.** Keep the credential itself out of your code:
  store it in Collimate's secret store and inject it at sandbox-create time, where it
  reaches the sandbox through the sealed credential proxy — never the artifact, never
  a log. See the [Secrets guide](https://docs.collimate.ai) for the current API.

Browser networking is a **Pro** capability: demo sandboxes have no outbound network,
so real navigation (and therefore login) needs a Pro key with egress enabled, e.g.
`client.create_sandbox("browser", egress={"allow": ["example.com"]})`.

## Adapting to other live-service environments

The same warm command works for any long-running service — swap the launch line and
the readiness probe, keep the shape:

| Service | Launch (detached) | Readiness probe |
|---|---|---|
| Jupyter kernel | `setsid jupyter kernel …` | connection file exists / ZMQ ping |
| Postgres | `setsid pg_ctl start …` | `pg_isready` |
| Model server | `setsid python -m your_server …` | `GET /health` returns 2xx |

Keep it **launch detached → block until serving → exit 0**, and the service lands in
the ready-state snapshot exactly like the browser.
