# syntax=docker/dockerfile:1.7
# browser: Playwright (Python) + Chromium, headless-ready. The browser-agent
# sandbox — every fork gets its own isolated browser with its own state.
# (The syntax directive above must stay the first line — it enables the BuildKit
# frontend that supports the RUN <<'PY' heredoc used in the build-time check.)
FROM python:3.12-slim@sha256:c3d81d25b3154142b0b42eb1e61300024426268edeb5b5a26dd7ddf64d9daf28

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN pip install playwright==1.61.0

# Chromium + its system dependencies, then drop the apt lists to keep the image lean.
RUN playwright install --with-deps chromium \
 && rm -rf /var/lib/apt/lists/*

# Prove the whole stack at build time: launch headless Chromium, render a page.
RUN python - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content("<title>collimate</title>")
    assert page.title() == "collimate"
    browser.close()
print("browser ready")
PY

# --- Live-browser warm script (the ready-state recipe) --------------------------
# Collimate runs this as the template's warm command at bake time. It launches a
# persistent headless Chromium with the CDP endpoint listening on 127.0.0.1:9222
# and blocks until CDP answers. Because Chromium is left RUNNING (setsid-detached),
# the ready-state snapshot captures a LIVE browser — every fork wakes with Chromium
# already up, so a rollout attaches in milliseconds via connect_over_cdp instead of
# paying a ~2-4s per-fork browser launch. This is the difference between a "warm
# caches" template and a true live-service template.
# The CDP endpoint itself is loopback-only by Chromium's choice: since 132 there
# is ONLY the new headless mode, which ignores --remote-debugging-address and
# always binds 127.0.0.1:9222 (verified on 149). Host→guest ingress
# (ready.exposePorts DNAT) terminates at the guest NIC address, so a tiny
# stdlib relay publishes the CDP server there: NIC:9222 → 127.0.0.1:9222.
# Version-proof — no dependency on Chromium bind flags surviving upgrades.
COPY <<'RELAY' /usr/local/bin/cdp-relay
#!/usr/bin/env python3
"""TCP relay: publish the loopback-only CDP endpoint on another address.

Usage: cdp-relay [LISTEN_HOST:PORT] [TARGET_HOST:PORT]
Defaults: 10.0.2.15:9222 (the baked guest NIC address) → 127.0.0.1:9222.
The listen address may not exist yet when this starts (the NIC comes up on its
own schedule at warm time), so the bind is retried for up to 10 minutes.
"""
import socket, sys, threading, time


def pump(a, b):
    try:
        while True:
            d = a.recv(65536)
            if not d:
                break
            b.sendall(d)
    except OSError:
        pass
    finally:
        for s in (a, b):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def main():
    listen = sys.argv[1] if len(sys.argv) > 1 else "10.0.2.15:9222"
    target = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1:9222"
    lh, lp = listen.rsplit(":", 1)
    th, tp = target.rsplit(":", 1)
    deadline = time.time() + 600
    while True:
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((lh, int(lp)))
            srv.listen(64)
            break
        except OSError:
            srv.close()
            if time.time() > deadline:
                sys.exit(1)
            time.sleep(0.5)
    print("relay up", listen, "->", target, flush=True)
    while True:
        c, _ = srv.accept()
        c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            u = socket.create_connection((th, int(tp)), timeout=5)
            u.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            c.close()
            continue
        threading.Thread(target=pump, args=(c, u), daemon=True).start()
        threading.Thread(target=pump, args=(u, c), daemon=True).start()


main()
RELAY

COPY <<'WARM' /usr/local/bin/collimate-warm
#!/bin/sh
set -e
# Loopback must be UP before Chromium binds its CDP server, or 127.0.0.1:9222 is
# unreachable inside the guest at warm time (the per-fork netns brings lo up later,
# but the bake/warm phase does not). Harmless if already up / not permitted.
ip link set lo up 2>/dev/null || true
# Resolve Chromium's real binary via Playwright — version-robust (the on-disk path,
# e.g. /ms-playwright/chromium-1228/chrome-linux64/chrome, changes across releases).
CH=$(python3 -c "from playwright.sync_api import sync_playwright as x; p=x().start(); print(p.chromium.executable_path); p.stop()")
# Launch detached (survives the warm command exiting → present in the snapshot).
# Chromium ≥132 ships ONLY the new headless mode: --remote-debugging-address is
# ignored and CDP always binds 127.0.0.1:9222 — NIC-side exposure is cdp-relay's
# job (below), never a bind flag. A dedicated --user-data-dir keeps the profile
# on tmpfs. dbus warnings are harmless.
setsid "$CH" --headless --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/cdp-profile about:blank \
  >/var/log/cdp.log 2>&1 < /dev/null &
# Publish CDP on the guest NIC (10.0.2.15 — the platform's baked guest address)
# for host→guest ingress. Detached like Chromium, so it lives in the snapshot;
# it retries its bind until the NIC address exists.
setsid /usr/local/bin/cdp-relay 10.0.2.15:9222 127.0.0.1:9222 \
  >/var/log/cdp-relay.log 2>&1 < /dev/null &
# Block until CDP is actually serving, so the snapshot is only taken once the
# browser is genuinely ready (not merely spawned).
for i in $(seq 1 60); do
  if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9222/json/version', timeout=1)" 2>/dev/null; then
    echo cdp-ready; exit 0
  fi
  sleep 1
done
echo cdp-timeout >&2; exit 1
WARM
RUN chmod +x /usr/local/bin/collimate-warm /usr/local/bin/cdp-relay && /usr/local/bin/collimate-warm

# --- Raw-CDP fast-path navigator (Python stdlib only) ---------------------------
# `cdp-nav <url>` drives the ALREADY-RUNNING headless Chromium directly over the
# Chrome DevTools Protocol websocket. Unlike Playwright's connect_over_cdp(), it
# starts no Node driver — it speaks CDP with a tiny stdlib WebSocket client — so
# attach-and-navigate is milliseconds instead of the ~1.5-2s Playwright pays to
# boot its own driver on every call. Use this when per-rollout latency is the
# bottleneck. Depends only on the resident browser; no extra packages.
#
#   cdp-nav <url> [--port 9222] [--timeout 30] [--expr <js>]
#
# Prints "<title>\t<current-url>" of the loaded page by default, or the --expr
# Runtime.evaluate result if given; exit 0 once the page load event fires.
COPY <<'CDPNAV' /usr/local/bin/cdp-nav
#!/usr/bin/env python3
# Collimate — raw-CDP navigate client (stdlib only, no websocket package, no Node).
import base64, json, os, socket, struct, sys, time, urllib.request


def http_get(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read().decode()


def find_page_ws(host, port, timeout=10):
    """Return a page target's webSocketDebuggerUrl, creating one if none exists."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            for t in json.loads(http_get(f"http://{host}:{port}/json")):
                if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                    return t["webSocketDebuggerUrl"]
            # No page tab yet -> ask the browser to open one.
            try:
                t = json.loads(http_get(f"http://{host}:{port}/json/new?about:blank"))
                if t.get("webSocketDebuggerUrl"):
                    return t["webSocketDebuggerUrl"]
            except Exception:
                pass
        except Exception:
            pass
        time.sleep(0.05)
    raise RuntimeError(f"no CDP page target on {host}:{port} within {timeout}s")


class WS:
    """Minimal client-side WebSocket for the CDP page endpoint."""

    def __init__(self, url, timeout=30):
        # url: ws://host:port/devtools/page/<id>
        body = url[len("ws://"):]
        hostport, path = body.split("/", 1)
        path = "/" + path
        host, port = hostport.split(":")
        self.s = socket.create_connection((host, int(port)), timeout=timeout)
        self.s.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET {path} HTTP/1.1\r\nHost: {hostport}\r\n"
               "Upgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
        self.s.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            c = self.s.recv(4096)
            if not c:
                raise RuntimeError("CDP ws handshake closed")
            buf += c
        if b" 101 " not in buf.split(b"\r\n", 1)[0]:
            raise RuntimeError("CDP ws handshake failed: " + buf[:80].decode("latin1"))
        self.rest = buf.split(b"\r\n\r\n", 1)[1]

    def _recv(self, n):
        while len(self.rest) < n:
            c = self.s.recv(65536)
            if not c:
                raise RuntimeError("CDP ws closed")
            self.rest += c
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def send(self, obj):
        payload = json.dumps(obj).encode()
        mask = os.urandom(4)
        hdr = bytearray([0x81])  # FIN + text frame
        n = len(payload)
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126); hdr += struct.pack(">H", n)
        else:
            hdr.append(0x80 | 127); hdr += struct.pack(">Q", n)
        hdr += mask
        self.s.sendall(bytes(hdr) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def recv(self):
        """Return one decoded JSON message (handles ping/pong + fragmentation)."""
        data = b""
        while True:
            b0, b1 = self._recv(2)
            op = b0 & 0x0f
            ln = b1 & 0x7f
            if ln == 126:
                ln = struct.unpack(">H", self._recv(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._recv(8))[0]
            frame = self._recv(ln) if ln else b""
            if op == 0x9:      # ping -> pong
                self._pong(frame); continue
            if op == 0x8:      # close
                raise RuntimeError("CDP ws closed by browser")
            data += frame
            if b0 & 0x80:      # FIN
                return json.loads(data.decode())

    def _pong(self, payload):
        mask = os.urandom(4)
        hdr = bytes([0x8a, 0x80 | len(payload)]) + mask
        self.s.sendall(hdr + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("usage: cdp-nav <url> [--port N] [--timeout S] [--expr JS]\n")
        return 2
    url = args[0]
    port, timeout, expr = 9222, 30, None
    i = 1
    while i < len(args):
        if args[i] == "--port":
            port = int(args[i + 1]); i += 2
        elif args[i] == "--timeout":
            timeout = int(args[i + 1]); i += 2
        elif args[i] == "--expr":
            expr = args[i + 1]; i += 2
        else:
            i += 1

    ws_url = find_page_ws("127.0.0.1", port, timeout=timeout)
    ws = WS(ws_url, timeout=timeout)
    ws.send({"id": 1, "method": "Page.enable"})
    ws.send({"id": 2, "method": "Page.navigate", "params": {"url": url}})

    # Wait for the load event (or frameStoppedLoading) before reading the page.
    deadline = time.time() + timeout
    loaded = False
    while time.time() < deadline:
        msg = ws.recv()
        if msg.get("id") == 2 and "error" in msg:
            sys.stderr.write("navigate error: %s\n" % msg["error"]); return 1
        if msg.get("method") in ("Page.loadEventFired", "Page.frameStoppedLoading"):
            loaded = True; break
    if not loaded:
        sys.stderr.write("timed out waiting for page load\n"); return 1

    # Read a result: the caller's --expr, or the page title + current URL by default.
    expression = expr or "JSON.stringify([document.title, location.href])"
    ws.send({"id": 3, "method": "Runtime.evaluate",
             "params": {"expression": expression, "returnByValue": True}})
    while time.time() < deadline:
        msg = ws.recv()
        if msg.get("id") == 3:
            if "error" in msg:
                sys.stderr.write("eval error\n"); return 1
            val = msg.get("result", {}).get("result", {}).get("value")
            if expr is None:
                try:
                    title, cur = json.loads(val)
                    sys.stdout.write(f"{title}\t{cur}\n")
                except Exception:
                    sys.stdout.write((val if isinstance(val, str) else json.dumps(val)) + "\n")
            else:
                sys.stdout.write((val if isinstance(val, str) else json.dumps(val)) + "\n")
            return 0
    sys.stderr.write("timed out waiting for result\n"); return 1


if __name__ == "__main__":
    sys.exit(main())
CDPNAV
# Self-test the fast path at build time. Each RUN is a fresh container — the
# Chromium the warm script launched in an earlier layer does NOT persist here, so
# start a browser in THIS layer (the warm script blocks until CDP answers), then
# navigate to a data: URL (no network needed at build time) and check the title.
RUN chmod +x /usr/local/bin/cdp-nav \
 && /usr/local/bin/collimate-warm >/dev/null \
 && OUT=$(/usr/local/bin/cdp-nav "data:text/html,<title>cdp-ok</title>" --timeout 20) \
 && echo "cdp-nav: $OUT" \
 && case "$OUT" in cdp-ok*) : ;; *) echo "cdp-nav self-test failed" >&2; exit 1 ;; esac \
 # Relay self-test: the guest NIC does not exist in a build container, so prove
 # the relay mechanics on a loopback alias instead — /json/version fetched
 # THROUGH the relay must answer (the non-loopback bind path is exercised at
 # bake by the veth connect).
 && (setsid /usr/local/bin/cdp-relay 127.0.0.2:9222 127.0.0.1:9222 >/tmp/relay-test.log 2>&1 < /dev/null &) \
 && sleep 1 \
 && python3 -c "import urllib.request,json; v=json.load(urllib.request.urlopen('http://127.0.0.2:9222/json/version', timeout=5)); print('relay:', v['Browser'])"

# ---------------------------------------------------------------------------------
# Pro browser-RL note (persistent auth / secrets):
#   Do NOT bake cookies, tokens, or credentials into this image or the ready state —
#   the snapshot is a shared catalog artifact. Instead:
#     • Inject secrets at RUNTIME via Collimate's secret store (write-only, sealed to
#       the node; they reach the sandbox's credential proxy, never the artifact).
#       See the Secrets guide at https://docs.collimate.ai for the current API.
#     • For a logged-in browser state, do the login INSIDE the rollout on first use
#       and persist storage_state to the sandbox's own disk (per-fork, never shared),
#       or drive auth through the injected secret. Egress must be open (Pro tier).
# See the environment cookbook: docs/cookbook/live-browser.md.
# ---------------------------------------------------------------------------------

WORKDIR /workspace
CMD ["sleep", "infinity"]
