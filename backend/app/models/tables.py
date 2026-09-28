"""SQLAlchemy ORM models for structured IRCC / StatCan / Job Bank data."""
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PrAdmission(Base):
    """IRCC — Permanent resident admissions by province and immigration category (monthly)."""

    __tablename__ = "pr_admissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    province: Mapped[str] = mapped_column(String(64), index=True)
    immigration_category: Mapped[str] = mapped_column(String(128), index=True)
    admissions: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(256), default="IRCC ODP-PR-PT_IMMCAT")

    __table_args__ = (Index("ix_pr_adm_year_prov_cat", "year", "province", "immigration_category"),)


class PrByCitizenship(Base):
    """IRCC — Permanent resident admissions by country of citizenship (monthly)."""

    __tablename__ = "pr_by_citizenship"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str] = mapped_column(String(128), index=True)
    admissions: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(256), default="IRCC ODP-PR-Citz")


class PrByNoc(Base):
    """IRCC — PR admissions by province and NOC (occupation) — economic categories."""

    __tablename__ = "pr_by_noc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    province: Mapped[str] = mapped_column(String(64), index=True)
    noc_code: Mapped[str] = mapped_column(String(8), index=True)
    noc_title: Mapped[str] = mapped_column(String(256))
    admissions: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(256), default="IRCC ODP-PR-PT_NOC4")


class ProcessingTime(Base):
    """IRCC — published processing times by application type."""

    __tablename__ = "processing_times"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_type: Mapped[str] = mapped_column(String(128), index=True)
    country_or_region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    processing_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    as_of_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(256), default="IRCC processing times")


class WageByNoc(Base):
    """StatCan / Job Bank — wages by occupation (NOC) and province."""

    __tablename__ = "wages_by_noc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    noc_code: Mapped[str] = mapped_column(String(8), index=True)
    noc_title: Mapped[str] = mapped_column(String(256), index=True)
    province: Mapped[str] = mapped_column(String(64), index=True)
    wage_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    wage_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    wage_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(256), default="StatCan 14-10-0417 / Job Bank")


class LabourForceStat(Base):
    """StatCan LFS — employment/unemployment by province, monthly (table 14-10-0287)."""

    __tablename__ = "labour_force_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ref_date: Mapped[str] = mapped_column(String(16), index=True)  # YYYY-MM
    province: Mapped[str] = mapped_column(String(64), index=True)
    characteristic: Mapped[str] = mapped_column(String(128), index=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(256), default="StatCan 14-10-0287")


class ImmigrantLabourStat(Base):
    """StatCan — labour force characteristics by immigrant status (table 14-10-0083)."""

    __tablename__ = "immigrant_labour_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ref_date: Mapped[str] = mapped_column(String(16), index=True)
    province: Mapped[str] = mapped_column(String(64), index=True)
    immigrant_status: Mapped[str] = mapped_column(String(128), index=True)
    characteristic: Mapped[str] = mapped_column(String(128), index=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(256), default="StatCan 14-10-0083")


class JobOutlook(Base):
    """Job Bank — 3-year employment outlook by NOC and province."""

    __tablename__ = "job_outlooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    noc_code: Mapped[str] = mapped_column(String(8), index=True)
    noc_title: Mapped[str] = mapped_column(String(256))
    province: Mapped[str] = mapped_column(String(64), index=True)
    outlook: Mapped[str] = mapped_column(String(64))  # e.g. "very good", "good", "moderate", "limited"
    outlook_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1..5
    period: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(256), default="Job Bank Canada outlooks")


class UserProfileRow(Base):
    """Persisted user profile, keyed by session id (survives restarts)."""

    __tablename__ = "user_profiles"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    profile_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IngestionRun(Base):
    """Audit log of ingestion runs (weekly refresh)."""

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32))  # success | failed | skipped
    rows_loaded: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
