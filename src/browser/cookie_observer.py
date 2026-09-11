# ---------------------------------------------------------
# Cookie Observer
# ---------------------------------------------------------

def get_cookies(context):

    try:

        cookies = context.cookies()

        return cookies

    except Exception as ex:

        print(
            f"[ERROR] Could not read browser cookies: {ex}"
        )

        return []


# ---------------------------------------------------------
# Simplify cookie information
# ---------------------------------------------------------

def simplify_cookies(cookies):

    simplified = []

    try:

        for cookie in cookies:

            simplified.append({
                "name": cookie.get("name"),
                "domain": cookie.get("domain"),
                "path": cookie.get("path"),
                "expires": cookie.get("expires"),
                "httpOnly": cookie.get("httpOnly"),
                "secure": cookie.get("secure"),
                "sameSite": cookie.get("sameSite")
            })

    except Exception as ex:

        print(
            f"[ERROR] Could not simplify cookies: {ex}"
        )

    return simplified


# ---------------------------------------------------------
# Get cookie names
# ---------------------------------------------------------

def get_cookie_names(cookies):

    try:

        return sorted(
            set(
                cookie.get("name")
                for cookie in cookies
                if cookie.get("name")
            )
        )

    except Exception as ex:

        print(
            f"[ERROR] Could not extract cookie names: {ex}"
        )

        return []


# ---------------------------------------------------------
# Compare two cookie states
# ---------------------------------------------------------

def find_new_cookies(
    before_cookies,
    after_cookies
):

    try:

        before = {
            (
                cookie.get("name"),
                cookie.get("domain"),
                cookie.get("path")
            )
            for cookie in before_cookies
        }

        new_cookies = []

        for cookie in after_cookies:

            key = (
                cookie.get("name"),
                cookie.get("domain"),
                cookie.get("path")
            )

            if key not in before:

                new_cookies.append(cookie)

        return new_cookies

    except Exception as ex:

        print(
            f"[ERROR] Could not compare cookies: {ex}"
        )

        return []

# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    from playwright.sync_api import sync_playwright

    url = "https://claude.ai"

    with sync_playwright() as p:

        browser = None
        context = None

        try:

            browser = p.chromium.launch(
                headless=False
            )

            context = browser.new_context()

            page = context.new_page()

            try:

                page.goto(
                    url,
                    wait_until="commit",
                    timeout=20000
                )

            except Exception as ex:

                print(
                    f"[ERROR] Page navigation failed: {ex}"
                )

            page.wait_for_timeout(5000)

            cookies = get_cookies(context)

            simplified = simplify_cookies(
                cookies
            )

            print("\n========================================")
            print("COOKIE OBSERVER TEST")
            print("========================================")

            print(
                "Total cookies:",
                len(simplified)
            )

            print(
                "\nCookie names:"
            )

            for name in get_cookie_names(
                simplified
            ):

                print(
                    f"  {name}"
                )

            print(
                "\nCookie details:"
            )

            for cookie in simplified:

                print(
                    f"  {cookie}"
                )

        except Exception as ex:

            print(
                f"[ERROR] Cookie observer test failed: {ex}"
            )

        finally:

            try:

                if context:
                    context.close()

            except Exception as ex:

                print(
                    f"[ERROR] Could not close context: {ex}"
                )

            try:

                if browser:
                    browser.close()

            except Exception as ex:

                print(
                    f"[ERROR] Could not close browser: {ex}"
                )