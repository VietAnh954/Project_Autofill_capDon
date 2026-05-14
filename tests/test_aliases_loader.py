"""Unit tests cho aliases_loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from auto_fill.mapper.aliases_loader import load_aliases


class TestLoadAliasesDefault:
    def test_returns_dict(self) -> None:
        result = load_aliases()
        assert isinstance(result, dict)

    def test_insured_name_has_aliases(self) -> None:
        result = load_aliases()
        assert "insured_name" in result
        assert len(result["insured_name"]) >= 3

    def test_insured_id_number_has_aliases(self) -> None:
        result = load_aliases()
        assert "insured_id_number" in result
        assert "cccd" in result["insured_id_number"]

    def test_premium_has_aliases(self) -> None:
        result = load_aliases()
        assert "premium" in result
        assert any("phí" in a for a in result["premium"])

    def test_all_values_are_lists_of_strings(self) -> None:
        result = load_aliases()
        for canonical, alias_list in result.items():
            assert isinstance(alias_list, list), f"{canonical} must be list"
            for a in alias_list:
                assert isinstance(a, str), f"alias {a!r} in {canonical} must be str"

    def test_travel_fields_present(self) -> None:
        result = load_aliases()
        for field in ("trip_start", "trip_end", "destination"):
            assert field in result, f"{field} missing from aliases"

    def test_vehicle_fields_present(self) -> None:
        result = load_aliases()
        for field in ("plate_number", "frame_number", "engine_number"):
            assert field in result, f"{field} missing from aliases"

    def test_student_fields_present(self) -> None:
        result = load_aliases()
        for field in ("school", "class_name"):
            assert field in result, f"{field} missing from aliases"

    def test_health_fields_present(self) -> None:
        result = load_aliases()
        for field in ("outpatient", "dental", "maternity"):
            assert field in result, f"{field} missing from aliases"

    def test_no_empty_alias_list(self) -> None:
        result = load_aliases()
        for canonical, alias_list in result.items():
            assert len(alias_list) > 0, f"{canonical} has empty alias list"


class TestLoadAliasesCustomPath:
    def test_loads_custom_yaml(self, tmp_path: Path) -> None:
        custom = tmp_path / "custom_aliases.yaml"
        custom.write_text(
            yaml.dump({"insured_name": ["full name", "name"]}),
            encoding="utf-8",
        )
        result = load_aliases.__wrapped__(custom)
        assert result == {"insured_name": ["full name", "name"]}

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_aliases.__wrapped__(tmp_path / "nonexistent.yaml")

    def test_invalid_yaml_structure_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ValueError):
            load_aliases.__wrapped__(bad)
