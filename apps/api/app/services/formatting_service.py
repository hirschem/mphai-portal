from app.services.openai_guard import call_openai_with_retry


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

async def generate_doc(user_prompt, llm_client):
    base_prompt = PROMPT_PREFIX + user_prompt

    async def call_model(prompt: str) -> str:
        async def _do_call():
            return await llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                top_p=1.0,
                presence_penalty=0.0,
                frequency_penalty=0.0,
                max_tokens=2000
            )
        response = await call_openai_with_retry(_do_call, max_attempts=3, per_attempt_timeout_s=20.0)
        return response.choices[0].message.content

    import asyncio
    raw1 = await call_model(base_prompt)
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
        raw2 = await call_model(retry_prompt)
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

    async def rewrite_structured_proposal(self, ocr_texts: list[str]) -> str:
        filtered = [t for t in ocr_texts if t.strip()]
        combined_text = "\n\n".join(filtered)
        prompt = (
            "Rewrite the following raw construction notes into a clean, professional proposal using the exact structure below.\n\n"
            "RULES:\n\n"
            "Output plain text only.\n"
            "No markdown.\n"
            "No asterisks.\n"
            "No code fences.\n"
            "Do not repeat headings.\n"
            "Do not invent scope items.\n"
            "Preserve all scope details exactly as written.\n"
            "Clean grammar and wording but do not change meaning.\n"
            "Tone must be professional, confident, and direct.\n"
            "No filler language.\n\n"
            "COST RULES:\n\n"
            "If individual line item costs are provided but no subtotal is written, calculate and include Subtotal.\n"
            "If a cost range is written (example: 5000-6000), format it as:\n"
            "Estimated Cost Range: $5,000.00 – $6,000.00\n"
            "If overhead percentage is written (example: 20%), calculate it based on subtotal and include it.\n"
            "If a grand total is not written but can be calculated, calculate and include it.\n"
            "If totals are already written, preserve them exactly as provided.\n\n"
            "FORMAT:\n\n"
            "Intro paragraph (1–2 sentences maximum)\n\n"
            "Scope of Work\n\n"
            "Section Title\n"
            "• Bullet\n"
            "• Bullet\n"
            "Cost: $X,XXX.XX\n\n"
            "Section Title\n"
            "• Bullet\n"
            "• Bullet\n"
            "Cost: $X,XXX.XX\n\n"
            "(Continue as needed)\n\n"
            "Subtotal: $X,XXX.XX\n"
            "Overhead (if applicable): $X,XXX.XX\n"
            "Grand Total: $X,XXX.XX\n\n"
            "Sincerely,\n"
            "Mark Hirsch\n\n"
            "RAW NOTES:\n{combined OCR text}"
        )
        full_prompt = prompt.replace("{combined OCR text}", combined_text)
        async def _do_call():
            return await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=2000,
                temperature=0.0
            )
        response = await call_openai_with_retry(_do_call, max_attempts=3, per_attempt_timeout_s=20.0)
        return response.choices[0].message.content.strip()
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    @staticmethod
    async def generate_doc(user_prompt, llm_client):
        return await generate_doc(user_prompt, llm_client)

    async def rewrite_professional(self, user_prompt: str) -> str:
        return await self.generate_doc(user_prompt, self.client)
