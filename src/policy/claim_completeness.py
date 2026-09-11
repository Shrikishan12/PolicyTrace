from src.policy.dependency_extractor import (
    PRIVACY_ACTIONS
)


def find_sentence_actions(sentence):
    try:
        actions = []

        for token in sentence:
            if token.lemma_.lower() in PRIVACY_ACTIONS:
                if token.pos_ == "VERB":
                    actions.append(
                        token.lemma_.lower()
                    )

        return actions

    except Exception as ex:
        print(
            f"[ERROR] Could not find sentence actions: {ex}"
        )
        return []


def get_claim_actions(claims):
    try:
        return {
            claim.get("action")
            for claim in claims
            if claim.get("action")
        }

    except Exception as ex:
        print(
            f"[ERROR] Could not get claim actions: {ex}"
        )
        return set()


def check_claim_completeness(sentence, claims):
    try:
        sentence_actions = set(
            find_sentence_actions(sentence)
        )

        claim_actions = get_claim_actions(
            claims
        )

        missing_actions = (
            sentence_actions - claim_actions
        )

        return {
            "complete": len(missing_actions) == 0,
            "sentence_actions": sorted(
                sentence_actions
            ),
            "extracted_actions": sorted(
                claim_actions
            ),
            "missing_actions": sorted(
                missing_actions
            )
        }

    except Exception as ex:
        print(
            f"[ERROR] Claim completeness check failed: {ex}"
        )

        return {
            "complete": False,
            "sentence_actions": [],
            "extracted_actions": [],
            "missing_actions": []
        }