import re


ACTOR_PATTERNS = [
    r"\bwe\b",
    r"\bour\b",
    r"\bthe company\b",
    r"\bthe website\b",
    r"\bwe and our partners\b",
]


ACTION_PATTERNS = {
    "share": [
        r"\bshare(?:s|d|ing)?\b",
    ],
    "collect": [
        r"\bcollect(?:s|ed|ing)?\b",
        r"\bgather(?:s|ed|ing)?\b",
        r"\bobtain(?:s|ed|ing)?\b",
        r"\breceive(?:s|d|ing)?\b",
    ],
    "use": [
        r"\buse(?:s|d|ing)?\b",
        r"\bprocess(?:es|ed|ing)?\b",
    ],
    "sell": [
        r"\bsell(?:s|ing)?\b",
        r"\bsold\b",
    ],
    "store": [
        r"\bstore(?:s|d|ing)?\b",
        r"\bretain(?:s|ed|ing)?\b",
        r"\bkeep(?:s|t|ing)?\b",
    ],
}


DATA_PATTERNS = [
    r"personal information",
    r"personal data",
    r"analytics information",
    r"usage information",
    r"location information",
    r"device information",
    r"contact information",
    r"technical information",
    r"your information",
    r"your data",
    r"information",
    r"data",
]


ENTITY_PATTERNS = [
    r"third-party service providers",
    r"third party service providers",
    r"business partners",
    r"marketing partners",
    r"analytics providers",
    r"data brokers",
    r"third parties",
    r"third party",
    r"service providers",
    r"advertisers",
    r"partners",
    r"vendors",
    r"affiliates",
    r"subsidiaries",
]


NEGATION_PATTERNS = [
    r"\bdo not\b",
    r"\bdoes not\b",
    r"\bdon't\b",
    r"\bdoesn't\b",
    r"\bwill never\b",
    r"\bwill not\b",
    r"\bwon't\b",
    r"\bnever\b",
    r"\bno longer\b",
]


def find_first_match(patterns, sentence):
    try:
        for pattern in patterns:
            match = re.search(
                pattern,
                sentence,
                re.IGNORECASE
            )

            if match:
                return match.group(0), match.start()

        return None, None

    except Exception as ex:
        print(f"[ERROR] Pattern matching failed: {ex}")
        return None, None


def find_actions(sentence):
    actions = []

    try:
        for action, patterns in ACTION_PATTERNS.items():

            for pattern in patterns:
                matches = re.finditer(
                    pattern,
                    sentence,
                    re.IGNORECASE
                )

                for match in matches:
                    actions.append({
                        "action": action,
                        "text": match.group(0),
                        "position": match.start()
                    })

        actions.sort(
            key=lambda item: item["position"]
        )

        return actions

    except Exception as ex:
        print(f"[ERROR] Action extraction failed: {ex}")
        return []


def detect_polarity(sentence, action_pos):
    try:
        prefix = sentence[:action_pos]

        for negation in NEGATION_PATTERNS:

            if re.search(
                negation,
                prefix,
                re.IGNORECASE
            ):
                return "denies"

        return "affirms"

    except Exception as ex:
        print(f"[ERROR] Polarity detection failed: {ex}")
        return "affirms"


def extract_claim(sentence, action_info, failures=None):
    try:
        actor, _ = find_first_match(
            ACTOR_PATTERNS,
            sentence
        )

        data_object, _ = find_first_match(
            DATA_PATTERNS,
            sentence
        )

        entity, _ = find_first_match(
            ENTITY_PATTERNS,
            sentence
        )

        action = action_info["action"]
        action_pos = action_info["position"]

        polarity = detect_polarity(
            sentence,
            action_pos
        )

        return {
            "sentence": sentence.strip(),
            "actor": actor,
            "action": action,
            "polarity": polarity,
            "data_object": data_object,
            "entity": entity
        }

    except Exception as ex:
        if failures is not None:
            failures.append({
                "sentence": sentence,
                "error": str(ex)
            })
        else:
            print(
                f"[ERROR] Claim extraction failed: {ex}"
            )

        return None


def extract_claims(text):
    claims = []
    failures = []

    try:
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text
        )

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            actions = find_actions(sentence)

            for action_info in actions:

                claim = extract_claim(
                    sentence,
                    action_info,
                    failures
                )

                if claim:
                    claims.append(claim)

    except Exception as ex:
        failures.append({
            "sentence": None,
            "error": str(ex)
        })

    return claims, failures


if __name__ == "__main__":

    test_text = """
    We may share your personal information with third parties.
    We collect device information to improve our services.
    We do not sell your personal data to advertisers.
    We will never share your data with third parties without your consent.
    We do not collect, store, or share personal data.
    """

    claims, failures = extract_claims(
        test_text
    )

    print("\nPOLICY CLAIMS\n")

    for claim in claims:
        print(claim)

    if failures:
        print(
            f"\n{len(failures)} extraction failure(s):"
        )

        for failure in failures:
            print(f"  {failure}")