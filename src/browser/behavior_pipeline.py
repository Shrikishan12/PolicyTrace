from urllib.parse import urlparse

from src.trackers.tracker_radar import (
    lookup_domain
)

from src.browser.cookie_observer import (
    get_cookies,
    find_new_cookies
)

from src.browser.consent import (
    click_consent
)

def get_website_domain(website_url):
    try:
        parsed_url = urlparse(
            website_url
        )

        return parsed_url.netloc.lower()

    except Exception as ex:
        print(
            f"[ERROR] Could not extract website domain: {ex}"
        )
        return None


def is_first_party(
    request_domain,
    website_domain
):
    try:
        if not request_domain:
            return False

        if not website_domain:
            return False

        return (
            request_domain == website_domain
            or request_domain.endswith(
                "." + website_domain
            )
        )

    except Exception as ex:
        print(
            f"[ERROR] First-party classification failed: {ex}"
        )
        return False


def classify_requests(
    requests,
    website_url
):
    try:
        website_domain = (
            get_website_domain(
                website_url
            )
        )

        if not website_domain:
            return [], []

        first_party = []
        third_party = []

        for request in requests:

            request_domain = (
                request.get("domain")
            )

            if is_first_party(
                request_domain,
                website_domain
            ):
                first_party.append(
                    request
                )

            else:
                third_party.append(
                    request
                )

        return (
            first_party,
            third_party
        )

    except Exception as ex:
        print(
            f"[ERROR] Request classification failed: {ex}"
        )
        return [], []


def enrich_third_party_requests(
    third_party_requests
):
    enriched = []

    try:
        for request in third_party_requests:

            domain = request.get(
                "domain"
            )

            tracker_info = (
                lookup_domain(
                    domain
                )
            )

            enriched.append({
                **request,
                "tracker_radar": tracker_info
            })

        return enriched

    except Exception as ex:
        print(
            f"[ERROR] Tracker enrichment failed: {ex}"
        )
        return enriched


def analyze_browser_requests(
    requests,
    website_url
):
    try:
        (
            first_party,
            third_party
        ) = classify_requests(
            requests,
            website_url
        )

        enriched_third_party = (
            enrich_third_party_requests(
                third_party
            )
        )

        return {
            "website_url": website_url,
            "first_party_requests": first_party,
            "third_party_requests": enriched_third_party
        }

    except Exception as ex:
        print(
            f"[ERROR] Browser request analysis failed: {ex}"
        )

        return {
            "website_url": website_url,
            "first_party_requests": [],
            "third_party_requests": []
        }


def run_behavior_test(
    website_url,
    action=None
):
    try:
        from playwright.sync_api import sync_playwright
        from src.browser.network_monitor import (
            create_request_record
        )

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            context = browser.new_context()

            page = context.new_page()

            requests = []

            def handle_request(request):
                try:
                    record = create_request_record(
                        request
                    )

                    requests.append(record)

                except Exception as ex:
                    print(
                        f"[ERROR] Request capture failed: {ex}"
                    )

            page.on(
                "request",
                handle_request
            )

            cookies_before = get_cookies(
                context
            )

            page.goto(
                website_url,
                wait_until="commit",
                timeout=60000
            )

            page.wait_for_timeout(
                5000
            )

            cookies_after_load = get_cookies(
                context
            )

            new_cookies_after_load = (
                find_new_cookies(
                    cookies_before,
                    cookies_after_load
                )
            )

            consent_clicked = False

            if action in {
                "accept",
                "reject"
            }:

                consent_clicked = click_consent(
                    page,
                    action
                )

                if consent_clicked:
                    page.wait_for_timeout(
                        5000
                    )

            cookies_after_action = get_cookies(
                context
            )

            new_cookies_after_action = (
                find_new_cookies(
                    cookies_after_load,
                    cookies_after_action
                )
            )

            browser_requests = (
                analyze_browser_requests(
                    requests,
                    website_url
                )
            )

            browser.close()

            return {
                "website_url": website_url,
                "action": action,
                "consent_clicked": consent_clicked,

                "cookies": {
                    "before": cookies_before,
                    "after_page_load": cookies_after_load,
                    "new_after_page_load": (
                        new_cookies_after_load
                    ),
                    "after_action": cookies_after_action,
                    "new_after_action": (
                        new_cookies_after_action
                    )
                },

                "network": {
                    "first_party_requests": (
                        browser_requests[
                            "first_party_requests"
                        ]
                    ),
                    "third_party_requests": (
                        browser_requests[
                            "third_party_requests"
                        ]
                    )
                }
            }

    except Exception as ex:

        print(
            f"[ERROR] Browser behavior test failed: {ex}"
        )

        return {
            "website_url": website_url,
            "action": action,
            "consent_clicked": False,

            "cookies": {
                "before": [],
                "after_page_load": [],
                "new_after_page_load": [],
                "after_action": [],
                "new_after_action": []
            },

            "network": {
                "first_party_requests": [],
                "third_party_requests": []
            }
        }

def run_all_behavior_tests(
    website_url
):
    results = {}

    try:
        print("\n==============================")
        print("BASELINE TEST")
        print("==============================")

        results["baseline"] = run_behavior_test(
            website_url
        )

        print("\n==============================")
        print("ACCEPT TEST")
        print("==============================")

        results["accept"] = run_behavior_test(
            website_url,
            action="accept"
        )

        print("\n==============================")
        print("REJECT TEST")
        print("==============================")

        results["reject"] = run_behavior_test(
            website_url,
            action="reject"
        )

        return results

    except Exception as ex:
        print(
            f"[ERROR] All behavior tests failed: {ex}"
        )

        return results
if __name__ == "__main__":

    from src.browser.browser import open_page

    website_url = "https://vtpoddar.com"

    requests = open_page(
        website_url
    )

    result = analyze_browser_requests(
        requests,
        website_url
    )

    print("\nWEBSITE:")
    print(result["website_url"])

    print("\nFIRST-PARTY REQUESTS:")
    print(len(result["first_party_requests"]))

    print("\nTHIRD-PARTY REQUESTS:")
    print(len(result["third_party_requests"]))

    print("\nTRACKER RADAR RESULTS:\n")

    domains_seen = set()

    for request in result["third_party_requests"]:

        domain = request.get("domain")

        if not domain:
            continue

        if domain in domains_seen:
            continue

        domains_seen.add(domain)

        tracker_info = request.get(
            "tracker_radar"
        )

        print("DOMAIN:", domain)

        if tracker_info:
            print("OWNER:", tracker_info.get("owner"))
            print("DISPLAY NAME:", tracker_info.get("display_name"))
            print("CATEGORIES:", tracker_info.get("categories"))
            print("FINGERPRINTING:", tracker_info.get("fingerprinting"))
            print("PREVALENCE:", tracker_info.get("prevalence"))
        else:
            print("TRACKER RADAR: NOT FOUND")

        print()