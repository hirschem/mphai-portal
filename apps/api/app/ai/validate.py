import json
from pydantic import ValidationError
from .schema_v1 import AiDocV1

def validate_ai_doc_v1(raw_text: str) -> AiDocV1:
    try:
        obj = json.loads(raw_text)
    except Exception as e:
        raise ValidationError([{"loc": ("json",), "msg": str(e), "type": "value_error.json"}], AiDocV1)
    return AiDocV1.model_validate(obj)
