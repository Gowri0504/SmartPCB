"""Capture Review-3 screenshots of the live SmartPCB-XAI stack.

Drives the installed Chrome (channel='chrome', no browser download) against
the Vite dev server (3000). Saves PNGs to docs/screenshots/review3/.
Run with services up: uvicorn:8000, express:5000, vite:3000.
"""
import os
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs", "screenshots", "review3")
os.makedirs(OUT, exist_ok=True)

BASE = "http://localhost:3000"


def wait_engine_online(page, timeout_s=60):
    for _ in range(timeout_s):
        label = page.locator("text=AI ENGINE ONLINE").count()
        if label:
            return True
        time.sleep(1)
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.goto(BASE, wait_until="networkidle")

        if not wait_engine_online(page):
            print("WARN: engine indicator never turned ONLINE")
        page.screenshot(path=os.path.join(OUT, "01_inspection_studio.png"), full_page=True)

        def run_and_settle():
            page.click("text=Run Inspection")
            page.wait_for_selector("text=Analyzing Optical Patterns...", timeout=30000)
            page.wait_for_selector("text=Analyzing Optical Patterns...", state="hidden", timeout=300000)
            page.wait_for_timeout(4000)

        # Run inspection on demo defect board 1
        page.select_option("select", value="/samples/sample_defect_board1.jpg")
        run_and_settle()
        page.screenshot(path=os.path.join(OUT, "02_inspection_result.png"), full_page=True)

        # Run second demo board (SMT components) for a second result shot
        page.select_option("select", value="/samples/sample_smt_board2.jpg")
        run_and_settle()
        page.screenshot(path=os.path.join(OUT, "03_inspection_smt.png"), full_page=True)

        # Digital Twin tab
        page.click("text=Digital Twin")
        page.wait_for_timeout(2500)
        page.screenshot(path=os.path.join(OUT, "04_digital_twin.png"), full_page=True)

        # Analytics tab
        page.click("text=Analytics")
        page.wait_for_timeout(2500)
        page.screenshot(path=os.path.join(OUT, "05_analytics.png"), full_page=True)

        # Research & Benchmarks tab
        page.click("text=Research & Benchmarks")
        page.wait_for_timeout(2500)
        page.screenshot(path=os.path.join(OUT, "06_benchmarks.png"), full_page=True)

        browser.close()
        print("Captured:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
