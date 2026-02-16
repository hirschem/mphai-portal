import json
import pytest

from app.ai.validate import validate_ai_doc_v1


def _valid_doc():
    """
    Must match AiDocV1 exactly (extra="forbid") and satisfy:
    - LineItem id format
    - amount math
    - totals_consistency (subtotal/discount)
    """
    line_items = [
        {
            "id": "LI-001",
            "title": "Exterior painting labor",
            "description": "Prep and paint exterior surfaces.",
            "kind": "labor",
            "unit": "lump_sum",
            "quantity": 1,
            "unit_price_cents": 50000,
            "amount_cents": 50000,
        },
        {
            "id": "LI-002",
            "title": "Discount",
            "description": "Courtesy discount",
            "kind": "discount",
            "unit": "each",
            "quantity": 1,
            "unit_price_cents": 5000,
            "amount_cents": -5000,  # MUST be negative and == -q*up
        },
    ]

    subtotal = 50000  # sum(non-discount amount_cents)
    discount = -5000  # sum(discount amount_cents) -> NEGATIVE per your schema
    tax = 0
    total = subtotal + discount + tax
    balance = total

    return {
        "schema_version": "v1",
        "doc_type": "proposal",
        "doc_id": "TEST-001",
        "currency": "USD",
        "locale": "en-US",
        "client": {
            "name": "John Doe",
            "address": {
                "street": "123 Main St",
                "city": "Denver",
                "state": "CO",
                "zip": "80202",
                "country": "USA",
            },
            "email": None,
            "phone": None,
        },
        "project": {
            "title": "Exterior paint",
            "description": "Paint exterior trim and siding.",
        },
        "line_items": line_items,
        "totals": {
            "subtotal_cents": subtotal,
            "discount_cents": discount,
            "tax_cents": tax,
            "total_cents": total,
            "balance_cents": balance,
        },
        "terms": {
            "payment_terms": "Due on receipt",
        },
        "notes": [],
        "assumptions": [],
        "source": {
            "system": "test",
        },
    }


def test_valid_doc_parses():
    raw = json.dumps(_valid_doc())
    doc = validate_ai_doc_v1(raw)
    assert doc.schema_version == "v1"
    assert doc.totals.subtotal_cents == 50000
    assert doc.totals.discount_cents == -5000


def test_rejects_non_json():
    with pytest.raises(Exception):
        validate_ai_doc_v1("not json")


def test_forbids_extra_keys_top_level():
    d = _valid_doc()
    d["extra"] = "nope"
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))


def test_forbids_extra_keys_nested():
    d = _valid_doc()
    d["client"]["company"] = "MPH"  # not allowed in ClientV1
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))


def test_rejects_bad_line_item_id():
    d = _valid_doc()
    d["line_items"][0]["id"] = "ITEM-1"
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))


def test_rejects_amount_math_mismatch():
    d = _valid_doc()
    d["line_items"][0]["amount_cents"] = 123  # should be q*up
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))


def test_rejects_discount_not_negative():
    d = _valid_doc()
    d["line_items"][1]["amount_cents"] = 5000  # must be negative
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))


def test_rejects_totals_subtotal_mismatch():
    d = _valid_doc()
    d["totals"]["subtotal_cents"] = 999
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))


def test_rejects_totals_discount_mismatch():
    d = _valid_doc()
    d["totals"]["discount_cents"] = -999
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))


def test_rejects_money_as_string():
    d = _valid_doc()
    d["line_items"][0]["unit_price_cents"] = "50000"
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))


def test_rejects_note_too_long():
    d = _valid_doc()
    d["notes"] = ["x" * 241]
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))


def test_rejects_assumption_too_long():
    d = _valid_doc()
    d["assumptions"] = ["x" * 241]
    with pytest.raises(Exception):
        validate_ai_doc_v1(json.dumps(d))
