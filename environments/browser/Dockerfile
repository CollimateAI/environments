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
# CRITICAL: use OLD --headless, NOT --headless=new — Chromium 124+ ignores
# --remote-debugging-address under --headless=new and binds 127.0.0.1 only. Bind
# 0.0.0.0 so the CDP endpoint is reachable both on loopback (in-guest exec) and on
# the per-fork veth address (host→guest DNAT via ready.exposePorts). A dedicated
# --user-data-dir keeps the profile on tmpfs. dbus warnings are harmless.
setsid "$CH" --headless --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0 \
  --user-data-dir=/tmp/cdp-profile about:blank \
  >/var/log/cdp.log 2>&1 < /dev/null &
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
RUN chmod +x /usr/local/bin/collimate-warm && /usr/local/bin/collimate-warm

# ---------------------------------------------------------------------------------
# Pro browser-RL note (persistent auth / secrets):
#   Do NOT bake cookies, tokens, or credentials into this image or the ready state —
#   the snapshot is a shared catalog artifact. Instead:
#     • Inject secrets at RUNTIME via Collimate's secret store (write-only, sealed to
#       the node; they reach the sandbox's credential proxy, never the artifact):
#         client.secrets.put("SITE_TOKEN", ...)  then reference at create/exec time.
#     • For a logged-in browser state, do the login INSIDE the rollout on first use
#       and persist storage_state to the sandbox's own disk (per-fork, never shared),
#       or drive auth through the injected secret. Egress must be open (Pro tier).
# See the environment cookbook: docs/cookbook/live-browser.md.
# ---------------------------------------------------------------------------------

WORKDIR /workspace
CMD ["sleep", "infinity"]
