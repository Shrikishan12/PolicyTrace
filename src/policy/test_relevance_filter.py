from src.policy.relevance_filter import (
    filter_relevant_sentences
)


sentences = [
    "This policy was updated in January 2026.",
    "We may collect your personal information.",
    "We use cookies to improve our website.",
    "The company was founded in 2010.",
    "We do not share personal data with third parties.",
    "This policy covers information collected through our website.",
]


try:
    relevant = filter_relevant_sentences(sentences)

    print("\nRELEVANT SENTENCES\n")

    for sentence in relevant:
        print("-", sentence)

except Exception as ex:
    print(
        f"[ERROR] Relevance filter test failed: {ex}"
    )