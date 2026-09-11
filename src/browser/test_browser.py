from src.browser.browser import open_page
from src.browser.domain_classifier import classify_requests
from src.trackers.tracker_radar import lookup_domain


url = "https://claude.ai/"

requests = open_page(url)

first_party, third_party = classify_requests(requests, url)

print("\nNetwork summary")
print("=" * 40)

print("Total requests:", len(requests))
print("First-party requests:", len(first_party))
print("Third-party requests:", len(third_party))

print("\nThird-party domains:")

domains = sorted(set(request["domain"] for request in third_party))

for domain in domains:
    print(domain)
print("\nTracker Radar Analysis")
print("=" * 40)

checked_domains = set()

for request in third_party:

    domain = request["domain"]
    if not domain:
        continue

    if domain in checked_domains:
        continue

    checked_domains.add(domain)

    result = lookup_domain(domain)

    print(f"\nDomain: {domain}")

    if result:
        print("  Tracker Radar: MATCHED")
        print("  Matched domain:", result["tracker_radar_domain"])
        print("  Owner:", result["owner"])
        print("  Display name:", result["display_name"])
        print("  Categories:", result["categories"])
        print("  Fingerprinting:", result["fingerprinting"])
        print("  Prevalence:", result["prevalence"])

    else:
        print("  Tracker Radar: NOT FOUND")