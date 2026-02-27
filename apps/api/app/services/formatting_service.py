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
        # --- ProposalData normalization block ---
        # Client name mapping
        def _get_nested(dct, *keys):
            for k in keys:
                if isinstance(dct, dict) and k in dct and dct[k]:
                    return dct[k]
            return None

        if not data.get("client_name"):
            data["client_name"] = (
                data.get("customer_name")
                or data.get("name")
                or data.get("bill_to_name")
                or _get_nested(data.get("client", {}), "name")
                or _get_nested(data.get("bill_to", {}), "name")
            )

        # Project address mapping (keep existing logic, add nested)
        if data.get("client_address") and not data.get("project_address"):
            data["project_address"] = data["client_address"]
        if data.get("address") and not data.get("project_address"):
            data["project_address"] = data["address"]
        # Nested: client["address"], bill_to["address"]
        if not data.get("project_address"):
            nested_addr = (
                _get_nested(data.get("client", {}), "address")
                or _get_nested(data.get("bill_to", {}), "address")
            )
            if nested_addr:
                data["project_address"] = nested_addr
        if data.get("project_address") and not data.get("client_address"):
            data["client_address"] = data["project_address"]

        # Line items mapping + cents->dollars
        if isinstance(data.get("line_items"), list):
            for item in data["line_items"]:
                # amount_cents -> amount
                if "amount_cents" in item and "amount" not in item:
                    try:
                        item["amount"] = float(item["amount_cents"]) / 100.0
                    except Exception:
                        pass
                # description mapping
                if not item.get("description"):
                    desc = item.get("item") or item.get("name")
                    if desc:
                        item["description"] = desc

        # Total cents->dollars
        if not data.get("total") and data.get("total_cents"):
            try:
                data["total"] = float(data["total_cents"]) / 100.0
            except Exception:
                pass

        # --- Fallback extraction from original input text (OCR/professional_text) ---
        # Use the first OCR input as the source text
        ocr_text = ocr[0] if ocr and isinstance(ocr[0], str) else ""
        lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]

        # Fallback client_name extraction
        if not data.get("client_name") and lines:
            for line in lines:
                for prefix in ("Client:", "Bill To:", "Customer:"):
                    if line.startswith(prefix):
                        val = line[len(prefix):].strip()
                        if val:
                            data["client_name"] = val
                            break
                if data.get("client_name"):
                    break

        # Fallback project_address extraction
        if not data.get("project_address") and lines:
            import re
            address_pattern = re.compile(r"\b\d+\b.*\b(St|Ave|Rd|Dr|Way|Ln|Blvd|Ct)\b", re.IGNORECASE)
            for line in lines[:10]:  # Only check first 10 lines
                if address_pattern.search(line):
                    data["project_address"] = line
                    break

        # --- End ProposalData normalization block ---
        return data

    async def rewrite_structured_proposal(self, ocr_texts: list[str]) -> str:
        filtered = [t for t in ocr_texts if t.strip()]
        combined_text = "\n\n".join(filtered)
        prompt = (
            "You are turning handwritten notes into a clean invoice/proposal scope list.\n"
            "Hard rules:\n"
            "- Plain text only. No markdown.\n"
            "- Output each line as plain text. Do NOT include bullets (no '•', no '-', no numbering).\n"
            "- Do NOT include client name, address, or any header information in the output body.\n"
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
            "- Produce a list of line items.\n"
            "- Each line item must include a description. A price is optional.\n"
            "- If priced:  'Description — $1,234.56'\n"
            "- If unpriced: 'Description'\n"
            "- Do not invent prices. Do not assign the final total to a random line item.\n"
            "- If the notes show an amount off to the right (like '650 00'), treat it as $650.00.\n"
            "- If an amount has no '$' or no decimals, normalize it to dollars with two decimals.\n"
            "- If you cannot confidently find a price for a scope line, KEEP the line but output it with NO price.\n"
            "- Stand-alone numbers (e.g. 192, 12600) should only be used as Total if clearly the final total; otherwise ignore them.\n"
            "- Do NOT merge separate scope lines into one combined line, even if they are adjacent.\n"
            "- If two separate amounts appear (e.g., 175 and 75), keep them as separate line items.\n"
            "- If a final handwritten total exists (e.g., 12,600), use ONLY that as the Total.\n"
            "- Do NOT recompute or sum line items.\n"
            "- Never add line items together to create new totals.\n"
            "Voice:\n"
            "Older, friendly, experienced construction owner: plain, direct, practical wording."
        )
        full_prompt = (
            prompt
            + "\n\n=== BEGIN HANDWRITTEN NOTES ===\n"
            + combined_text
            + "\n=== END HANDWRITTEN NOTES ===\n"
        )
        async def _do_call():
            model_name = "gpt-4o"
            temperature_value = 0.0
            max_tokens_value = 4000
            system_prompt_string = None
            user_prompt_string = full_prompt
            logger.info("=== REWRITE_MODEL === %s", model_name)
            logger.info("=== REWRITE_TEMPERATURE === %s", temperature_value)
            logger.info("=== REWRITE_MAX_TOKENS === %s", max_tokens_value)
            logger.info("=== REWRITE_SYSTEM_PROMPT_START ===\n%s\n=== REWRITE_SYSTEM_PROMPT_END ===", system_prompt_string or "None")
            # Log prompt length
            logger.info("=== REWRITE_USER_PROMPT_LEN === %s", len(user_prompt_string))
            # Safe truncation for logging
            max_log = 8000
            fp = user_prompt_string
            if len(fp) > max_log:
                fp_log = fp[:6000] + "\n...<TRUNCATED>...\n" + fp[-1500:]
            else:
                fp_log = fp
            logger.info("=== REWRITE_USER_PROMPT_START ===\n%s\n=== REWRITE_USER_PROMPT_END ===", fp_log)
            return await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=max_tokens_value,
                temperature=temperature_value
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
