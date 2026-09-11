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

from src.llm.groq_client import (
    call_groq
)


TEST_SENTENCES = [

    "We do not collect, store, or share personal data.",

    "If you voluntarily provide information, it will be used only for academic purposes and will not be shared with any third party.",

    "This policy covers information collected through our website.",

    "No Data Sharing. The college follows a no data sharing policy.",

    "We ensure that any student or visitor information is kept confidential and used exclusively within the institution.",

]


def load_nlp_model():
    try:
        return spacy.load(
            "en_core_web_sm"
        )

    except Exception as ex:
        print(
            f"[ERROR] Could not load spaCy model: {ex}"
        )
        return None


def get_spacy_claims(sentence, nlp):
    try:
        doc = nlp(sentence)

        claims = []

        for sent in doc.sents:

            if not is_privacy_relevant(
                sent.text
            ):
                continue

            actions = find_privacy_actions(
                sent
            )

            for action in actions:

                claim = extract_claim(
                    sent,
                    action
                )

                if claim:

                    validation = validate_claim(
                        claim
                    )

                    if validation["valid"]:
                        claims.append(
                            claim
                        )

        return claims

    except Exception as ex:
        print(
            f"[ERROR] spaCy extraction failed: {ex}"
        )
        return []


def test_groq_review(sentence, nlp):
    try:
        print("\n" + "=" * 80)
        print("ORIGINAL SENTENCE")
        print("=" * 80)
        print(sentence)

        # --------------------------------
        # 1. Get spaCy preliminary claims
        # --------------------------------
        spacy_claims = get_spacy_claims(
            sentence,
            nlp
        )

        print("\n[SPACY PRELIMINARY CLAIMS]")
        print("-" * 80)

        if not spacy_claims:
            print("NONE")
        else:
            for claim in spacy_claims:
                print(claim)

        # --------------------------------
        # 2. Send sentence + spaCy output
        #    to Groq
        # --------------------------------
        groq_result = call_groq(
            sentence=sentence,
            spacy_claims=spacy_claims,
            problems=[]
        )

        print("\n[GROQ REVIEW]")
        print("-" * 80)

        if groq_result is None:
            print("Groq returned no result.")
            return

        claims = groq_result.get(
            "claims",
            []
        )

        if not claims:
            print("No claims.")

        else:
            for claim in claims:
                print(claim)

    except Exception as ex:
        print(
            f"[ERROR] Groq review test failed: {ex}"
        )


def run_tests():
    try:
        print("\n")
        print("#" * 80)
        print("POLICYTRACE - GROQ STAGE 2 REVIEW TEST")
        print("#" * 80)

        nlp = load_nlp_model()

        if nlp is None:
            return

        for index, sentence in enumerate(
            TEST_SENTENCES,
            start=1
        ):

            print(
                f"\n\nTEST CASE {index}"
            )

            test_groq_review(
                sentence,
                nlp
            )

        print("\n")
        print("#" * 80)
        print("GROQ STAGE 2 TEST COMPLETED")
        print("#" * 80)

    except Exception as ex:
        print(
            f"[ERROR] Groq testing failed: {ex}"
        )


if __name__ == "__main__":
    run_tests()