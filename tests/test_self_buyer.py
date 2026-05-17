"""Unit tests for mapper/self_buyer.py."""

from __future__ import annotations

from pathlib import Path

from auto_fill.mapper.self_buyer import normalize_self_buyer


class TestNormalizeSelfBuyer:
    def test_copies_insured_to_buyer_when_buyer_empty(self) -> None:
        record = {
            "insured_name": "Nguyễn Thị A",
            "buyer_name": None,
            "buyer_relation": "Bản thân",
        }
        result = normalize_self_buyer(record)
        assert result["buyer_name"] == "Nguyễn Thị A"

    def test_copies_buyer_to_insured_when_insured_empty(self) -> None:
        record = {
            "buyer_name": "Trần Văn B",
            "insured_name": None,
            "buyer_relation": "Bản thân",
        }
        result = normalize_self_buyer(record)
        assert result["insured_name"] == "Trần Văn B"

    def test_does_not_overwrite_existing_values(self) -> None:
        record = {
            "insured_name": "Alice",
            "buyer_name": "Bob",
            "buyer_relation": "Bản thân",
        }
        result = normalize_self_buyer(record)
        assert result["insured_name"] == "Alice"
        assert result["buyer_name"] == "Bob"

    def test_skips_when_relation_not_self(self) -> None:
        record = {
            "insured_name": "Alice",
            "buyer_name": None,
            "buyer_relation": "Con đẻ",
        }
        result = normalize_self_buyer(record)
        assert result["buyer_name"] is None

    def test_skips_when_relation_empty(self) -> None:
        record = {"insured_name": "Alice", "buyer_name": None, "buyer_relation": None}
        result = normalize_self_buyer(record)
        assert result["buyer_name"] is None

    def test_copies_all_paired_fields(self) -> None:
        record = {
            "insured_name": "Alice",
            "insured_id_number": "123456789012",
            "insured_dob": "1990-01-01",
            "insured_phone": "0901234567",
            "insured_email": "alice@example.com",
            "insured_address": "HCM",
            "insured_gender": "Nữ",
            "buyer_name": None,
            "buyer_id_number": None,
            "buyer_dob": None,
            "buyer_phone": None,
            "buyer_email": None,
            "buyer_address": None,
            "buyer_gender": None,
            "buyer_relation": "Bản thân",
        }
        result = normalize_self_buyer(record)
        assert result["buyer_name"] == "Alice"
        assert result["buyer_id_number"] == "123456789012"
        assert result["buyer_dob"] == "1990-01-01"
        assert result["buyer_phone"] == "0901234567"
        assert result["buyer_email"] == "alice@example.com"
        assert result["buyer_address"] == "HCM"
        assert result["buyer_gender"] == "Nữ"

    def test_treats_nan_float_as_empty(self) -> None:
        record = {
            "insured_name": "Alice",
            "buyer_name": float("nan"),
            "buyer_relation": "Bản thân",
        }
        result = normalize_self_buyer(record)
        assert result["buyer_name"] == "Alice"

    def test_treats_empty_string_as_empty(self) -> None:
        record = {
            "insured_name": "Alice",
            "buyer_name": "",
            "buyer_relation": "Bản thân",
        }
        result = normalize_self_buyer(record)
        assert result["buyer_name"] == "Alice"

    def test_does_not_mutate_input(self) -> None:
        record = {
            "insured_name": "Alice",
            "buyer_name": None,
            "buyer_relation": "Bản thân",
        }
        original = dict(record)
        normalize_self_buyer(record)
        assert record == original

    def test_relation_case_insensitive(self) -> None:
        record = {
            "insured_name": "Alice",
            "buyer_name": None,
            "buyer_relation": "BẢN THÂN",
        }
        result = normalize_self_buyer(record)
        assert result["buyer_name"] == "Alice"

    def test_relation_without_diacritics(self) -> None:
        record = {
            "insured_name": "Alice",
            "buyer_name": None,
            "buyer_relation": "ban than",
        }
        result = normalize_self_buyer(record)
        assert result["buyer_name"] == "Alice"

    def test_no_buyer_relation_key(self) -> None:
        record = {"insured_name": "Alice", "buyer_name": None}
        result = normalize_self_buyer(record)
        assert result["buyer_name"] is None


class TestSelfBuyerAcceptance:
    """8.5 acceptance: sample_suc_khoe.xlsx case 1 (Bản thân) → both name fields equal."""

    SAMPLE_PATH = Path("sample_capdon/sample_suc_khoe.xlsx")

    def test_self_buyer_row_has_both_names(self) -> None:
        from auto_fill.mapper.aliases_loader import load_aliases
        from auto_fill.reader.excel_reader import read_excel

        aliases = load_aliases()
        df = read_excel(self.SAMPLE_PATH, aliases)
        self_rows = (
            df[
                df.get("buyer_relation", df.get("buyer_relation", "")).str.lower().str.strip()
                == "bản thân"
            ]
            if "buyer_relation" in df.columns
            else df.head(0)
        )
        assert len(self_rows) >= 1, "Expected at least 1 'Bản thân' row"
        row = self_rows.iloc[0]
        assert row.get("buyer_name") == row.get(
            "insured_name"
        ), f"buyer_name={row.get('buyer_name')!r} != insured_name={row.get('insured_name')!r}"
