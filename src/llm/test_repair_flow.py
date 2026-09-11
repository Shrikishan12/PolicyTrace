from src.policy.dependency_extractor import extract_claims
from src.policy.claim_validator import validate_claims
from src.llm.mistral_client import call_mistral


TEST_SENTENCE = (
    "We do not collect, store, or share any personal data "
    "from visitors without their explicit consent."
)


def run_repair_test():
    try:
        print("=" * 80)
        print("ORIGINAL SENTENCE")
        print("=" * 80)
        print(TEST_SENTENCE)

        # --------------------------------------------------
        # 1. spaCy extraction
        # --------------------------------------------------

        spacy_claims = extract_claims(TEST_SENTENCE)

        print("\n" + "=" * 80)
        print("SPACY CLAIMS")
        print("=" * 80)

        for claim in spacy_claims:
            print(claim)

        # --------------------------------------------------
        # 2. Claim validation
        # --------------------------------------------------

        validation_results = validate_claims(
            spacy_claims
        )

        print("\n" + "=" * 80)
        print("VALIDATION")
        print("=" * 80)

        for result in validation_results:
            print(result)

        # --------------------------------------------------
        # 3. Find incomplete claims
        # --------------------------------------------------

        incomplete_claims = []
        problems = []

        for result in validation_results:
            validation = result["validation"]

            if validation["needs_llm"]:
                incomplete_claims.append(
                    result["claim"]
                )

                problems.extend(
                    validation["problems"]
                )

        print("\n" + "=" * 80)
        print("INCOMPLETE CLAIMS")
        print("=" * 80)

        for claim in incomplete_claims:
            print(claim)

        print("\nPROBLEMS:")
        print(problems)

        # --------------------------------------------------
        # 4. Mistral repair
        # --------------------------------------------------

        if incomplete_claims:
            repaired_result = call_mistral(
                sentence=TEST_SENTENCE,
                spaCy_claims=incomplete_claims,
                problems=problems,
                mode="repair",
            )

            print("\n" + "=" * 80)
            print("MISTRAL REPAIR RESULT")
            print("=" * 80)
            print(repaired_result)

        else:
            print(
                "\nNo incomplete claims found. "
                "Mistral repair was not required."
            )

    except Exception as ex:
        print(
            f"[ERROR] Repair flow test failed: {ex}"
        )


if __name__ == "__main__":
    run_repair_test()