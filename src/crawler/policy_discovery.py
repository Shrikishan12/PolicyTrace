from bs4 import BeautifulSoup
from urllib.parse import urljoin


def find_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = a["href"]

        full_url = urljoin(base_url, href)

        links.append({
            "text": text,
            "url": full_url
        })

    return links


def score_privacy_link(link):
    text = link["text"].lower().strip()
    url = link["url"].lower()

    score = 0

    if "privacy policy" in text:
        score += 10

    elif "privacy notice" in text:
        score += 9

    elif text == "privacy":
        score += 8

    elif "privacy" in text:
        score += 6

    if "privacy-policy" in url:
        score += 5

    elif "privacy_policy" in url:
        score += 5

    elif "privacy" in url:
        score += 3

    if "data protection" in text:
        score += 5

    if "cookie policy" in text:
        score += 2

    return score


def find_privacy_policy(links):
    candidates = []

    for link in links:
        score = score_privacy_link(link)

        if score > 0:
            candidates.append({
                "text": link["text"],
                "url": link["url"],
                "score": score
            })

    candidates.sort(
        key=lambda candidate: candidate["score"],
        reverse=True
    )

    return candidates