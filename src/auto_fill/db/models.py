"""SQLAlchemy ORM models cho 6 sheet bảo hiểm chính.

Mỗi sheet → 1 table.  Common columns mixin: id, source_email_id,
source_attachment, created_at.  Dedup constraints theo DATABASE §4.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    DATE,
    REAL,
    TEXT,
    TIMESTAMP,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class _AuditMixin:
    source_email_id: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    source_attachment: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )


class TravelInsurance(_AuditMixin, Base):
    """Du lịch — dedup (insured_id_number, trip_start, destination)."""

    __tablename__ = "travel_insurance"
    __table_args__ = (UniqueConstraint("insured_id_number", "trip_start", "destination"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    issued_date: Mapped[date] = mapped_column(DATE, nullable=False)
    insured_name: Mapped[str] = mapped_column(TEXT, nullable=False)
    insured_dob: Mapped[date | None] = mapped_column(DATE, nullable=True)
    insured_id_number: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    payment_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    trip_start: Mapped[date] = mapped_column(DATE, nullable=False)
    trip_end: Mapped[date] = mapped_column(DATE, nullable=False)
    destination: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    scope: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    plan: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    premium: Mapped[float | None] = mapped_column(REAL, nullable=True)
    buyer_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)


class AutoInsurance(_AuditMixin, Base):
    """Bao hiem oto — dedup (plate_number, issued_date)."""

    __tablename__ = "auto_insurance"
    __table_args__ = (UniqueConstraint("plate_number", "issued_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    issued_date: Mapped[date] = mapped_column(DATE, nullable=False)
    insured_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    phone: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    email: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    address: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    plate_number: Mapped[str] = mapped_column(TEXT, nullable=False)
    frame_number: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    engine_number: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    payload: Mapped[float | None] = mapped_column(REAL, nullable=True)
    seats: Mapped[int | None] = mapped_column(nullable=True)
    vehicle_type: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    brand: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    vehicle_value: Mapped[float | None] = mapped_column(REAL, nullable=True)
    purpose: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    premium: Mapped[float | None] = mapped_column(REAL, nullable=True)


class MotorbikeInsurance(_AuditMixin, Base):
    """Xe may — dedup (plate_number, issued_date)."""

    __tablename__ = "motorbike_insurance"
    __table_args__ = (UniqueConstraint("plate_number", "issued_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    issued_date: Mapped[date] = mapped_column(DATE, nullable=False)
    plate_number: Mapped[str] = mapped_column(TEXT, nullable=False)
    frame_number: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    engine_number: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    customer_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    premium_tnds: Mapped[float | None] = mapped_column(REAL, nullable=True)
    premium_accident: Mapped[float | None] = mapped_column(REAL, nullable=True)
    years: Mapped[int | None] = mapped_column(nullable=True)
    total_premium: Mapped[float | None] = mapped_column(REAL, nullable=True)
    start_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    end_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    vehicle_type: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    brand: Mapped[str | None] = mapped_column(TEXT, nullable=True)


class HealthInsurance(_AuditMixin, Base):
    """Suc khoe — dedup (insured_id_number, effective_from)."""

    __tablename__ = "health_insurance"
    __table_args__ = (UniqueConstraint("insured_id_number", "effective_from"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    issued_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    insured_name: Mapped[str] = mapped_column(TEXT, nullable=False)
    insured_dob: Mapped[date | None] = mapped_column(DATE, nullable=True)
    insured_id_number: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(DATE, nullable=True)
    outpatient: Mapped[float | None] = mapped_column(REAL, nullable=True)
    dental: Mapped[float | None] = mapped_column(REAL, nullable=True)
    maternity: Mapped[float | None] = mapped_column(REAL, nullable=True)
    premium: Mapped[float | None] = mapped_column(REAL, nullable=True)
    buyer_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    buyer_dob: Mapped[date | None] = mapped_column(DATE, nullable=True)
    buyer_id_number: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    buyer_relation: Mapped[str | None] = mapped_column(TEXT, nullable=True)


class BhytBhxhInsurance(_AuditMixin, Base):
    """BHYTBHXH — dedup (insured_id_number, effective_from)."""

    __tablename__ = "bhyt_bhxh_insurance"
    __table_args__ = (UniqueConstraint("insured_id_number", "effective_from"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    issued_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    insured_name: Mapped[str] = mapped_column(TEXT, nullable=False)
    insured_id_number: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(DATE, nullable=True)
    buyer_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    buyer_dob: Mapped[date | None] = mapped_column(DATE, nullable=True)
    buyer_relation: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    premium: Mapped[float | None] = mapped_column(REAL, nullable=True)


class StudentInsurance(_AuditMixin, Base):
    """HSSV — dedup (insured_id_number, school, issued_date)."""

    __tablename__ = "student_insurance"
    __table_args__ = (UniqueConstraint("insured_id_number", "school", "issued_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    issued_date: Mapped[date] = mapped_column(DATE, nullable=False)
    insured_name: Mapped[str] = mapped_column(TEXT, nullable=False)
    insured_dob: Mapped[date | None] = mapped_column(DATE, nullable=True)
    insured_id_number: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    school: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    class_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(DATE, nullable=True)
    premium: Mapped[float | None] = mapped_column(REAL, nullable=True)
    buyer_name: Mapped[str | None] = mapped_column(TEXT, nullable=True)


ALL_MODELS = (
    TravelInsurance,
    AutoInsurance,
    MotorbikeInsurance,
    HealthInsurance,
    BhytBhxhInsurance,
    StudentInsurance,
)
