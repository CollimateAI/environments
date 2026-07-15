# browser

Playwright 1.61 (Python) with headless Chromium and all of its system
dependencies installed at a fixed path (`/ms-playwright`).

**Best for:** browser agents, web-automation rollouts, and scraping evals.
Forking is what makes this one interesting: every fork is a fully isolated
browser environment — its own cookies, its own storage, its own process tree —
so a thousand parallel browsing rollouts never step on each other.

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("browser")
r = client.exec(sb["id"], commands=[["bash", "-lc", """
python - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    page.goto("https://example.com")
    print(page.title())
PY
"""]], timeout_seconds=120)
print(r["stdout"])
```

Chromium is launched once during the image build (a real page render), so a
green build guarantees a working browser. Outbound navigation follows your
sandbox's egress policy.
