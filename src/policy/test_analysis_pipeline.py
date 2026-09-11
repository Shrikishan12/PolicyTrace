from src.policy.analysis_pipeline import (
    analyze_policy_claims
)


POLICY_TEXT = """
We collect personal information from students and visitors.

We use cookies to improve our website.

We do not sell personal information.

We may share personal information with service providers.

We do not collect, store, or share personal data without consent.

Your information will be used for administrative purposes.

This policy covers information collected through our website.

No Data Sharing. The college follows a no data sharing policy.
"""


def run_test():
    try:
        print("\n")
        print("#" * 80)
        print("POLICYTRACE - FULL POLICY CLAIM ANALYSIS TEST")
        print("#" * 80)

        claims = analyze_policy_claims(
            POLICY_TEXT
        )

        print("\n")
        print("=" * 80)
        print("FINAL CLAIMS")
        print("=" * 80)

        if not claims:
            print("No claims returned.")
            return

        for index, claim in enumerate(
            claims,
            start=1
        ):

            print(
                f"\nCLAIM {index}"
            )

            print(
                f"Sentence    : "
                f"{claim.get('sentence')}"
            )

            print(
                f"Actor       : "
                f"{claim.get('actor')}"
            )

            print(
                f"Action      : "
                f"{claim.get('action')}"
            )

            print(
                f"Polarity    : "
                f"{claim.get('polarity')}"
            )

            print(
                f"Data Object : "
                f"{claim.get('data_object')}"
            )

            print(
                f"Entity      : "
                f"{claim.get('entity')}"
            )

        print("\n")
        print("#" * 80)
        print("FULL POLICY TEST COMPLETED")
        print("#" * 80)

    except Exception as ex:
        print(
            f"[ERROR] Full policy test failed: "
            f"{ex}"
        )


if __name__ == "__main__":
    run_test()