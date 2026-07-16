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

WORKDIR /workspace
CMD ["sleep", "infinity"]
