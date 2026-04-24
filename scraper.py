"""
Playwright scraper for https://app.ask-dom.com/campaign/comparison
- Logs in with Account / Username / Password (3-field login form)
- Waits for JS to render
- Scrapes all visible data from the comparison page
- Saves results to dom_comparison.csv

Usage:
    pip install playwright && playwright install chromium
    python scraper.py
    python scraper.py --account myacct --username myuser --password mypass
    python scraper.py --output results.csv --visible   # run with browser window
"""

import csv
import asyncio
import argparse
from playwright.async_api import async_playwright

# ── CONFIG ────────────────────────────────────────────────────────────────────
LOGIN_URL   = "https://app.ask-dom.com/login"
TARGET_URL  = "https://app.ask-dom.com/campaign/comparison"
ACCOUNT     = "test"
USERNAME    = "test"
PASSWORD    = "test"
OUTPUT_FILE = "dom_comparison.csv"
HEADLESS    = True
# ─────────────────────────────────────────────────────────────────────────────


async def login(page, account: str, username: str, password: str) -> None:
    """Navigate to the login page and fill the 3-field form."""
    print("[*] Navigating to login page...")
    await page.goto(LOGIN_URL, wait_until="networkidle")
    await page.wait_for_selector("input", timeout=10_000)

    inputs = await page.query_selector_all(
        'input[type="text"], input[type="password"], input:not([type])'
    )

    if len(inputs) < 3:
        raise RuntimeError(
            f"Expected 3 login inputs, found {len(inputs)}. "
            "Check LOGIN_URL or the page structure."
        )

    await inputs[0].fill(account)   # Account field
    await inputs[1].fill(username)  # Username field
    await inputs[2].fill(password)  # Password field

    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    print("[+] Login complete.")


async def scrape_comparison(page) -> list[list[str]]:
    """Navigate to the comparison page and extract all visible data."""
    print("[*] Navigating to comparison page...")
    await page.goto(TARGET_URL, wait_until="networkidle")

    # Extra wait for JS-heavy content to fully render
    await page.wait_for_timeout(3_000)
    print("[*] Extracting data...")

    all_rows: list[list[str]] = []

    # ── 1. Try to extract a table ──────────────────────────────────────────
    tables = await page.query_selector_all("table")
    if tables:
        for table in tables:
            rows = await table.query_selector_all("tr")
            for row in rows:
                cells = await row.query_selector_all("th, td")
                cell_texts = [(await c.inner_text()).strip() for c in cells]
                if any(cell_texts):
                    all_rows.append(cell_texts)
        print(f"[+] Extracted {len(all_rows)} rows from <table>.")

    # ── 2. Fallback: card / list items ────────────────────────────────────
    if not all_rows:
        print("[!] No <table> found — falling back to card/list scraper.")
        items = await page.query_selector_all(
            "[class*='row'], [class*='card'], [class*='item'], "
            "[class*='comparison'], [class*='campaign']"
        )
        for item in items:
            text = (await item.inner_text()).strip()
            if text:
                all_rows.append(text.splitlines())
        print(f"[+] Extracted {len(all_rows)} card/list items.")

    # ── 3. Final fallback: all visible text ───────────────────────────────
    if not all_rows:
        print("[!] No structured elements found — capturing all visible text.")
        body_text = await page.inner_text("body")
        for line in body_text.splitlines():
            line = line.strip()
            if line:
                all_rows.append([line])
        print(f"[+] Captured {len(all_rows)} text lines.")

    return all_rows


def save_to_csv(rows: list[list[str]], filename: str) -> None:
    """Write the scraped rows to a CSV file."""
    if not rows:
        print("[!] No data to save.")
        return

    max_cols = max(len(r) for r in rows)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row + [""] * (max_cols - len(row)))

    print(f"[+] Saved {len(rows)} rows → '{filename}'")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape ask-dom.com campaign comparison page.")
    p.add_argument("--account",  default=ACCOUNT,     help="DOM account name")
    p.add_argument("--username", default=USERNAME,     help="DOM username")
    p.add_argument("--password", default=PASSWORD,     help="DOM password")
    p.add_argument("--output",   default=OUTPUT_FILE,  help="Output CSV file path")
    p.add_argument("--visible",  action="store_true",  help="Run browser in visible (non-headless) mode")
    return p.parse_args()


async def main() -> None:
    args = parse_args()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.visible)
        context = await browser.new_context()
        page    = await context.new_page()

        try:
            await login(page, args.account, args.username, args.password)
            rows = await scrape_comparison(page)
            save_to_csv(rows, args.output)
        finally:
            await browser.close()


if __name__ == "__main__":
    import sys
    if "ipykernel" in sys.modules or "google.colab" in sys.modules:
        # Jupyter/Colab already has a running event loop — use nest_asyncio
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass
        asyncio.get_event_loop().run_until_complete(main())
    else:
        asyncio.run(main())
