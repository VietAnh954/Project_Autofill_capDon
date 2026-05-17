"""self_buyer — copy fields between buyer and insured when buyer_relation == 'Bản thân'.

Pattern 1 (self-insured): BMBH IS the NĐBH.
- If buyer fields empty but insured fields present → copy insured_* → buyer_*
- If insured fields empty but buyer fields present → copy buyer_* → insured_*
"""

from __future__ import annotations

from typing import Any

_SELF_RELATION_VALUES = frozenset({"bản thân", "ban than", "self", "chinh minh", "chính mình"})

_PAIRED: tuple[tuple[str, str], ...] = (
    ("insured_name", "buyer_name"),
    ("insured_id_number", "buyer_id_number"),
    ("insured_dob", "buyer_dob"),
    ("insured_phone", "buyer_phone"),
    ("insured_email", "buyer_email"),
    ("insured_address", "buyer_address"),
    ("insured_gender", "buyer_gender"),
)


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    try:
        import math

        if isinstance(v, float) and math.isnan(v):
            return True
    except Exception:
        pass
    return str(v).strip().lower() in {"", "nan", "nat", "na", "n/a", "none"}


def normalize_self_buyer(record: dict[str, Any]) -> dict[str, Any]:
    """Fill missing buyer or insured fields when buyer_relation == 'Bản thân'.

    Returns a new dict; does not mutate the input.
    """
    relation = record.get("buyer_relation", "")
    if _is_empty(relation):
        return record
    if str(relation).strip().lower() not in _SELF_RELATION_VALUES:
        return record

    result = dict(record)
    for insured_key, buyer_key in _PAIRED:
        ins_val = result.get(insured_key)
        buy_val = result.get(buyer_key)
        ins_empty = _is_empty(ins_val)
        buy_empty = _is_empty(buy_val)

        if not ins_empty and buy_empty:
            result[buyer_key] = ins_val
        elif not buy_empty and ins_empty:
            result[insured_key] = buy_val

    return result
