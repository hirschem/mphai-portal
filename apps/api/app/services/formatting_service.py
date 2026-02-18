from openai import AsyncOpenAI
from app.models.config import get_settings
from app.models.schemas import ProposalData
import json
import logging
logger = logging.getLogger("api.formatting_service")

settings = get_settings()

from app.errors import StandardizedAIError
from app.ai.validate import validate_ai_doc_v1

def _format_validation_errors(err: Exception) -> str:
    return str(err)[:2000]

PROMPT_PREFIX = (
    "You MUST return exactly one JSON object matching the AiDocV1 schema.\n"
    "Do NOT return markdown. Do NOT wrap in code fences. Do NOT add any extra text.\n"
    "All money fields must be integer cents (e.g., 12500). Never use '$' or decimals.\n"
    "If information is missing, set the field to null and add a short warning in source.warnings.\n"
    "Do NOT invent phone/email/address.\n"
    "Output must be valid JSON (RFC 8259). One object only.\n"
)

def generate_doc(user_prompt, llm_client):
    base_prompt = PROMPT_PREFIX + user_prompt

    def call_model(prompt: str) -> str:
        return llm_client.generate(
            prompt=prompt,
            temperature=0.0,
            top_p=1.0,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            # ...existing model, max_tokens, etc.
        )

    raw1 = call_model(base_prompt)
    try:
        doc = validate_ai_doc_v1(raw1)
        return doc
    except Exception as e1:
        err_txt = _format_validation_errors(e1)
        retry_prompt = (
            base_prompt
            + "\n\nVALIDATION ERRORS:\n"
            + err_txt
            + "\n\nFix ONLY what is needed to satisfy AiDocV1. "
              "Return exactly one JSON object, no extra keys, no markdown."
        )
        raw2 = call_model(retry_prompt)
        try:
            doc2 = validate_ai_doc_v1(raw2)
            return doc2
        except Exception as e2:
            raise StandardizedAIError(
                code="AI_SCHEMA_VALIDATION_FAILED",
                message="AI output failed schema validation after retry.",
                detail={"first_error": err_txt, "second_error": _format_validation_errors(e2)}
            )

class FormattingService:
    @staticmethod
    def generate_doc(user_prompt, llm_client):
        return generate_doc(user_prompt, llm_client)
