from pydantic import BaseModel, Field, ConfigDict, ValidationError, field_validator, StrictInt
from typing import Optional, List, Literal
import re

class AddressV1(BaseModel):
    street: Optional[str] = Field(None, max_length=80)
    city: Optional[str] = Field(None, max_length=80)
    state: Optional[str] = Field(None, max_length=80)
    zip: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=40)
    model_config = ConfigDict(extra="forbid")

class ClientV1(BaseModel):
    name: str = Field(..., max_length=80)
    address: Optional[AddressV1] = None
    email: Optional[str] = Field(None, max_length=80)
    phone: Optional[str] = Field(None, max_length=40)
    model_config = ConfigDict(extra="forbid")

class ProjectV1(BaseModel):
    title: str = Field(..., max_length=80)
    description: Optional[str] = Field(None, max_length=240)
    model_config = ConfigDict(extra="forbid")

class LineItemV1(BaseModel):
    id: str
    title: str = Field(..., max_length=80)
    description: Optional[str] = Field(None, max_length=240)
    kind: Literal["service", "material", "labor", "fee", "discount"]
    unit: Literal["each", "hour", "sqft", "linear_ft", "lump_sum"]
    quantity: StrictInt = Field(..., ge=1)
    unit_price_cents: StrictInt = Field(..., ge=0)
    amount_cents: StrictInt
    model_config = ConfigDict(extra="forbid")

    @field_validator("id")
    def id_format(cls, v):
        if not re.match(r"^LI-\d{3}$", v):
            raise ValueError("Line item id must match LI-001, LI-002, etc.")
        return v

    @field_validator("amount_cents")
    def amount_math(cls, v, info):
        values = info.data
        q = values.get("quantity")
        up = values.get("unit_price_cents")
        kind = values.get("kind")
        if q is not None and up is not None:
            expected = q * up
            if kind == "discount":
                if v >= 0:
                    raise ValueError("Discount amount_cents must be negative.")
                if v != -expected:
                    raise ValueError("Discount amount_cents must equal -quantity*unit_price_cents.")
            else:
                if v != expected:
                    raise ValueError("amount_cents must equal quantity*unit_price_cents.")
        return v

class TotalsV1(BaseModel):
    subtotal_cents: StrictInt
    discount_cents: StrictInt
    tax_cents: StrictInt
    total_cents: StrictInt
    balance_cents: StrictInt
    model_config = ConfigDict(extra="forbid")

class TermsV1(BaseModel):
    payment_terms: Optional[str] = Field(None, max_length=240)
    model_config = ConfigDict(extra="forbid")

class SourceV1(BaseModel):
    system: Optional[str] = Field(None, max_length=80)
    model_config = ConfigDict(extra="forbid")

class AiDocV1(BaseModel):
    schema_version: Literal["v1"]
    doc_type: Literal["proposal", "invoice"]
    doc_id: str
    currency: Literal["USD"]
    locale: Literal["en-US"]
    client: ClientV1
    project: ProjectV1
    line_items: List[LineItemV1] = Field(..., min_length=1, max_length=12)
    totals: TotalsV1
    terms: TermsV1
    notes: List[str] = Field(default_factory=list, max_length=12)
    assumptions: List[str] = Field(default_factory=list, max_length=12)
    source: SourceV1
    model_config = ConfigDict(extra="forbid")

    @field_validator("notes", mode="before")
    def note_length(cls, v):
        if v is not None:
            for note in v:
                if len(note) > 240:
                    raise ValueError("Note too long")
        return v

    @field_validator("assumptions", mode="before")
    def assumption_length(cls, v):
        if v is not None:
            for assumption in v:
                if len(assumption) > 240:
                    raise ValueError("Assumption too long")
        return v

    @field_validator("totals")
    def totals_consistency(cls, v, info):
        values = info.data
        items = values.get("line_items", [])
        subtotal = sum(i.amount_cents for i in items if i.kind != "discount")
        discount = sum(i.amount_cents for i in items if i.kind == "discount")
        if v.subtotal_cents != subtotal:
            raise ValueError("Subtotal mismatch")
        if v.discount_cents != discount:
            raise ValueError("Discount mismatch")
        # tax, total, balance can be recomputed as needed
        return v
