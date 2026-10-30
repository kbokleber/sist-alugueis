import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid

from app.database import Base


class ChecklistType(str, enum.Enum):
    CHECKIN = "checkin"
    CHECKOUT = "checkout"


class ChecklistStatus(str, enum.Enum):
    DRAFT = "draft"
    COMPLETED = "completed"


class ChecklistItemCondition(str, enum.Enum):
    OK = "ok"
    MISSING = "missing"
    DAMAGED = "damaged"
    OTHER = "other"


class StayChecklist(Base):
    __tablename__ = "stay_checklists"
    __table_args__ = (
        UniqueConstraint(
            "rental_revenue_id",
            "checklist_type",
            name="uq_stay_checklists_revenue_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("properties.id"),
        nullable=False,
        index=True,
    )
    rental_revenue_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("rental_revenues.id"),
        nullable=False,
        index=True,
    )
    checklist_type: Mapped[ChecklistType] = mapped_column(
        Enum(ChecklistType, name="checklist_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[ChecklistStatus] = mapped_column(
        Enum(ChecklistStatus, name="checklist_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ChecklistStatus.DRAFT,
    )
    performed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    performed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    general_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_incidents: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, onupdate=datetime.utcnow
    )

    property = relationship("Property", back_populates="stay_checklists")
    rental_revenue = relationship("RentalRevenue", back_populates="stay_checklists")
    performed_by = relationship("User", foreign_keys=[performed_by_user_id])
    items = relationship(
        "StayChecklistItem",
        back_populates="checklist",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class StayChecklistItem(Base):
    __tablename__ = "stay_checklist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    checklist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("stay_checklists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("property_inventory_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity_expected: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_found: Mapped[int | None] = mapped_column(Integer, nullable=True)
    condition: Mapped[ChecklistItemCondition] = mapped_column(
        Enum(
            ChecklistItemCondition,
            name="checklist_item_condition",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ChecklistItemCondition.OK,
    )
    incident_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    incident_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_consumable: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, onupdate=datetime.utcnow
    )

    checklist = relationship("StayChecklist", back_populates="items")
    inventory_item = relationship("PropertyInventoryItem")
