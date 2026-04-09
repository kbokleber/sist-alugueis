import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, DECIMAL, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.database import Base


class Property(Base):
    __tablename__ = "properties"

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
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    property_value: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    monthly_depreciation_percent: Mapped[float] = mapped_column(
        DECIMAL(5, 2), default=1.00
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, onupdate=datetime.utcnow
    )

    # Relationships
    owner = relationship("User", back_populates="properties")
    revenues = relationship("RentalRevenue", back_populates="property", lazy="selectin")
    expenses = relationship("PropertyExpense", back_populates="property", lazy="selectin")
