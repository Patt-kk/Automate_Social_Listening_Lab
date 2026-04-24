# DOM Intelligence Scraper

A two-part toolkit for scraping **ask-dom.com** campaign comparison data:

| File | Purpose |
|---|---|
| `proxy.py` | Local CORS proxy — bridges the browser dashboard to ask-dom.com |
| `scraper.py` | Playwright headless scraper — saves data to CSV |
| `dom_dashboard.html` | Browser dashboard — visualise & export scraped data |
| `requirements.txt` | Python dependencies |

---

## Quick Start

### 1 — Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2a — Headless scrape (no browser needed)

```bash
python scraper.py --account YOUR_ACCOUNT --username YOUR_USER --password YOUR_PASS
# Output: dom_comparison.csv
```

Optional flags:

| Flag | Default | Description |
|---|---|---|
| `--account` | `test` | DOM account name |
| `--username` | `test` | DOM username |
| `--password` | `test` | DOM password |
| `--output` | `dom_comparison.csv` | Output file path |
| `--visible` | off | Show the browser window while scraping |

### 2b — Live dashboard (proxy + browser)

1. Start the proxy:
   ```bash
   python proxy.py
   # ✅  DOM Proxy running at http://localhost:5055
   ```
2. Open `dom_dashboard.html` in your browser (double-click or `open dom_dashboard.html`).
3. Enter your Account / Username / Password and click **Connect & Login**.
4. The dashboard fetches live data from the comparison page and renders it as a sortable, searchable, paginated table.
5. Click **↓ Export CSV** to download the data.

### 2c — Import an existing CSV

Open `dom_dashboard.html`, click **↑ Import CSV instead**, and drag in any `dom_comparison.csv` produced by `scraper.py`.

---

## Architecture

```
Browser (dom_dashboard.html)
      │  POST /proxy/login
      │  GET  /proxy/campaign/comparison
      ▼
proxy.py  (Flask, localhost:5055)
      │  forwards requests
      ▼
https://app.ask-dom.com   (the real site)
```

`scraper.py` is fully independent — it drives Chromium directly via Playwright and writes a CSV without needing the proxy or dashboard.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `proxy offline` badge in dashboard | Start `python proxy.py` first |
| `Expected 3 login inputs` error | The login page structure may have changed; inspect `LOGIN_URL` in `scraper.py` |
| Empty table after login | The comparison page may use a different API endpoint; check Network tab in DevTools |
| CSV has garbled columns | Use `--visible` mode to watch what Playwright actually sees |
