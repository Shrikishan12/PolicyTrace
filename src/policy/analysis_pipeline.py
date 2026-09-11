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


def extract_spacy_claims(sentence):
    try:
        claims = []

        actions = find_privacy_actions(
            sentence
        )

        for action_token in actions:

            claim = extract_claim(
                sentence,
                action_token
            )

            if claim:
                claims.append(
                    claim
                )

        return claims

    except Exception as ex:
        print(
            f"[ERROR] spaCy claim extraction failed: {ex}"
        )
        return []


def validate_spacy_claims(claims):
    try:
        valid_claims = []
        problems = []

        for claim in claims:

            validation = validate_claim(
                claim
            )

            if validation["valid"]:
                valid_claims.append(
                    claim
                )

            problems.extend(
                validation.get(
                    "problems",
                    []
                )
            )

        return (
            valid_claims,
            problems
        )

    except Exception as ex:
        print(
            f"[ERROR] spaCy claim validation failed: {ex}"
        )

        return (
            [],
            [f"validation error: {str(ex)}"]
        )


def review_with_groq(sentence, spacy_claims, problems):
    try:
        print("\n[Groq] Reviewing sentence:")
        print(sentence)

        print("[Groq] spaCy claims:")
        print(spacy_claims)

        print("[Groq] Problems:")
        print(problems)

        result = call_groq(
            sentence=sentence,
            spacy_claims=spacy_claims,
            problems=problems
        )

        if not result:
            print("[Groq] No result returned.")
            return None

        claims = result.get(
            "claims",
            []
        )

        print("[Groq] Claims returned:")
        print(claims)

        return claims

    except Exception as ex:
        print(
            f"[ERROR] Groq review failed: {ex}"
        )
        return None


def analyze_policy_claims(
    policy_text
):
    try:
        if (
            not policy_text
            or not policy_text.strip()
        ):
            print(
                "[ERROR] Policy text is empty."
            )
            return []

        # --------------------------------
        # Load spaCy once
        # --------------------------------
        nlp = load_nlp_model()

        if nlp is None:
            return []

        # --------------------------------
        # Parse complete policy once
        # --------------------------------
        doc = nlp(
            policy_text
        )

        final_claims = []

        # --------------------------------
        # Process each sentence
        # --------------------------------
        for sentence in doc.sents:

            sentence_text = (
                sentence.text.strip()
            )

            if not sentence_text:
                continue

            # --------------------------------
            # 1. Relevance filtering
            # --------------------------------
            try:
                relevant = (
                    is_privacy_relevant(
                        sentence_text
                    )
                )

            except Exception as ex:
                print(
                    f"[ERROR] Relevance check failed: {ex}"
                )
                continue

            if not relevant:
                continue

            # --------------------------------
            # 2. spaCy extraction
            # --------------------------------
            spacy_claims = (
                extract_spacy_claims(
                    sentence
                )
            )

            # --------------------------------
            # 3. Validate spaCy claims
            # --------------------------------
            (
                valid_spacy_claims,
                problems
            ) = validate_spacy_claims(
                spacy_claims
            )

            # --------------------------------
            # 4. Groq semantic review
            # --------------------------------
            groq_claims = review_with_groq(
                sentence=sentence_text,
                spacy_claims=valid_spacy_claims,
                problems=problems
            )

            # --------------------------------
            # 5. Final claims
            # --------------------------------
            if groq_claims is not None:

                final_claims.extend(
                    groq_claims
                )

            else:

                # Groq/API failure fallback.
                final_claims.extend(
                    valid_spacy_claims
                )

        return final_claims

    except Exception as ex:
        print(
            f"[ERROR] Policy claim analysis failed: {ex}"
        )
        return []