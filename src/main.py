from crawler.http_crawler import fetch_page
from crawler.policy_discovery import find_links, find_privacy_policy
from policy.rules import analyze_policy
from policy.extractor import extract_policy_text
from browser.browser import open_page

url = "https://chatgpt.com"

open_page(url)
print("Website fetched successfully")
html = fetch_page(url)

links = find_links(html,url)

print("\nLinks found:", len(links))

for link in links:
    print(link["text"], "->", link["url"])

privacy_links = find_privacy_policy(links)

print("\nPrivacy policy candidates:")

for link in privacy_links:
    print(
        f"{link['text']} -> {link['url']} "
        f"(score: {link['score']})"
    )

if privacy_links:
    policy_url = privacy_links[0]["url"]

    print("\nSelected privacy policy:")
    print(policy_url)

    policy_html = fetch_page(policy_url)

    print("\nPrivacy policy fetched")
    print("Policy HTML length:", len(policy_html))

    policy_text = extract_policy_text(policy_html)

    print("Extracted policy text length:", len(policy_text))

    print("\n========== POLICY TEXT SAMPLE ==========\n")
    print(policy_text[:2000])
    print("\n=========================================")

    results = analyze_policy(policy_text)

    print("\nPolicy Analysis")
    print("=" * 40)

    for category, result in results.items():
        print(
            f"\n{category}: "
            f"{'FOUND' if result['found'] else 'NOT FOUND'}"
        )

        for evidence in result["evidence"]:
            print("  Evidence:", evidence[:300])

else:
    print("\nNo privacy policy found.")