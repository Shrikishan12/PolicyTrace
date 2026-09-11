import os
import json

from dotenv import load_dotenv
from groq import Groq

from src.llm.schema import CLAIM_SCHEMA
from src.llm.prompts import (
    SYSTEM_PROMPT,
    build_review_prompt
)


load_dotenv()


def create_groq_client():
    try:
        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:
            print(
                "[ERROR] GROQ_API_KEY is not set."
            )
            return None

        return Groq(
            api_key=api_key
        )

    except Exception as ex:
        print(
            f"[ERROR] Could not create Groq client: {ex}"
        )
        return None


def call_groq(
    sentence,
    spacy_claims,
    problems
):
    try:
        client = create_groq_client()

        if client is None:
            return None

        model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

        user_prompt = build_review_prompt(
            sentence=sentence,
            spaCy_claims=spacy_claims,
            problems=problems
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "privacy_claims",
                    "strict": True,
                    "schema": CLAIM_SCHEMA
                }
            }
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:
            print(
                "[ERROR] Groq returned empty content."
            )
            return None

        return json.loads(content)

    except Exception as ex:
        print(
            f"[ERROR] Groq request failed: {ex}"
        )
        return None