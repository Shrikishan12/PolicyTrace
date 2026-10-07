from urllib.parse import urlparse

from src.browser import consent
from src.browser.tracker_classification import (
    TRACKING_CATEGORIES,
    has_fingerprinting_signal,
)


def normalize_domain(domain):
    try:
        if not domain:
            return None

        domain = domain.lower().strip()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception as ex:
        print(f"[ERROR] Domain normalization failed: {ex}")
        return None


def get_website_domain(website_url):
    try:
        parsed_url = urlparse(website_url)

        return normalize_domain(
            parsed_url.netloc
        )

    except Exception as ex:
        print(f"[ERROR] Could not extract website domain: {ex}")
        return None


def is_first_party(request_domain, website_domain):
    try:
        request_domain = normalize_domain(
            request_domain
        )

        website_domain = normalize_domain(
            website_domain
        )

        if not request_domain or not website_domain:
            return False

        return (
            request_domain == website_domain
            or request_domain.endswith(
                "." + website_domain
            )
        )

    except Exception as ex:
        print(f"[ERROR] First-party classification failed: {ex}")
        return False


def classify_browser_evidence(
    request,
    website_domain
):
    try:
        request_domain = request.get(
            "domain"
        )

        first_party = is_first_party(
            request_domain,
            website_domain
        )

        tracker_info = request.get(
            "tracker_radar"
        )

        evidence = {
            "domain": request_domain,
            "url": request.get("url"),
            "resource_type": request.get(
                "resource_type"
            ),
            "first_party": first_party,
            "third_party": not first_party,
            "tracker_identified": False,
            "tracking_related": False,
            "tracker_owner": None,
            "tracker_categories": [],
            "fingerprinting": False
        }

        if tracker_info:

            evidence["tracker_identified"] = True

            evidence["tracker_owner"] = (
                tracker_info.get("owner")
                or tracker_info.get("display_name")
            )

            evidence["tracker_categories"] = (
                tracker_info.get("categories")
                or []
            )

            evidence["fingerprinting"] = has_fingerprinting_signal(
                tracker_info.get("fingerprinting")
            )

            normalized_categories = {
                str(category).strip().lower()
                for category in evidence["tracker_categories"]
            }

            if (
                normalized_categories.intersection(TRACKING_CATEGORIES)
                or evidence["fingerprinting"]
            ):
                evidence["tracking_related"] = True

        return evidence

    except Exception as ex:
        print(
            f"[ERROR] Browser evidence classification failed: {ex}"
        )
        return None


def collect_evidence(
    claim,
    browser_behavior
):
    try:
        website_domain = get_website_domain(
            browser_behavior.get(
                "website_url"
            )
        )

        if not website_domain:
            return []

        network = browser_behavior.get(
            "network",
            {}
        )

        requests = network.get(
            "third_party_requests",
            []
        )

        evidence = []

        for request in requests:

            classified = classify_browser_evidence(
                request,
                website_domain
            )

            if classified:
                evidence.append(
                    classified
                )

        return evidence

    except Exception as ex:
        print(
            f"[ERROR] Evidence collection failed: {ex}"
        )
        return []


def analyze_claim(
    claim,
    browser_behavior
):
    try:
        action = claim.get(
            "action"
        )

        polarity = claim.get(
            "polarity"
        )

        condition = claim.get(
            "condition"
        )

        evidence = collect_evidence(
            claim,
            browser_behavior
        )

        tracking_evidence = [
            item
            for item in evidence
            if item.get("tracking_related")
        ]

        # ----------------------------------------
        # COLLECT
        # ----------------------------------------

        if action == "collect":

            return {
                "claim": claim,
                "status": "insufficient_evidence",
                "reason": (
                    "Browser activity was observed, "
                    "but current evidence does not directly "
                    "prove collection of the policy data."
                ),
                "evidence": tracking_evidence
            }

        # ----------------------------------------
        # RETAIN
        # ----------------------------------------

        if action == "retain":

            cookies = browser_behavior.get(
                "cookies",
                {}
            )

            new_cookies = cookies.get(
                "new_after_page_load",
                []
            )

            if new_cookies:

                return {
                    "claim": claim,
                    "status": "observed_activity",
                    "reason": (
                        "Cookies were created during page load. "
                        "This is related browser activity, but "
                        "does not prove retention of the "
                        "personal data described by the claim."
                    ),
                    "evidence": []
                }

            return {
                "claim": claim,
                "status": "insufficient_evidence",
                "reason": (
                    "No browser evidence currently proves "
                    "retention of the policy data."
                ),
                "evidence": []
            }

        # ----------------------------------------
        # SHARE
        # ----------------------------------------

        if action == "share":

            if tracking_evidence:

                if polarity == "denies":

                    return {
                        "claim": claim,
                        "status": "observed_activity",
                        "reason": (
                            "Third-party tracking-related "
                            "communication was observed, but "
                            "the available evidence does not "
                            "prove that the policy data was shared."
                        ),
                        "evidence": tracking_evidence
                    }

                if condition:
                    consent = browser_behavior.get("consent", {})
                    consent_clicked = consent.get("clicked", False)
                    

                    if not consent_clicked:

                        return {
                            "claim": claim,
                            "status": "observed_activity",
                            "reason": (
                                "Third-party tracking-related "
                                "communication was observed "
                                "without a recognized consent "
                                "action. This does not prove "
                                "personal-data sharing."
                            ),
                            "evidence": tracking_evidence
                        }

                return {
                    "claim": claim,
                    "status": "observed_activity",
                    "reason": (
                        "Third-party tracking-related "
                        "communication was observed, but "
                        "the available evidence does not "
                        "prove that personal data was shared."
                    ),
                    "evidence": tracking_evidence
                }

            return {
                "claim": claim,
                "status": "insufficient_evidence",
                "reason": (
                    "No relevant browser evidence was observed "
                    "for the sharing claim."
                ),
                "evidence": []
            }

        # ----------------------------------------
        # USE
        # ----------------------------------------

        if action == "use":

            if tracking_evidence:

                return {
                    "claim": claim,
                    "status": "observed_activity",
                    "reason": (
                        "Tracking-related browser activity "
                        "was observed, but it does not prove "
                        "the specific use described by the "
                        "policy claim."
                    ),
                    "evidence": tracking_evidence
                }

            return {
                "claim": claim,
                "status": "insufficient_evidence",
                "reason": (
                    "No browser evidence currently proves "
                    "the specific use described by the claim."
                ),
                "evidence": []
            }

        # ----------------------------------------
        # SELL
        # ----------------------------------------

        if action == "sell":

            return {
                "claim": claim,
                "status": "insufficient_evidence",
                "reason": (
                    "Current browser evidence cannot establish "
                    "that personal data was sold."
                ),
                "evidence": []
            }

        return {
            "claim": claim,
            "status": "insufficient_evidence",
            "reason": (
                "Current evidence is insufficient to align "
                "this policy action."
            ),
            "evidence": evidence
        }

    except Exception as ex:
        print(
            f"[ERROR] Claim analysis failed: {ex}"
        )

        return {
            "claim": claim,
            "status": "analysis_error",
            "reason": str(ex),
            "evidence": []
        }


def align_claims(
    policy_claims,
    browser_behavior
):
    try:
        findings = []

        for claim in policy_claims:

            finding = analyze_claim(
                claim,
                browser_behavior
            )

            findings.append(
                finding
            )

        return findings

    except Exception as ex:
        print(
            f"[ERROR] Alignment failed: {ex}"
        )
        return []


def summarize_findings(findings):
    try:
        summary = {
            "supported": 0,
            "potential_mismatch": 0,
            "observed_activity": 0,
            "insufficient_evidence": 0,
            "analysis_error": 0
        }

        for finding in findings:

            status = finding.get(
                "status"
            )

            if status in summary:
                summary[status] += 1

        return summary

    except Exception as ex:
        print(
            f"[ERROR] Finding summary failed: {ex}"
        )
        return {}


def print_alignment_results(findings):
    try:
        print("\n")
        print("=" * 60)
        print("ALIGNMENT FINDINGS")
        print("=" * 60)

        for index, finding in enumerate(
            findings,
            start=1
        ):

            claim = finding.get(
                "claim",
                {}
            )

            print("\n" + "-" * 60)
            print(f"CLAIM {index}")
            print("-" * 60)

            print(
                "Action       :",
                claim.get("action")
            )

            print(
                "Polarity     :",
                claim.get("polarity")
            )

            print(
                "Data object  :",
                claim.get("data_object")
            )

            print(
                "Condition    :",
                claim.get("condition")
            )

            print(
                "Entity       :",
                claim.get("entity")
            )

            print(
                "\nStatus       :",
                finding.get("status", "").upper()
            )

            print(
                "Reason       :",
                finding.get("reason")
            )

            evidence = finding.get(
                "evidence",
                []
            )

            if evidence:

                print("\nEvidence:")

                shown = set()

                for item in evidence:

                    domain = item.get(
                        "domain"
                    )

                    if domain in shown:
                        continue

                    shown.add(domain)

                    print(
                        f"  - {domain}"
                    )

                    owner = item.get(
                        "tracker_owner"
                    )

                    categories = item.get(
                        "tracker_categories",
                        []
                    )

                    if owner:
                        print(
                            f"    Owner      : {owner}"
                        )

                    if categories:
                        print(
                            "    Categories : "
                            + ", ".join(categories)
                        )

            else:
                print(
                    "\nEvidence      : None"
                )

        print("\n")
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)

        summary = summarize_findings(
            findings
        )

        for status, count in summary.items():

            print(
                f"{status.replace('_', ' ').title():25}: {count}"
            )

    except Exception as ex:
        print(
            f"[ERROR] Could not print alignment results: {ex}"
        )

if __name__ == "__main__":

    from src.policy.pipeline import analyze_website_policy
    from src.browser.behavior_pipeline import run_all_behavior_tests

    website_url = "https://vtpoddar.ai"

    print("\n")
    print("=" * 60)
    print("POLICY ANALYSIS")
    print("=" * 60)

    policy_result = analyze_website_policy(
        website_url
    )

    policy_claims = policy_result.get(
        "claims",
        []
    )

    print(
        "\nPrivacy Policy:",
        policy_result.get("privacy_policy_url")
    )

    print(
        "\nNormalized Policy Claims:",
        len(policy_claims)
    )

    # Print claims ONLY
    for index, claim in enumerate(
        policy_claims,
        start=1
    ):
        print(
            f"\nClaim {index}:"
        )

        print(
            f"  Policy statement: {claim.get('sentence')}"
        )

        print(
            f"  Action          : {claim.get('action')}"
        )

        print(
            f"  Polarity        : {claim.get('polarity')}"
        )

        print(
            f"  Data object     : {claim.get('data_object')}"
        )

        print(
            f"  Condition       : {claim.get('condition')}"
        )

        print(
            f"  Entity          : {claim.get('entity')}"
        )

    # ------------------------------------------
    # BROWSER BEHAVIOR
    # ------------------------------------------

    print("\n")
    print("=" * 60)
    print("BROWSER BEHAVIOR")
    print("=" * 60)

    behavior_results = run_all_behavior_tests(
        website_url
    )

    for state in ("pre_consent", "accept", "reject"):

        browser_behavior = behavior_results.get(
            state,
            {}
        )

        print("\n")
        print("=" * 60)
        print(f"BROWSER BEHAVIOR: {state.upper()}")
        print("=" * 60)

        print(
            "First-party requests:",
            len(
                browser_behavior["network"]["first_party_requests"]
            )
        )

        print(
            "Third-party requests:",
            len(
                browser_behavior["network"]["third_party_requests"]
            )
        )

        print(
            "Cookies after page load:",
            len(
                browser_behavior["cookies"]["after_page_load"]
            )
        )

        consent = browser_behavior.get(
            "consent",
            {}
        )

        print(
            "Consent status:",
            consent.get("status")
        )

        print(
            "Consent clicked:",
            consent.get("clicked")
        )

        if consent.get("matched_label"):
            print(
                "Matched button:",
                consent.get("matched_label")
            )

        # ------------------------------------------
        # ALIGNMENT
        # ------------------------------------------

        print("\n")
        print("=" * 60)
        print(f"ALIGNMENT: {state.upper()}")
        print("=" * 60)

        findings = align_claims(
            policy_claims,
            browser_behavior
        )

        print_alignment_results(
            findings
        )

    # ------------------------------------------
    # CONSENT-STATE COMPARISON
    # ------------------------------------------

    comparison = behavior_results.get(
        "comparison",
        {}
    )

    print("\n" + "=" * 60)
    print("CONSENT-STATE COMPARISON")
    print("=" * 60)

    print(
        "Likely tracking domains before consent:",
        ", ".join(
            comparison.get(
                "pre_consent_likely_tracking_domains",
                []
            )
        ) or "None observed",
    )

    for action, result in comparison.get(
        "actions",
        {}
    ).items():

        print(
            f"\n{action.upper()}: {result.get('message')}"
        )

        domains = result.get(
            "new_likely_tracking_domains",
            []
        )

        print(
            "New likely tracking domains after action:",
            ", ".join(domains) or "None observed",
        )