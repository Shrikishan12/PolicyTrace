import spacy

from src.policy.relevance_filter import (
    is_privacy_relevant
)

from src.policy.dependency_extractor import (
    find_privacy_actions,
    extract_claim
)

from src.policy.claim_validator import (
    validate_claim
)


TEST_SENTENCES = [

    # 1. Simple positive collection
    "We collect personal information.",

    # 2. Simple negative collection
    "We do not collect personal information.",

    # 3. Coordinated actions
    "We do not collect, store, or share personal data.",

    # 4. Passive voice
    "Your information will be used for administrative purposes.",

    # 5. Sharing with an entity
    "We may share information with third parties.",

    # 6. Noun phrase / possible false positive
    "No Data Sharing. The college follows a no data sharing policy.",

    # 7. Privacy action used as a modifier
    "This policy covers information collected through our website.",

    # 8. Passive keep and use
    "We ensure that any student or visitor information is kept confidential and used exclusively within the institution.",

    # 9. Passive use and share
    "If you voluntarily provide information, it will be used only for academic purposes and will not be shared with any third party.",

    # 10. Multiple positive actions
    "We collect, process, and retain your personal information.",

    # 11. Sharing with service providers
    "We may disclose your information to service providers.",

    # 12. Cookies
    "We use cookies and similar technologies to improve our website.",

    # 13. Tracking
    "We may use tracking technologies for analytics.",

    # 14. Negative sharing
    "We do not share your personal information with third parties.",

    # 15. Policy title
    "Privacy and Data Protection Policy.",
]


def load_nlp_model():
    try:
        return spacy.load("en_core_web_sm")

    except Exception as ex:
        print(
            f"[ERROR] Could not load spaCy model: {ex}"
        )
        return None


def inspect_sentence(sentence, nlp):
    try:
        print("\n" + "=" * 80)
        print("SENTENCE")
        print("=" * 80)
        print(sentence)

        # --------------------------------
        # 1. Relevance
        # --------------------------------
        relevant = is_privacy_relevant(
            sentence
        )

        print("\n[1. RELEVANCE]")
        print("-" * 80)

        if relevant:
            print("RELEVANT")
        else:
            print("NOT RELEVANT")
            return

        # --------------------------------
        # 2. spaCy parsing
        # --------------------------------
        doc = nlp(sentence)

        for sent in doc.sents:

            # --------------------------------
            # 3. Privacy actions
            # --------------------------------
            actions = find_privacy_actions(
                sent
            )

            print("\n[2. PRIVACY ACTIONS]")
            print("-" * 80)

            if not actions:
                print("NONE")
                continue

            for action in actions:
                print(
                    f"- {action.text}"
                    f"  → lemma = "
                    f"{action.lemma_.lower()}"
                )

            # --------------------------------
            # 4. Extract claims
            # --------------------------------
            extracted_claims = []

            print("\n[3. EXTRACTED CLAIMS]")
            print("-" * 80)

            for action in actions:

                claim = extract_claim(
                    sent,
                    action
                )

                if claim:
                    extracted_claims.append(
                        claim
                    )

                    print(
                        f"\nAction      : "
                        f"{claim['action']}"
                    )

                    print(
                        f"Actor       : "
                        f"{claim['actor']}"
                    )

                    print(
                        f"Data Object : "
                        f"{claim['data_object']}"
                    )

                    print(
                        f"Entity      : "
                        f"{claim['entity']}"
                    )

                    print(
                        f"Polarity    : "
                        f"{claim['polarity']}"
                    )

            # --------------------------------
            # 5. Validate claims
            # --------------------------------
            print("\n[4. CLAIM VALIDATION]")
            print("-" * 80)

            if not extracted_claims:
                print("NO CLAIMS TO VALIDATE")
                continue

            for claim in extracted_claims:

                validation = validate_claim(
                    claim
                )

                print(
                    f"\nAction : "
                    f"{claim['action']}"
                )

                print(
                    f"Status : "
                    f"{validation['status']}"
                )

                print(
                    f"Valid  : "
                    f"{validation['valid']}"
                )

                if validation["problems"]:
                    print(
                        f"Problems : "
                        f"{validation['problems']}"
                    )

    except Exception as ex:
        print(
            f"[ERROR] Sentence inspection failed: "
            f"{ex}"
        )


def run_stage1_tests():
    try:
        print("\n")
        print("#" * 80)
        print("POLICYTRACE - STAGE 1 SPACY PIPELINE TEST")
        print("#" * 80)

        # Load spaCy only once.
        nlp = load_nlp_model()

        if nlp is None:
            return

        # Test every sentence using the same spaCy pipeline.
        for index, sentence in enumerate(
            TEST_SENTENCES,
            start=1
        ):

            print(
                f"\n\nTEST CASE {index}"
            )

            inspect_sentence(
                sentence,
                nlp
            )

        print("\n")
        print("#" * 80)
        print("STAGE 1 TEST COMPLETED")
        print("#" * 80)

    except Exception as ex:
        print(
            f"[ERROR] Stage 1 testing failed: "
            f"{ex}"
        )


if __name__ == "__main__":
    run_stage1_tests()