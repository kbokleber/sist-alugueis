import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, onupdate=datetime.utcnow
    )

    # Relationships
    properties = relationship("Property", back_populates="owner", lazy="selectin")
    categories = relationship("FinancialCategory", back_populates="owner", lazy="selectin")
    revenues = relationship("RentalRevenue", back_populates="user", lazy="selectin")
    expenses = relationship("PropertyExpense", back_populates="user", lazy="selectin")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="selectin")
