from src.policy.pipeline import (
    analyze_website_policy
)


def run_test():
    try:
        website_url = (
            "https://vtpoddar.com"
        )

        result = analyze_website_policy(
            website_url
        )

        print("\n")
        print("#" * 80)
        print("POLICYTRACE - REAL WEBSITE POLICY TEST")
        print("#" * 80)

        print(
            "\nWebsite URL:"
        )
        print(
            result["website_url"]
        )

        print(
            "\nPrivacy Policy URL:"
        )
        print(
            result["privacy_policy_url"]
        )

        print(
            "\nFinal Claims:"
        )

        claims = result["claims"]

        if not claims:
            print("No claims found.")
            return

        for index, claim in enumerate(
            claims,
            start=1
        ):
            print(
                f"\nCLAIM {index}"
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
                f"Condition   : "
                f"{claim.get('condition')}"
            )

            print(
                f"Data Object : "
                f"{claim.get('data_object')}"
            )

            print(
                f"Entity      : "
                f"{claim.get('entity')}"
            )

            print(
                f"Sentence    : "
                f"{claim.get('sentence')}"
            )

    except Exception as ex:
        print(
            f"[ERROR] Real policy test failed: "
            f"{ex}"
        )


if __name__ == "__main__":
    run_test()