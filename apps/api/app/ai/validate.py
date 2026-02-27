import json
from pydantic import ValidationError
from .schema_v1 import AiDocV1

def validate_ai_doc_v1(raw_text: str) -> AiDocV1:
    try:
        # Extract first JSON object from raw_text
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in AI response")

        json_str = raw_text[start:end + 1]
        obj = json.loads(json_str)
    except Exception as e:
        raise ValidationError(
            [{"loc": ("json",), "msg": str(e), "type": "value_error.json"}],
            AiDocV1
        )

    return AiDocV1.model_validate(obj)
