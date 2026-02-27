from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import json
from pydantic import ValidationError

class LineItemV1(BaseModel):
    description: str
    amount_cents: Optional[int] = None

class ContractorDocV1(BaseModel):
    schema_version: Literal["v1"] = "v1"
    client_name: Optional[str] = None
    client_address: Optional[str] = None
    line_items: List[LineItemV1]
    total_cents: Optional[int] = None


def validate_contractor_doc_v1(raw_text: str) -> ContractorDocV1:
    try:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found")

        json_str = raw_text[start:end + 1]
        obj = json.loads(json_str)
    except Exception as e:
        raise ValidationError(
            [{"loc": ("json",), "msg": str(e), "type": "value_error.json"}],
            ContractorDocV1
        )

    return ContractorDocV1.model_validate(obj)
