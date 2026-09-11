import json
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

from src.browser.network_monitor import create_request_record
from src.browser.consent import click_consent
from src.trackers.tracker_radar import lookup_domain


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

url = "https://www.youtube.com"
# ---------------------------------------------------------
# Experiment output directory
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

timestamp = datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S"
)

EXPERIMENT_DIR = (
    BASE_DIR
    / "data"
    / "experiments"
    / "claude.ai"
    / timestamp
)

try:

    EXPERIMENT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

except Exception as ex:

    print(
        f"[ERROR] Could not create experiment directory: {ex}"
    )
# ---------------------------------------------------------
# Get unique domains
# ---------------------------------------------------------

def get_unique_domains(requests):

    try:

        domains = set()

        for request in requests:

            domain = request.get("domain")

            if domain:
                domains.add(domain)

        return sorted(domains)

    except Exception as ex:

        print(
            f"[ERROR] Could not extract domains: {ex}"
        )

        return []


# ---------------------------------------------------------
# Analyze domains with Tracker Radar
# ---------------------------------------------------------

def analyze_domains(domains, state):

    results = []

    for domain in domains:

        try:

            tracker_result = lookup_domain(domain)

            evidence = {
                "domain": domain,
                "state": state,
                "tracker_radar": tracker_result is not None
            }

            if tracker_result:

                evidence.update({
                    "matched_domain": tracker_result.get(
                        "tracker_radar_domain"
                    ),
                    "owner": tracker_result.get(
                        "owner"
                    ),
                    "display_name": tracker_result.get(
                        "display_name"
                    ),
                    "categories": tracker_result.get(
                        "categories",
                        []
                    ),
                    "fingerprinting": tracker_result.get(
                        "fingerprinting"
                    ),
                    "prevalence": tracker_result.get(
                        "prevalence"
                    ),
                    "cookies": tracker_result.get(
                        "cookies"
                    ),
                    "types": tracker_result.get(
                        "types",
                        []
                    )
                })

            else:

                evidence.update({
                    "matched_domain": None,
                    "owner": None,
                    "display_name": None,
                    "categories": [],
                    "fingerprinting": None,
                    "prevalence": None,
                    "cookies": None,
                    "types": []
                })

            results.append(evidence)

        except Exception as ex:

            print(
                f"[ERROR] Domain analysis failed "
                f"for {domain}: {ex}"
            )

    return results


# ---------------------------------------------------------
# Save JSON
# ---------------------------------------------------------

def save_json(filename, data):

    try:

        file_path = EXPERIMENT_DIR / filename

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        print(
            f"[SAVED] {file_path}"
        )

    except Exception as ex:

        print(
            f"[ERROR] Could not save {filename}: {ex}"
        )


# ---------------------------------------------------------
# Run one experiment
# ---------------------------------------------------------

def run_experiment(browser, state, action=None):

    context = None

    try:

        context = browser.new_context()

        page = context.new_page()

        requests = []

        # ---------------------------------------------
        # Capture requests
        # ---------------------------------------------

        def handle_request(request):

            try:

                record = create_request_record(request)

                requests.append(record)

            except Exception as ex:

                print(
                    f"[ERROR] Could not record request: {ex}"
                )

        page.on(
            "request",
            handle_request
        )

        # ---------------------------------------------
        # Open website
        # ---------------------------------------------

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

        print(
            "Page title:",
            page.title()
        )

        # ---------------------------------------------
        # Capture pre-consent requests
        # ---------------------------------------------

        pre_consent_requests = list(
            requests
        )

        print(
            "Pre-consent requests:",
            len(pre_consent_requests)
        )

        # ---------------------------------------------
        # Consent action
        # ---------------------------------------------

        post_action_requests = []

        if action:

            print(
                f"Trying to {action} cookies..."
            )

            clicked = click_consent(
                page,
                action
            )

            if clicked:

                print(
                    f"{action.capitalize()} button "
                    f"clicked successfully"
                )

            else:

                print(
                    f"{action.capitalize()} button "
                    f"not found"
                )

            # -----------------------------------------
            # Mark exact point after action
            # -----------------------------------------

            request_count_before_action = len(
                requests
            )

            page.wait_for_timeout(5000)

            post_action_requests = requests[
                request_count_before_action:
            ]

            print(
                "Requests after action:",
                len(post_action_requests)
            )

        else:

            print(
                "No consent action performed."
            )

        # ---------------------------------------------
        # Domains
        # ---------------------------------------------

        pre_domains = get_unique_domains(
            pre_consent_requests
        )

        post_domains = get_unique_domains(
            post_action_requests
        )

        # ---------------------------------------------
        # Tracker Radar
        # ---------------------------------------------

        if state == "pre_consent":

            evidence_domains = pre_domains

        else:

            evidence_domains = post_domains

        tracker_evidence = analyze_domains(
            evidence_domains,
            state
        )

        # ---------------------------------------------
        # Build structured result
        # ---------------------------------------------

        result = {
            "website": url,
            "state": state,

            "pre_consent": {
                "request_count": len(
                    pre_consent_requests
                ),
                "domains": pre_domains
            },

            "post_action": {
                "request_count": len(
                    post_action_requests
                ),
                "domains": post_domains
            },

            "tracker_radar": tracker_evidence
        }

        return result

    except Exception as ex:

        print(
            f"[ERROR] Experiment failed "
            f"({state}): {ex}"
        )

        return {
            "website": url,
            "state": state,
            "pre_consent": {
                "request_count": 0,
                "domains": []
            },
            "post_action": {
                "request_count": 0,
                "domains": []
            },
            "tracker_radar": []
        }

    finally:

        try:

            if context:

                context.close()

        except Exception as ex:

            print(
                f"[ERROR] Could not close "
                f"browser context: {ex}"
            )


# ---------------------------------------------------------
# Compare consent states
# ---------------------------------------------------------

def create_comparison(
    pre_result,
    accept_result,
    reject_result
):

    try:

        pre_domains = set(
            pre_result["pre_consent"]["domains"]
        )

        accept_domains = set(
            accept_result["post_action"]["domains"]
        )

        reject_domains = set(
            reject_result["post_action"]["domains"]
        )

        return {

            "new_after_accept": sorted(
                accept_domains - pre_domains
            ),

            "new_after_reject": sorted(
                reject_domains - pre_domains
            ),

            "accept_only": sorted(
                accept_domains
                - pre_domains
                - reject_domains
            ),

            "reject_only": sorted(
                reject_domains
                - pre_domains
                - accept_domains
            ),

            "common_all_states": sorted(
                pre_domains
                & accept_domains
                & reject_domains
            )
        }

    except Exception as ex:

        print(
            f"[ERROR] Could not create comparison: {ex}"
        )

        return {}


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    print("\n" + "=" * 40)
    print("CONSENT EXPERIMENT")
    print("=" * 40)

    with sync_playwright() as p:

        browser = None

        try:

            browser = p.chromium.launch(
                headless=False
            )

            # -----------------------------------------
            # Pre-consent
            # -----------------------------------------

            print("\n")
            print("=" * 40)
            print("Experiment: pre_consent")
            print("=" * 40)

            pre_result = run_experiment(
                browser,
                "pre_consent"
            )

            # -----------------------------------------
            # Accept
            # -----------------------------------------

            print("\n")
            print("=" * 40)
            print("Experiment: accept")
            print("=" * 40)

            accept_result = run_experiment(
                browser,
                "accept",
                "accept"
            )

            # -----------------------------------------
            # Reject
            # -----------------------------------------

            print("\n")
            print("=" * 40)
            print("Experiment: reject")
            print("=" * 40)

            reject_result = run_experiment(
                browser,
                "reject",
                "reject"
            )

            # -----------------------------------------
            # Comparison
            # -----------------------------------------

            comparison = create_comparison(
                pre_result,
                accept_result,
                reject_result
            )

            # -----------------------------------------
            # Final experiment object
            # -----------------------------------------

            final_result = {

                "website": url,

                "experiments": {
                    "pre_consent": pre_result,
                    "accept": accept_result,
                    "reject": reject_result
                },

                "comparison": comparison
            }

            # -----------------------------------------
            # Save individual states
            # -----------------------------------------

            save_json(
                "pre_consent.json",
                pre_result
            )

            save_json(
                "accept.json",
                accept_result
            )

            save_json(
                "reject.json",
                reject_result
            )

            # -----------------------------------------
            # Save complete experiment
            # -----------------------------------------

            save_json(
                "consent_experiment.json",
                final_result
            )

            # -----------------------------------------
            # Print summary
            # -----------------------------------------

            print("\n")
            print("=" * 40)
            print("STRUCTURED EXPERIMENT COMPLETE")
            print("=" * 40)

            print(
                "Pre-consent domains:",
                len(
                    pre_result[
                        "pre_consent"
                    ]["domains"]
                )
            )

            print(
                "Accept post-action domains:",
                len(
                    accept_result[
                        "post_action"
                    ]["domains"]
                )
            )

            print(
                "Reject post-action domains:",
                len(
                    reject_result[
                        "post_action"
                    ]["domains"]
                )
            )

            print(
                "\nExperiment files saved to:"
            )

            print(
                EXPERIMENT_DIR
            )

        except Exception as ex:

            print(
                f"[ERROR] Main experiment failed: {ex}"
            )

        finally:

            try:

                if browser:

                    browser.close()

            except Exception as ex:

                print(
                    f"[ERROR] Could not close browser: {ex}"
                )