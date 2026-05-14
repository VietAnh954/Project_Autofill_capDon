"""Unit tests cho Classifier."""

from __future__ import annotations

import pytest

from auto_fill.mapper.classifier import classify
from auto_fill.utils.errors import ClassifierError


class TestClassifyBySender:
    def test_sender_hint_overrides_subject(self) -> None:
        hints = {"daily@pti.com.vn": "travel"}
        result = classify(
            subject="Bao cao thang 5",  # no keyword match
            sender_email="daily@pti.com.vn",
            sender_hints=hints,
        )
        assert result.alias == "travel"

    def test_sender_case_insensitive(self) -> None:
        hints = {"daily@pti.com.vn": "travel"}
        result = classify("x", "DAILY@PTI.COM.VN", sender_hints=hints)
        assert result.alias == "travel"

    def test_unknown_sender_falls_through_to_subject(self) -> None:
        hints = {"other@pti.com.vn": "health"}
        result = classify("Du lich Nhat Ban", "any@x.com", sender_hints=hints)
        assert result.alias == "travel"


class TestClassifyBySubject:
    @pytest.mark.parametrize(
        "subject, expected_alias",
        [
            ("Phieu cap don du lich", "travel"),
            ("Travel insurance", "travel"),
            ("Du lich Thai Lan", "travel"),
            ("Suc khoe ca nhan", "health"),
            ("health insurance 2026", "health"),
            ("sk thang 5", "health"),
            ("Bao hiem oto hang nam", "auto"),
            ("OTO Toyota Camry", "auto"),
            ("Car insurance", "auto"),
            ("Cap don xe may", "motorbike"),
            ("TNDS XM thang 5", "motorbike"),
            ("BHYT 2026", "bhyt_bhxh"),
            ("BHXH thang 5", "bhyt_bhxh"),
            ("HSSV nam hoc 2026", "student"),
            ("Hoc sinh tieu hoc", "student"),
            ("Sinh vien dai hoc", "student"),
        ],
    )
    def test_subject_keywords(self, subject: str, expected_alias: str) -> None:
        result = classify(subject, "sale@pti.com.vn")
        assert result.alias == expected_alias

    def test_no_match_raises(self) -> None:
        with pytest.raises(ClassifierError):
            classify("Bao cao thang 5", "unknown@x.com")


class TestClassifyByColumns:
    def test_travel_columns_classify_as_travel(self) -> None:
        result = classify(
            "Phieu cap",
            "sale@x.com",
            df_columns=["insured_name", "trip_start", "trip_end", "destination"],
        )
        assert result.alias == "travel"

    def test_vehicle_cols_with_seats_classify_as_auto(self) -> None:
        result = classify(
            "Phieu cap",
            "sale@x.com",
            df_columns=["plate_number", "frame_number", "seats"],
        )
        assert result.alias == "auto"

    def test_vehicle_cols_without_seats_classify_as_motorbike(self) -> None:
        result = classify(
            "Phieu cap",
            "sale@x.com",
            df_columns=["plate_number", "frame_number"],
        )
        assert result.alias == "motorbike"

    def test_health_columns_classify_as_health(self) -> None:
        result = classify(
            "Phieu cap",
            "sale@x.com",
            df_columns=["insured_name", "outpatient", "dental"],
        )
        assert result.alias == "health"

    def test_student_columns_classify_as_student(self) -> None:
        result = classify(
            "Phieu cap",
            "sale@x.com",
            df_columns=["insured_name", "school", "class_name"],
        )
        assert result.alias == "student"

    def test_bhyt_columns_classify_as_bhyt_bhxh(self) -> None:
        result = classify(
            "Phieu cap",
            "sale@x.com",
            df_columns=["insured_id_number", "buyer_relation", "buyer_dob", "issued_date"],
        )
        assert result.alias == "bhyt_bhxh"

    def test_single_bhyt_col_does_not_classify(self) -> None:
        with pytest.raises(ClassifierError):
            classify(
                "Khong ro loai",
                "sale@x.com",
                df_columns=["insured_id_number"],
            )


class TestSheetInfoReturned:
    def test_travel_sheet_info_correct(self) -> None:
        result = classify("Du lich", "sale@pti.com.vn")
        assert result.excel_name == "Du lịch"
        assert result.enabled_in_mvp is True

    def test_all_phase2_sheets_enabled(self) -> None:
        for subject, alias, excel_name in [
            ("Suc khoe", "health", "Sức khỏe"),
            ("Bao hiem oto", "auto", "Bao hiem oto"),
            ("Cap don xe may", "motorbike", "Thông tin cấp Bảo hiểm xe máy"),
            ("BHYT 2026", "bhyt_bhxh", "BHYTBHXH"),
            ("HSSV nam hoc", "student", "HSSV"),
        ]:
            result = classify(subject, "sale@pti.com.vn")
            assert result.alias == alias
            assert result.excel_name == excel_name
            assert result.enabled_in_mvp is True

    def test_result_is_frozen_dataclass(self) -> None:
        result = classify("Du lich", "sale@pti.com.vn")
        with pytest.raises((AttributeError, TypeError)):
            result.alias = "x"  # type: ignore[misc]
