# ============================================================================
# KrishiBondhu Bangladesh — Geographic Hierarchy ORM Models
# Maps to geo.divisions, geo.districts, geo.upazilas, geo.unions
# ============================================================================

import uuid
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Division(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Maps to geo.divisions."""

    __tablename__ = "divisions"
    __table_args__ = {"schema": "geo"}

    bbs_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    districts: Mapped[list["District"]] = relationship("District", back_populates="division", lazy="selectin")


class District(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Maps to geo.districts."""

    __tablename__ = "districts"
    __table_args__ = {"schema": "geo"}

    division_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("geo.divisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bbs_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    division: Mapped["Division"] = relationship("Division", back_populates="districts", lazy="joined")
    upazilas: Mapped[list["Upazila"]] = relationship("Upazila", back_populates="district", lazy="selectin")


class Upazila(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Maps to geo.upazilas."""

    __tablename__ = "upazilas"
    __table_args__ = {"schema": "geo"}

    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("geo.districts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bbs_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    district: Mapped["District"] = relationship("District", back_populates="upazilas", lazy="joined")
    unions: Mapped[list["Union"]] = relationship("Union", back_populates="upazila", lazy="selectin")


class Union(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Maps to geo.unions."""

    __tablename__ = "unions"
    __table_args__ = {"schema": "geo"}

    upazila_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("geo.upazilas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bbs_code: Mapped[str] = mapped_column(String(10), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    upazila: Mapped["Upazila"] = relationship("Upazila", back_populates="unions", lazy="joined")

