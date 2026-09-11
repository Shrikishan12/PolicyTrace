import time

from src.llm.mistral_client import call_mistral
from src.llm.gemini_client import call_gemini

TEST_CASES = [
    {
        "name": "Coordinated actions",
        "sentence": (
            "We do not collect, store, or share any personal data "
            "from visitors without their explicit consent."
        ),
    },
    {
        "name": "Passive construction",
        "sentence": (
            "If you voluntarily provide information, it will be used "
            "only for academic or administrative purposes and will not "
            "be shared with any third party."
        ),
    },
    {
        "name": "Actor inheritance",
        "sentence": (
            "We ensure that any student or visitor information is kept "
            "confidential and used exclusively within the institution "
            "for necessary communication and support."
        ),
    },
    {
        "name": "No data sharing noun phrase",
        "sentence": (
            "No Data Sharing. The college strictly follows a "
            "no data sharing policy."
        ),
    },
    {
        "name": "Collected as modifier",
        "sentence": (
            "This Privacy Policy outlines how we handle and protect "
            "any information collected through our website."
        ),
    },
]


def run_test_case(test_case):
    try:
        print("\n" + "=" * 80)
        print(f"TEST: {test_case['name']}")
        print("=" * 80)

        print("\nSENTENCE:")
        print(test_case["sentence"])

        result = call_gemini(
            sentence=test_case["sentence"],
            spaCy_claims=[],
            problems=[],
            mode="extract",
        )

        print("\nMISTRAL OUTPUT:")
        print(result)

        return result

    except Exception as ex:
        print(
            f"[ERROR] Test case failed: {ex}"
        )
        return None


def run_all_tests():
    try:
        results = []

        for index, test_case in enumerate(TEST_CASES):
            result = run_test_case(test_case)

            results.append({
                "name": test_case["name"],
                "result": result,
            })

            if index < len(TEST_CASES) - 1:
                print("\nWaiting before next API request...")
                time.sleep(2)

        return results

    except Exception as ex:
        print(
            f"[ERROR] LLM test suite failed: {ex}"
        )
        return []


if __name__ == "__main__":
    run_all_tests()