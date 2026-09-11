import os

from dotenv import load_dotenv
from mistralai.client import Mistral
import json

from src.llm.prompts import (
    SYSTEM_PROMPT,
    build_repair_prompt,
    build_extract_prompt,
)

from src.llm.schema import CLAIM_SCHEMA


load_dotenv()


def create_mistral_client():
    try:
        api_key = os.getenv("MISTRAL_API_KEY")

        if not api_key:
            print("[ERROR] MISTRAL_API_KEY is not set.")
            return None

        return Mistral(api_key=api_key)

    except Exception as ex:
        print(
            f"[ERROR] Could not create Mistral client: {ex}"
        )
        return None


def get_mistral_model():
    try:
        model = os.getenv(
            "MISTRAL_MODEL",
            "mistral-small-latest"
        )

        return model

    except Exception as ex:
        print(
            f"[ERROR] Could not read Mistral model: {ex}"
        )
        return "mistral-small-latest"


def call_mistral(
    sentence,
    spaCy_claims=None,
    problems=None,
    mode="repair",
):
    try:
        client = create_mistral_client()

        if client is None:
            return None

        model = get_mistral_model()

        if mode == "repair":
            user_prompt = build_repair_prompt(
                sentence,
                spaCy_claims or [],
                problems or [],
            )

        elif mode == "extract":
            user_prompt = build_extract_prompt(sentence)

        else:
            print(
                f"[ERROR] Unknown Mistral mode: {mode}"
            )
            return None

        response = client.chat.complete(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "privacy_claims",
                    "schema": CLAIM_SCHEMA,
                },
            },
            temperature=0,
        )

        content = response.choices[0].message.content

        if not content:
            print("[ERROR] Mistral returned empty content.")
            return None

        if isinstance(content, str):
            return json.loads(content)

        return content

    except json.JSONDecodeError as ex:
        print(
            f"[ERROR] Mistral returned invalid JSON: {ex}"
        )
        return None

    except Exception as ex:
        print(
            f"[ERROR] Mistral API call failed: {ex}"
        )
        return None