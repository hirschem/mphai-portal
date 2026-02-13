
from openai import AsyncOpenAI
from app.models.config import get_settings
from app.models.schemas import ProposalData
import json
import logging
logger = logging.getLogger("api.formatting_service")

settings = get_settings()


class FormattingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def rewrite_professional(self, raw_text: str) -> str:
        """Rewrite transcribed text in professional construction proposal language"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an experienced residential construction business owner writing professional proposals. "
                            "Your goal is to transform handwritten notes into polished, professional proposals while:\n\n"
                            "1. PRESERVING ALL INFORMATION - Include every detail, measurement, material, cost, and timeline mentioned\n"
                            "2. Using clear, professional language that homeowners can easily understand\n"
                            "3. Maintaining the confident, trustworthy tone of a successful contractor\n"
                            "4. Organizing information logically (scope, materials, pricing, timeline, terms)\n"
                            "5. Keeping technical terms simple and approachable\n\n"
                            "DO NOT:\n"
                            "- Remove or summarize any details from the original\n"
                            "- Use overly complex or corporate language\n"
                            "- Add information that wasn't in the original\n\n"
                            "Write as if you're personally explaining the project to a valued client."
                        )
                    },
                    {
                        "role": "user",
                        "content": raw_text
                    }
                ],
                max_tokens=2500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"[rewrite_professional] error: {e}", exc_info=True)
            raise
    
    async def structure_proposal(self, professional_text: str, document_type: str = "proposal") -> ProposalData:
        """Extract structured data from professional proposal/invoice text"""
        try:
            # Prompt changes slightly for invoice vs proposal
            if document_type == "invoice":
                system_prompt = (
                    "Extract structured data from this construction invoice. "
                    "Return a JSON object with these fields:\n"
                    "- client_name (string or null)\n"
                    "- project_address (string or null)\n"
                    "- invoice_number (string or null)\n"
                    "- due_date (string or null)\n"
                    "- line_items (array of objects with description (string), quantity (number or null), rate (number or null), amount (number or null), or null)\n"
                    "- subtotal (number or null)\n"
                    "- tax (number or null)\n"
                    "- total (number or null)\n"
                    "- payment_terms (string or null)\n"
                    "- notes (string or null)\n"
                    "IMPORTANT RULES:\n"
                    "1. For numeric fields, use null if not present - NEVER use strings or placeholders\n"
                    "2. If a line_item has no description, omit it entirely\n"
                    "3. Add a document_type field set to 'invoice'\n"
                )
            else:
                system_prompt = (
                    "Extract structured data from this construction proposal. "
                    "Return a JSON object with these fields:\n"
                    "- client_name (string or null)\n"
                    "- project_address (string or null)\n"
                    "- scope_of_work (array of strings or null)\n"
                    "- line_items (array of objects with description (string), quantity (number or null), rate (number or null), amount (number or null), or null)\n"
                    "- subtotal (number or null)\n"
                    "- tax (number or null)\n"
                    "- total (number or null)\n"
                    "- payment_terms (null - always set to null, not used)\n"
                    "- timeline (STRING or null - ONLY if a timeline/schedule is explicitly mentioned in the text. If no timeline is mentioned, use null)\n"
                    "- notes (string or null - Include any PS notes, downpayment information, deposits, or side notes here)\n"
                    "IMPORTANT RULES:\n"
                    "1. For numeric fields, use null if not present - NEVER use strings or placeholders\n"
                    "2. timeline MUST be plain string, NOT object or array, and ONLY if explicitly mentioned\n"
                    "3. payment_terms should always be null (not used in output)\n"
                    "4. notes should capture PS, downpayment, deposits, and any side comments\n"
                    "5. If a line_item has no description, omit it entirely\n"
                    "6. Add a document_type field set to 'proposal'\n"
                )
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": professional_text
                    }
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            data["document_type"] = document_type
            # Clean up any string placeholders or wrong types
            for field in ['subtotal', 'tax', 'total']:
                if field in data and (isinstance(data[field], str) or data[field] == {}):
                    data[field] = None
            # payment_terms and timeline should be strings, not dicts
            for field in ['payment_terms', 'timeline', 'notes']:
                if field in data:
                    if isinstance(data[field], dict):
                        data[field] = str(data[field])
                    elif not data[field]:
                        data[field] = None
            if 'line_items' in data and data['line_items']:
                for item in data['line_items']:
                    for field in ['quantity', 'rate', 'amount']:
                        if field in item and (isinstance(item[field], str) or item[field] == {}):
                            item[field] = None
                    if 'description' in item:
                        if not item['description'] or (isinstance(item['description'], str) and item['description'].strip() == ''):
                            item['description'] = None
                data['line_items'] = [item for item in data['line_items'] if item.get('description')]
            return ProposalData(**data)
        except Exception as e:
            logger.error(f"[structure_proposal] error: {e}", exc_info=True)
            raise
