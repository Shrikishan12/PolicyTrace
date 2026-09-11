from playwright.sync_api import sync_playwright
from src.browser.network_monitor import create_request_record


def open_page(url):
    requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        def handle_request(request):
            record = create_request_record(request)
            requests.append(record)

        page.on("request", handle_request)

        page.goto(url, timeout=20000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)  # settle time regardless
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
             pass  # fine if it never goes idle — proceed anyway
        page.wait_for_timeout(3000)  # settle time regardless
        print(f"[debug] final URL after navigation: {page.url}")
        print(f"[debug] page title: {page.title()!r}")

        print("\nBrowser opened successfully")
        print("Page title:", page.title())

        browser.close()

    return requests