from src.crawler.http_crawler import fetch_page

from src.crawler.policy_discovery import (
    find_links,
    find_privacy_policy
)

from src.policy.extractor import (
    extract_policy_text
)

from src.policy.analysis_pipeline import (
    analyze_policy_claims
)


def analyze_website_policy(website_url):
    try:
        # --------------------------------
        # 1. Fetch homepage
        # --------------------------------
        homepage_html = fetch_page(
            website_url
        )

        # --------------------------------
        # 2. Discover links
        # --------------------------------
        links = find_links(
            homepage_html,
            website_url
        )

        # --------------------------------
        # 3. Find privacy policy
        # --------------------------------
        candidates = find_privacy_policy(
            links
        )

        if not candidates:
            print(
                "[ERROR] Privacy policy not found."
            )

            return {
                "website_url": website_url,
                "privacy_policy_url": None,
                "policy_text": "",
                "claims": []
            }

        # --------------------------------
        # 4. Select best privacy-policy URL
        # --------------------------------
        privacy_policy_url = (
            candidates[0]["url"]
        )

        # --------------------------------
        # 5. Fetch privacy policy
        # --------------------------------
        policy_html = fetch_page(
            privacy_policy_url
        )

        # --------------------------------
        # 6. Extract policy text
        # --------------------------------
        policy_text = extract_policy_text(
            policy_html
        )

        if not policy_text:
            print(
                "[ERROR] Privacy policy text is empty."
            )

            return {
                "website_url": website_url,
                "privacy_policy_url": privacy_policy_url,
                "policy_text": "",
                "claims": []
            }

        # --------------------------------
        # 7. Analyze policy claims
        # --------------------------------
        claims = analyze_policy_claims(
            policy_text
        )

        # --------------------------------
        # 8. Return complete result
        # --------------------------------
        return {
            "website_url": website_url,
            "privacy_policy_url": privacy_policy_url,
            "policy_text": policy_text,
            "claims": claims
        }

    except Exception as ex:
        print(
            f"[ERROR] Website policy analysis failed: "
            f"{ex}"
        )

        return {
            "website_url": website_url,
            "privacy_policy_url": None,
            "policy_text": "",
            "claims": []
        }