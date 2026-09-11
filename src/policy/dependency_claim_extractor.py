import spacy


# ---------------------------------------------------------
# Privacy-related actions
# ---------------------------------------------------------

PRIVACY_ACTIONS = {
    "collect",
    "gather",
    "obtain",
    "receive",
    "share",
    "disclose",
    "sell",
    "use",
    "process",
    "store",
    "retain",
    "keep"
}


# ---------------------------------------------------------
# Model
# ---------------------------------------------------------

def load_nlp_model():
    try:
        return spacy.load("en_core_web_sm")

    except Exception as ex:
        print(
            f"[ERROR] Could not load spaCy model: {ex}"
        )

        return None


# ---------------------------------------------------------
# Phrase extraction
# ---------------------------------------------------------

def get_phrase(token):
    """
    Build a noun phrase around a token.

    Example:

        personal information

        your personal information

        student or visitor information
    """

    try:
        token_indices = {token.i}

        # Normal modifiers
        for child in token.children:

            if child.dep_ in {
                "det",
                "amod",
                "compound",
                "poss"
            }:

                token_indices.add(
                    child.i
                )

        # Coordinated noun
        for conjunct in token.conjuncts:

            token_indices.add(
                conjunct.i
            )

            for child in conjunct.children:

                if child.dep_ in {
                    "det",
                    "amod",
                    "compound",
                    "poss"
                }:

                    token_indices.add(
                        child.i
                    )

        token_indices = sorted(
            token_indices
        )

        return " ".join(
            token.doc[i].text
            for i in token_indices
        )

    except Exception as ex:

        print(
            f"[ERROR] Phrase extraction failed: {ex}"
        )

        return token.text


# ---------------------------------------------------------
# Actor extraction
# ---------------------------------------------------------

def find_direct_actor(action_token):
    try:

        for child in action_token.children:

            if child.dep_ == "nsubj":

                return get_phrase(child)

        return None

    except Exception as ex:

        print(
            f"[ERROR] Direct actor extraction failed: {ex}"
        )

        return None


def find_actor(action_token):
    """
    Find actor for active actions.

    If the action is coordinated:

        We collect, store, or share data.

    then:

        collect -> We
        store   -> We
        share   -> We

    Actor is inherited from the governing action.
    """

    try:

        # 1. Direct actor
        actor = find_direct_actor(
            action_token
        )

        if actor:
            return actor

        # 2. Inherit actor from coordinated action
        current = action_token

        visited = set()

        while current.dep_ == "conj":

            if current.i in visited:
                break

            visited.add(
                current.i
            )

            parent = current.head

            actor = find_direct_actor(
                parent
            )

            if actor:
                return actor

            current = parent

        return None

    except Exception as ex:

        print(
            f"[ERROR] Actor extraction failed: {ex}"
        )

        return None


# ---------------------------------------------------------
# Data object extraction
# ---------------------------------------------------------

def find_direct_data_object(action_token):
    try:

        for child in action_token.children:

            if child.dep_ in {
                "dobj",
                "obj"
            }:

                return get_phrase(child)

        return None

    except Exception as ex:

        print(
            f"[ERROR] Data-object extraction failed: {ex}"
        )

        return None


def find_passive_subject(action_token):
    try:

        for child in action_token.children:

            if child.dep_ == "nsubjpass":

                return child

        return None

    except Exception as ex:

        print(
            f"[ERROR] Passive-subject extraction failed: {ex}"
        )

        return None


def find_data_object(action_token, visited=None):
    """
    Find data object for an action.

    Handles:

        We share personal information.

    and coordinated actions:

        We collect, store, or share personal data.

    and passive actions:

        Information is shared with third parties.
    """

    try:

        if visited is None:
            visited = set()

        if action_token.i in visited:
            return None

        visited.add(
            action_token.i
        )

        # -------------------------------------------------
        # 1. Direct object
        # -------------------------------------------------

        data_object = find_direct_data_object(
            action_token
        )

        if data_object:
            return data_object

        # -------------------------------------------------
        # 2. Passive subject
        # -------------------------------------------------

        passive_subject = find_passive_subject(
            action_token
        )

        if passive_subject:

            return get_phrase(
                passive_subject
            )

        # -------------------------------------------------
        # 3. Search coordinated actions
        # -------------------------------------------------

        for conjunct in action_token.conjuncts:

            data_object = find_data_object(
                conjunct,
                visited
            )

            if data_object:
                return data_object

        # -------------------------------------------------
        # 4. Search parent coordinated action
        # -------------------------------------------------

        if action_token.dep_ == "conj":

            parent = action_token.head

            data_object = find_data_object(
                parent,
                visited
            )

            if data_object:
                return data_object

        return None

    except Exception as ex:

        print(
            f"[ERROR] Data-object extraction failed: {ex}"
        )

        return None


# ---------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------

def find_entity(action_token):
    """
    Find receiving entities.

    Example:

        share data with third parties

    -> third parties

    We intentionally do not treat:

        collect data from visitors

    as an entity.
    """

    try:

        preferred_prepositions = {
            "with",
            "to",
            "by"
        }

        # Search the action and its coordinated actions.
        actions_to_check = [
            action_token
        ]

        actions_to_check.extend(
            list(action_token.conjuncts)
        )

        for current_action in actions_to_check:

            for token in current_action.subtree:

                if (
                    token.dep_ == "prep"
                    and token.text.lower()
                    in preferred_prepositions
                ):

                    for child in token.children:

                        if child.dep_ == "pobj":

                            return get_phrase(
                                child
                            )

        # If this is a coordinated action,
        # inspect its parent too.
        if action_token.dep_ == "conj":

            parent = action_token.head

            entity = find_entity(
                parent
            )

            if entity:
                return entity

        return None

    except Exception as ex:

        print(
            f"[ERROR] Entity extraction failed: {ex}"
        )

        return None


# ---------------------------------------------------------
# Polarity
# ---------------------------------------------------------

def detect_polarity(action_token):
    """
    Detect direct dependency negation.

    Example:

        do not collect

        not -> neg -> collect
    """

    try:

        # Direct negation
        for child in action_token.children:

            if child.dep_ == "neg":
                return "denies"

        # Coordinated actions inherit negation.
        if action_token.dep_ == "conj":

            parent = action_token.head

            parent_polarity = detect_polarity(
                parent
            )

            if parent_polarity == "denies":
                return "denies"

        return "affirms"

    except Exception as ex:

        print(
            f"[ERROR] Polarity detection failed: {ex}"
        )

        return "affirms"


# ---------------------------------------------------------
# Candidate action detection
# ---------------------------------------------------------

def is_privacy_action(token):
    """
    Determine whether a token is actually being used
    as a privacy/data action.

    This prevents:

        data sharing policy

    from becoming:

        action = share
    """

    try:

        lemma = token.lemma_.lower()

        if lemma not in PRIVACY_ACTIONS:
            return False

        # Actual verb
        if token.pos_ == "VERB":
            return True

        return False

    except Exception as ex:

        print(
            f"[ERROR] Privacy-action detection failed: {ex}"
        )

        return False


def find_privacy_actions(sentence):
    """
    Find privacy actions in a sentence.

    We accept actual verbs and exclude noun/compound
    usages such as:

        data sharing policy
    """

    actions = []

    try:

        for token in sentence:

            if is_privacy_action(
                token
            ):

                actions.append(
                    token
                )

        return actions

    except Exception as ex:

        print(
            f"[ERROR] Privacy action search failed: {ex}"
        )

        return []


# ---------------------------------------------------------
# Simple reference resolution
# ---------------------------------------------------------

def resolve_data_reference(
    data_object,
    sentence
):
    """
    Resolve simple passive pronouns such as:

        it will be used

    when an earlier noun phrase contains:

        information

    This is deliberately conservative.
    """

    try:

        if not data_object:
            return None

        if data_object.lower() not in {
            "it",
            "this",
            "that"
        }:

            return data_object

        # Look backwards for a noun phrase that could
        # represent the data.
        action_index = None

        for token in sentence:

            if token.text.lower() in {
                "it",
                "this",
                "that"
            }:

                action_index = token.i
                break

        if action_index is None:
            return data_object

        candidates = []

        for token in sentence:

            if token.i >= action_index:
                continue

            if token.pos_ in {
                "NOUN",
                "PROPN"
            }:

                phrase = get_phrase(
                    token
                )

                if phrase:
                    candidates.append(
                        (
                            token.i,
                            phrase
                        )
                    )

        if not candidates:
            return data_object

        # Prefer the closest previous noun.
        candidates.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return candidates[0][1]

    except Exception as ex:

        print(
            f"[ERROR] Reference resolution failed: {ex}"
        )

        return data_object


# ---------------------------------------------------------
# Claim extraction
# ---------------------------------------------------------

def extract_claim(
    sentence,
    action_token
):
    try:

        actor = find_actor(
            action_token
        )

        data_object = find_data_object(
            action_token
        )

        entity = find_entity(
            action_token
        )

        polarity = detect_polarity(
            action_token
        )

        # Simple pronoun resolution.
        if data_object:

            data_object = resolve_data_reference(
                data_object,
                sentence
            )

        return {
            "sentence": sentence.text.strip(),
            "actor": actor,
            "action": action_token.lemma_.lower(),
            "polarity": polarity,
            "data_object": data_object,
            "entity": entity
        }

    except Exception as ex:

        print(
            f"[ERROR] Claim extraction failed: {ex}"
        )

        return None


# ---------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------

def extract_claims(text):

    claims = []

    try:

        nlp = load_nlp_model()

        if nlp is None:
            return claims

        doc = nlp(
            text
        )

        for sentence in doc.sents:

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
            f"[ERROR] Dependency claim extraction failed: {ex}"
        )

        return claims


# ---------------------------------------------------------
# Real policy test
# ---------------------------------------------------------

if __name__ == "__main__":

    from src.crawler.http_crawler import fetch_page
    from src.policy.extractor import extract_policy_text

    website_url = (
        "https://vtpoddar.com"
    )

    policy_url = (
        "https://vtpoddar.com/?page_id=6447"
    )

    try:

        # 1. Fetch policy
        policy_html = fetch_page(
            policy_url
        )

        # 2. Extract text
        policy_text = extract_policy_text(
            policy_html
        )

        # 3. Extract claims
        claims = extract_claims(
            policy_text
        )

        # 4. Display
        print(
            "\nDEPENDENCY-BASED POLICY CLAIMS\n"
        )

        print(
            f"Website: {website_url}"
        )

        print(
            f"Policy: {policy_url}"
        )

        print(
            f"Claims found: {len(claims)}"
        )

        print()

        for number, claim in enumerate(
            claims,
            start=1
        ):

            print(
                f"Claim {number}"
            )

            print(
                "-" * 60
            )

            print(
                f"Sentence:    {claim['sentence']}"
            )

            print(
                f"Actor:       {claim['actor']}"
            )

            print(
                f"Action:      {claim['action']}"
            )

            print(
                f"Polarity:    {claim['polarity']}"
            )

            print(
                f"Data object: {claim['data_object']}"
            )

            print(
                f"Entity:      {claim['entity']}"
            )

            print()

    except Exception as ex:

        print(
            f"[ERROR] Real policy dependency analysis failed: {ex}"
        )