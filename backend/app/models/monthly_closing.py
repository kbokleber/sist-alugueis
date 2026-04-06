import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, DECIMAL, Text, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database import Base


class ClosingStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class MonthlyClosing(Base):
    __tablename__ = "monthly_closings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)
    total_revenue: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False, default=0)
    total_expenses: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False, default=0)
    net_result: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False, default=0)
    total_nights: Mapped[int] = mapped_column(default=0)
    total_bookings: Mapped[int] = mapped_column(default=0)
    depreciation_value: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    cleaning_total: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    platform_fee_total: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    other_expenses: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    status: Mapped[ClosingStatus] = mapped_column(
        Enum(ClosingStatus), default=ClosingStatus.OPEN
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="closings")
    property = relationship("Property", back_populates="closings")

    __table_args__ = (
        Index("idx_closing_property_month", "property_id", "year_month", unique=True),
    )
