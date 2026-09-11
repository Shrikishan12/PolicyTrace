import os
import json

from dotenv import load_dotenv
from google import genai

from src.llm.prompts import (
    SYSTEM_PROMPT,
    build_repair_prompt,
    build_extract_prompt,
)

from src.llm.schema import CLAIM_SCHEMA


load_dotenv()


def create_gemini_client():
    try:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            print("[ERROR] GEMINI_API_KEY is not set.")
            return None

        return genai.Client(api_key=api_key)

    except Exception as ex:
        print(
            f"[ERROR] Could not create Gemini client: {ex}"
        )
        return None


def get_gemini_model():
    try:
        return os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        )

    except Exception as ex:
        print(
            f"[ERROR] Could not read Gemini model: {ex}"
        )
        return "gemini-2.5-flash"


def call_gemini(
    sentence,
    spaCy_claims=None,
    problems=None,
    mode="repair",
):
    try:
        client = create_gemini_client()

        if client is None:
            return None

        model = get_gemini_model()

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
                f"[ERROR] Unknown Gemini mode: {mode}"
            )
            return None

        response = client.models.generate_content(
            model=model,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                SYSTEM_PROMPT
                                + "\n\n"
                                + user_prompt
                            )
                        }
                    ],
                }
            ],
            config={
                "temperature": 0,
                "response_mime_type": "application/json",
                "response_json_schema": CLAIM_SCHEMA,
            },
        )

        content = response.text

        if not content:
            print("[ERROR] Gemini returned empty content.")
            return None

        return json.loads(content)

    except json.JSONDecodeError as ex:
        print(
            f"[ERROR] Gemini returned invalid JSON: {ex}"
        )
        return None

    except Exception as ex:
        print(
            f"[ERROR] Gemini API call failed: {ex}"
        )
        return None