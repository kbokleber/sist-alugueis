import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Integer, DECIMAL, Text, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.database import Base


class RentalRevenue(Base):
    __tablename__ = "rental_revenues"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("properties.id"),
        nullable=False,
        index=True,
    )
    year_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    checkin_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    checkout_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False)
    listing_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    listing_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nights: Mapped[int] = mapped_column(Integer, nullable=False)
    gross_amount: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    cleaning_fee: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    platform_fee: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    net_amount: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="revenues")
    property = relationship("Property", back_populates="revenues")

    __table_args__ = (
        Index("idx_revenues_property_month", "property_id", "year_month"),
        Index("idx_revenues_user_month", "user_id", "year_month"),
        Index("idx_revenues_guest", "guest_name"),
    )
