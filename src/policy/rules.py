import re


RULES = {
    "cookies": [
        "cookie",
        "cookies"
    ],
    "analytics": [
        "analytics",
        "google analytics"
    ],
    "tracking": [
        "tracking",
        "track your activity",
        "track your browsing"
    ],
    "third_party": [
        "third party",
        "third-party",
        "third parties",
        "third-party services"
    ],
    "personal_information": [
        "personal information",
        "personal data"
    ]
}


def find_evidence(text, keywords):
    sentences = re.split(r'(?<=[.!?])\s+', text)

    evidence = []

    for sentence in sentences:
        sentence_lower = sentence.lower()

        for keyword in keywords:
            if keyword in sentence_lower:
                evidence.append(sentence.strip())
                break

    return evidence


def analyze_policy(text):
    results = {}

    for category, keywords in RULES.items():
        evidence = find_evidence(text, keywords)

        results[category] = {
            "found": len(evidence) > 0,
            "evidence": evidence[:3]
        }

    return results