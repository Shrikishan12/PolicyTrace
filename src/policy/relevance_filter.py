import re


PRIVACY_TERMS = [
    r"\bcollect\b",
    r"\bcollects\b",
    r"\bcollecting\b",
    r"\bcollection\b",

    r"\bgather\b",
    r"\bgathers\b",
    r"\bgathering\b",

    r"\bobtain\b",
    r"\bobtains\b",
    r"\bobtaining\b",

    r"\breceive\b",
    r"\breceives\b",
    r"\breceiving\b",

    r"\bshare\b",
    r"\bshares\b",
    r"\bsharing\b",

    r"\bdisclose\b",
    r"\bdiscloses\b",
    r"\bdisclosure\b",

    r"\bsell\b",
    r"\bsells\b",
    r"\bselling\b",

    r"\buse\b",
    r"\buses\b",
    r"\busing\b",
    r"\bprocess\b",
    r"\bprocesses\b",
    r"\bprocessing\b",

    r"\bstore\b",
    r"\bstores\b",
    r"\bstoring\b",
    r"\bstored\b",

    r"\bretain\b",
    r"\bretains\b",
    r"\bretaining\b",
    r"\bretention\b",

    r"\bdelete\b",
    r"\bdeletes\b",
    r"\bdeleting\b",
    r"\bdeletion\b",

    r"\berase\b",
    r"\berases\b",
    r"\berasing\b",

    r"\btransfer\b",
    r"\btransfers\b",
    r"\btransferring\b",

    r"\bcookie\b",
    r"\bcookies\b",

    r"\btracking\b",
    r"\btrack\b",
    r"\btracker\b",
    r"\banalytics\b",

    r"\bpersonal data\b",
    r"\bpersonal information\b",
    r"\bprivate information\b",

    r"\bthird[- ]party\b",
    r"\bthird[- ]parties\b",

    r"\bdata broker\b",
    r"\bdata brokers\b",
]


def is_privacy_relevant(sentence):
    try:
        sentence_lower = sentence.lower()

        for pattern in PRIVACY_TERMS:
            if re.search(pattern, sentence_lower):
                return True

        return False

    except Exception as ex:
        print(f"[ERROR] Privacy relevance check failed: {ex}")
        return False


def filter_relevant_sentences(sentences):
    relevant_sentences = []

    try:
        for sentence in sentences:
            if is_privacy_relevant(sentence):
                relevant_sentences.append(sentence)

        return relevant_sentences

    except Exception as ex:
        print(
            f"[ERROR] Privacy relevance filtering failed: {ex}"
        )
        return []