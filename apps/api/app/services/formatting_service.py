CONTRACTOR_PROMPT_PREFIX = (
    "You MUST return exactly one JSON object matching the ContractorDocV1 schema.\n"
    "Do NOT return markdown. Do NOT wrap in code fences. Do NOT add any extra text.\n"
    "No extra keys allowed. No explanations.\n"
    "The top-level object MUST contain ONLY these keys: schema_version, client_name, client_address, line_items, total_cents.\n"
    "Do NOT nest under another object. Do NOT add extra keys. Do NOT omit required keys.\n"
    "\n"
    "Example ContractorDocV1 JSON:\n"
    "{\n"
    "  \"schema_version\": \"v1\",\n"
    "  \"client_name\": \"Jane Smith\",\n"
    "  \"client_address\": \"123 Main St, Denver, CO\",\n"
    "  \"line_items\": [\n"
    "    {\n"
    "      \"description\": \"Install carpet\",\n"
    "      \"amount_cents\": 120000\n"
    "    },\n"
    "    {\n"
    "      \"description\": \"Remove old carpet\",\n"
    "      \"amount_cents\": 20000\n"
    "    }\n"
    "  ],\n"
    "  \"total_cents\": 140000\n"
    "}\n"
)
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
    "You MUST return exactly one JSON object that matches the AiDocV1 schema.\n"
    "The top-level object MUST contain ONLY these keys:\n"
    "\"schema_version\"\n"
    "\"currency\"\n"
    "\"locale\"\n"
    "\"client\"\n"
    "\"project\"\n"
    "\"line_items\"\n"
    "\"totals\"\n"
    "\"source\" (if applicable per schema)\n"
    "Do NOT create an 'invoice' object.\n"
    "Do NOT nest all fields under another object.\n"
    "Do NOT add extra keys.\n"
    "Do NOT omit required keys.\n"
    "\n"
    "Example of valid top-level structure:\n"
    "{\n"
    "  \"schema_version\": \"1.0\",\n"
    "  \"currency\": \"USD\",\n"
    "  \"locale\": \"en-US\",\n"
    "  \"client\": { ... },\n"
    "  \"project\": { ... },\n"
    "  \"line_items\": [\n"
    "    {\n"
    "      \"description\": \"Demo carpet\",\n"
    "      \"quantity\": 1,\n"
    "      \"unit_price_cents\": 100000,\n"
    "      \"total_cents\": 100000\n"
    "    }\n"
    "  ],\n"
    "  \"totals\": {\n"
    "    \"subtotal_cents\": 100000,\n"
    "    \"total_cents\": 100000\n"
    "  }\n"
    "}\n"
    "\n"
    "Return ONLY JSON.\n"
    "No markdown.\n"
    "No explanations.\n"
    "No extra wrapping objects.\n"
)

async def generate_doc(user_prompt, llm_client):
    from app.ai.schema_contractor_v1 import validate_contractor_doc_v1
    contractor_prompt = CONTRACTOR_PROMPT_PREFIX + user_prompt
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

    # Try ContractorDocV1 first
    raw_contractor = await call_model(contractor_prompt)
    try:
        contractor_doc = validate_contractor_doc_v1(raw_contractor)
        return contractor_doc
    except Exception as contractor_exc:
        logger.info("CONTRACTOR VALIDATION FAILED: %s", str(contractor_exc))
        logger.info("CONTRACTOR RAW RESPONSE (truncated): %s", raw_contractor[:2000])
        # Fallback to AiDocV1 logic unchanged
        base_prompt = PROMPT_PREFIX + user_prompt
        raw1 = await call_model(base_prompt)
        try:
            doc = validate_ai_doc_v1(raw1)
            return doc
        except Exception as e1:
            logger.error("AIDOC VALIDATION FAILED: %s", str(e1))
            logger.error("AIDOC RAW RESPONSE (truncated): %s", raw1[:2000])
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
    async def structure_proposal(self, *args, **kwargs):
        """Backwards-compatible alias for proposals route. Minimal wrapper. Returns ProposalData-compatible dict."""
        import json
        kwargs.pop("document_type", None)
        ocr = []
        if args:
            first = args[0]
            if isinstance(first, str):
                ocr = [first]
            elif isinstance(first, (list, tuple)):
                ocr = list(first)
            else:
                ocr = [str(first)]
        try:
            try:
                result = await self.rewrite_structured_proposal(ocr, **kwargs)
            except TypeError:
                result = await self.rewrite_structured_proposal(ocr)
            data = json.loads(result)
        except Exception as e:
            raise StandardizedAIError(
                "AI_SCHEMA_VALIDATION_FAILED",
                f"Failed to parse proposal JSON: {e}"
            )
        if not isinstance(data, dict):
            raise StandardizedAIError(
                "AI_SCHEMA_VALIDATION_FAILED",
                "Proposal output was not a JSON object."
            )
        # Normalization: if client_address exists and project_address does not, copy client_address
        if "client_address" in data and "project_address" not in data:
            data["project_address"] = data["client_address"]
        return data

    async def rewrite_structured_proposal(self, ocr_texts: list[str]) -> str:
        filtered = [t for t in ocr_texts if t.strip()]
        combined_text = "\n\n".join(filtered)
        prompt = (
            "You are turning handwritten notes into a clean invoice/proposal scope list.\n"
            "Hard rules:\n"
            "- Plain text only. No markdown, no bullets like '*' (use '•' only if needed).\n"
            "- Do NOT include printed/letterhead content (company slogans, phone, email, address).\n"
            "- Do NOT include 'Session:' or 'Page:' lines.\n"
            "- Do NOT output stand-alone numbers or an 'Amount' section.\n"
            "Pricing Rules:\n"
            "- If the handwritten notes contain no dollar amounts anywhere, do NOT invent pricing.\n"
            "- In that case, output the scope only and include a final line:\n"
            "  'Total: TO BE DETERMINED'\n"
            "- If a line shows a price range (example: 5000-7000 or 5,000 – 7,000):\n"
            "  Format it exactly as:\n"
            "  'Description — $5,000.00 – $7,000.00'\n"
            "- If any line uses a range price, the final total must also show a range:\n"
            "  'Total: $X,XXX.XX – $Y,YYY.YY'\n"
            "- Always normalize money with '$' and two decimals.\n"
            "- Never output stand-alone number columns.\n"
            "Output format:\n"
            "- Produce a list of charge items.\n"
            "- EACH charge item must include BOTH a description and a price.\n"
            "- Format each priced line exactly like:\n"
            "  'Description — $1,234.56'\n"
            "- If the notes show an amount off to the right (like '650 00'), treat it as $650.00.\n"
            "- If an amount has no '$' or no decimals, normalize it to dollars with two decimals.\n"
            "- If you cannot confidently pair a description with a price, omit it (do not guess).\n"
            "Voice:\n"
            "Older, friendly, experienced construction owner: plain, direct, practical wording."
        )
        full_prompt = prompt + "\n\n" + combined_text
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
        # Restore original behavior: return only clean professional prose text
        # This should not return JSON or dict, only formatted text
        return await self.rewrite_structured_proposal([user_prompt])
