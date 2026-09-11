# for testing of spacy and en-core-web-sm
import spacy


def inspect_sentence(sentence):
    try:
        nlp = spacy.load("en_core_web_sm")

        doc = nlp(sentence)

        print("\nDEPENDENCY ANALYSIS\n")

        for token in doc:
            print(
                f"{token.text:<20}"
                f"POS={token.pos_:<8}"
                f"DEP={token.dep_:<10}"
                f"HEAD={token.head.text}"
            )

    except Exception as ex:
        print(f"[ERROR] Dependency analysis failed: {ex}")


if __name__ == "__main__":

    sentence = (
    "1. This Privacy Policy outlines how we handle and protect any information collected through our website."

    "2. If you voluntarily provide information (e.g., via forms or email), it will be used only for academic or administrative purposes and will not be shared with any third party."

    "3. No Data Sharing The college strictly follows a no data sharing policy."

    "4. We ensure that any student or visitor information is kept confidential and used exclusively within the institution for necessary communication and support."
)

    inspect_sentence(sentence)