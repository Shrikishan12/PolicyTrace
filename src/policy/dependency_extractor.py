import spacy

PRIVACY_ACTIONS = {
    "collect", "gather", "obtain", "receive",
    "share", "disclose", "sell", "use", "process",
    "store", "retain", "keep",
}

# Supplementary check for bare "no" as a noun-phrase negator, e.g.
# "a no data sharing policy" — see fix #3 above.
NO_WINDOW_WORDS = 4


def load_nlp_model():
    try:
        return spacy.load("en_core_web_sm")
    except Exception as ex:
        print(f"[ERROR] Could not load spaCy model: {ex}")
        return None


def get_phrase(token):
    try:
        token_indices = {token.i}
        for child in token.children:
            if child.dep_ in {"det", "amod", "compound", "poss"}:
                token_indices.add(child.i)
        for conjunct in token.conjuncts:
            token_indices.add(conjunct.i)
            for child in conjunct.children:
                if child.dep_ in {"det", "amod", "compound", "poss"}:
                    token_indices.add(child.i)
        token_indices = sorted(token_indices)
        return " ".join(token.doc[i].text for i in token_indices)
    except Exception as ex:
        print(f"[ERROR] Phrase extraction failed: {ex}")
        return token.text


def find_direct_actor(action_token):
    try:
        for child in action_token.children:
            if child.dep_ == "nsubj":
                return get_phrase(child)
        return None
    except Exception as ex:
        print(f"[ERROR] Direct actor extraction failed: {ex}")
        return None


def find_actor(action_token):
    try:
        actor = find_direct_actor(action_token)
        if actor:
            return actor
        current = action_token
        visited = set()
        while current.dep_ == "conj":
            if current.i in visited:
                break
            visited.add(current.i)
            parent = current.head
            actor = find_direct_actor(parent)
            if actor:
                return actor
            current = parent
        return None
    except Exception as ex:
        print(f"[ERROR] Actor extraction failed: {ex}")
        return None


def find_direct_data_object(action_token):
    try:
        for child in action_token.children:
            if child.dep_ in {"dobj", "obj"}:
                return get_phrase(child)

        # FIX 1: participial modifier — the action is a child of the noun
        # it describes ("information collected"), not the other way round.
        if action_token.dep_ == "acl":
            return get_phrase(action_token.head)

        return None
    except Exception as ex:
        print(f"[ERROR] Data-object extraction failed: {ex}")
        return None


def find_passive_subject(action_token):
    try:
        for child in action_token.children:
            if child.dep_ == "nsubjpass":
                return child
        return None
    except Exception as ex:
        print(f"[ERROR] Passive-subject extraction failed: {ex}")
        return None


def find_data_object(action_token, visited=None):
    try:
        if visited is None:
            visited = set()
        if action_token.i in visited:
            return None
        visited.add(action_token.i)

        data_object = find_direct_data_object(action_token)
        if data_object:
            return data_object

        passive_subject = find_passive_subject(action_token)
        if passive_subject:
            return get_phrase(passive_subject)

        for conjunct in action_token.conjuncts:
            data_object = find_data_object(conjunct, visited)
            if data_object:
                return data_object

        if action_token.dep_ == "conj":
            parent = action_token.head
            data_object = find_data_object(parent, visited)
            if data_object:
                return data_object

        return None
    except Exception as ex:
        print(f"[ERROR] Data-object extraction failed: {ex}")
        return None


def find_entity(action_token):
    try:
        preferred_prepositions = {"with", "to", "by"}
        actions_to_check = [action_token]
        actions_to_check.extend(list(action_token.conjuncts))

        for current_action in actions_to_check:
            for token in current_action.subtree:
                if token.dep_ == "prep" and token.text.lower() in preferred_prepositions:
                    for child in token.children:
                        if child.dep_ == "pobj":
                            return get_phrase(child)

        if action_token.dep_ == "conj":
            parent = action_token.head
            entity = find_entity(parent)
            if entity:
                return entity

        return None
    except Exception as ex:
        print(f"[ERROR] Entity extraction failed: {ex}")
        return None


def detect_polarity(action_token, sentence):
    try:
        for child in action_token.children:
            if child.dep_ == "neg":
                return "denies"

        if action_token.dep_ == "conj":
            parent_polarity = detect_polarity(action_token.head, sentence)
            if parent_polarity == "denies":
                return "denies"

        # FIX 3: bare "no" check, scoped to a short window of words
        # immediately before the action token, within this sentence only.
        sentence_text = sentence.text
        token_offset_in_sentence = action_token.idx - sentence.start_char
        prefix = sentence_text[:token_offset_in_sentence]
        window = " ".join(prefix.split()[-NO_WINDOW_WORDS:])
        if any(w.lower() == "no" for w in window.split()):
            return "denies"

        return "affirms"
    except Exception as ex:
        print(f"[ERROR] Polarity detection failed: {ex}")
        return "affirms"


def is_privacy_action(token):
    try:
        lemma = token.lemma_.lower()
        if lemma not in PRIVACY_ACTIONS:
            return False
        return token.pos_ == "VERB"
    except Exception as ex:
        print(f"[ERROR] Privacy-action detection failed: {ex}")
        return False


def find_privacy_actions(sentence):
    actions = []
    try:
        for token in sentence:
            if is_privacy_action(token):
                actions.append(token)
        return actions
    except Exception as ex:
        print(f"[ERROR] Privacy action search failed: {ex}")
        return []


def resolve_data_reference(data_object, sentence):
    try:
        if not data_object:
            return None
        if data_object.lower() not in {"it", "this", "that"}:
            return data_object

        action_index = None
        for token in sentence:
            if token.text.lower() in {"it", "this", "that"}:
                action_index = token.i
                break
        if action_index is None:
            return data_object

        candidates = []
        paren_depth = 0
        for token in sentence:
            # FIX 2: track parenthetical depth and skip nouns inside one —
            # "(e.g., via forms or email)" sits closer to "it" than the
            # real antecedent "information", so an un-scoped nearest-noun
            # search picks the wrong word.
            if token.text == "(":
                paren_depth += 1
            elif token.text == ")":
                paren_depth = max(0, paren_depth - 1)

            if token.i >= action_index:
                continue
            if token.pos_ in {"NOUN", "PROPN"} and paren_depth == 0:
                phrase = get_phrase(token)
                if phrase:
                    candidates.append((token.i, phrase))

        if not candidates:
            return data_object
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]
    except Exception as ex:
        print(f"[ERROR] Reference resolution failed: {ex}")
        return data_object


def extract_claim(sentence, action_token):
    try:
        actor = find_actor(action_token)
        data_object = find_data_object(action_token)
        entity = find_entity(action_token)
        polarity = detect_polarity(action_token, sentence)

        if data_object:
            data_object = resolve_data_reference(data_object, sentence)

        return {
            "sentence": sentence.text.strip(),
            "actor": actor,
            "action": action_token.lemma_.lower(),
            "polarity": polarity,
            "data_object": data_object,
            "entity": entity,
        }
    except Exception as ex:
        print(f"[ERROR] Claim extraction failed: {ex}")
        return None


def extract_claims(text):
    claims = []
    try:
        nlp = load_nlp_model()
        if nlp is None:
            return claims
        doc = nlp(text)
        for sentence in doc.sents:
            actions = find_privacy_actions(sentence)
            for action_token in actions:
                claim = extract_claim(sentence, action_token)
                if claim:
                    claims.append(claim)
        return claims
    except Exception as ex:
        print(f"[ERROR] Dependency claim extraction failed: {ex}")
        return claims

