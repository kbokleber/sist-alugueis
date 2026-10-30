import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from app.models import (
    ChecklistItemCondition,
    ChecklistStatus,
    ChecklistType,
    PropertyInventoryItem,
    RentalRevenue,
    StayChecklist,
    StayChecklistItem,
)


class ChecklistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_revenue(
        self, revenue_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> RentalRevenue | None:
        query = select(RentalRevenue).where(RentalRevenue.id == revenue_id)
        if user_id is not None:
            query = query.where(RentalRevenue.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(
        self, checklist_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> StayChecklist | None:
        query = (
            select(StayChecklist)
            .options(
                selectinload(StayChecklist.items),
                selectinload(StayChecklist.rental_revenue),
                selectinload(StayChecklist.performed_by),
            )
            .where(StayChecklist.id == checklist_id)
        )
        result = await self.db.execute(query)
        checklist = result.scalar_one_or_none()
        if checklist is None:
            return None
        if user_id is not None and checklist.rental_revenue.user_id != user_id:
            return None
        return checklist

    async def list_for_revenue(
        self, revenue_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> list[StayChecklist]:
        revenue = await self.get_revenue(revenue_id, user_id)
        if revenue is None:
            return []
        result = await self.db.execute(
            select(StayChecklist)
            .options(
                selectinload(StayChecklist.items),
                selectinload(StayChecklist.performed_by),
            )
            .where(StayChecklist.rental_revenue_id == revenue_id)
            .order_by(StayChecklist.created_at)
        )
        return list(result.scalars().all())

    async def list_all(
        self,
        user_id: uuid.UUID | None = None,
        property_id: uuid.UUID | None = None,
        has_incidents: bool | None = None,
    ) -> list[StayChecklist]:
        query = (
            select(StayChecklist)
            .join(RentalRevenue, StayChecklist.rental_revenue_id == RentalRevenue.id)
            .options(
                selectinload(StayChecklist.items),
                selectinload(StayChecklist.performed_by),
            )
        )
        if user_id is not None:
            query = query.where(RentalRevenue.user_id == user_id)
        if property_id is not None:
            query = query.where(StayChecklist.property_id == property_id)
        if has_incidents is not None:
            query = query.where(StayChecklist.has_incidents == has_incidents)
        query = query.order_by(StayChecklist.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _load_active_inventory(
        self, property_id: uuid.UUID
    ) -> list[PropertyInventoryItem]:
        inventory_result = await self.db.execute(
            select(PropertyInventoryItem)
            .options(selectinload(PropertyInventoryItem.category))
            .where(
                PropertyInventoryItem.property_id == property_id,
                PropertyInventoryItem.is_active == True,  # noqa: E712
            )
            .order_by(PropertyInventoryItem.name)
        )
        return list(inventory_result.scalars().all())

    def _inventory_snapshot_fields(self, inv_item: PropertyInventoryItem) -> dict:
        # Usa só o que já veio no selectinload — evita lazy IO fora do await
        category = inv_item.__dict__.get("category")
        category_name = category.name if category is not None else "Sem categoria"
        return {
            "item_name": inv_item.name,
            "category_name": category_name,
            "quantity_expected": inv_item.quantity_expected,
            "is_consumable": bool(getattr(inv_item, "is_consumable", False)),
        }

    async def _refresh_from_inventory(
        self, checklist: StayChecklist, inventory_items: list[PropertyInventoryItem]
    ) -> bool:
        """Espelha o inventário atual. Retorna True se entrou item novo."""
        by_inventory_id = {
            item.inventory_item_id: item
            for item in list(checklist.items)
            if item.inventory_item_id is not None
        }
        active_ids = {inv.id for inv in inventory_items}
        added_new = False

        # Remove linhas de itens que saíram do inventário ativo
        for item in list(checklist.items):
            if item.inventory_item_id is None or item.inventory_item_id not in active_ids:
                checklist.items.remove(item)

        # Atualiza existentes e inclui novos, na ordem do inventário
        for index, inv_item in enumerate(inventory_items):
            snapshot = self._inventory_snapshot_fields(inv_item)
            existing = by_inventory_id.get(inv_item.id)
            if existing is not None:
                old_expected = existing.quantity_expected
                existing.item_name = snapshot["item_name"]
                existing.category_name = snapshot["category_name"]
                existing.quantity_expected = snapshot["quantity_expected"]
                existing.is_consumable = snapshot["is_consumable"]
                existing.sort_order = index
                # Se ainda estava no valor padrão anterior, acompanha o mínimo/qtd atual
                if (
                    existing.condition == ChecklistItemCondition.OK
                    and existing.quantity_found == old_expected
                ):
                    existing.quantity_found = snapshot["quantity_expected"]
                continue

            checklist.items.append(
                StayChecklistItem(
                    inventory_item_id=inv_item.id,
                    quantity_found=snapshot["quantity_expected"],
                    condition=ChecklistItemCondition.OK,
                    sort_order=index,
                    **snapshot,
                )
            )
            added_new = True

        return added_new

    async def create_from_inventory(
        self,
        revenue: RentalRevenue,
        checklist_type: ChecklistType,
        performed_by_user_id: uuid.UUID,
    ) -> StayChecklist:
        existing = await self.db.execute(
            select(StayChecklist)
            .options(selectinload(StayChecklist.items))
            .where(
                StayChecklist.rental_revenue_id == revenue.id,
                StayChecklist.checklist_type == checklist_type,
            )
        )
        found = existing.scalar_one_or_none()
        inventory_items = await self._load_active_inventory(revenue.property_id)
        if not inventory_items:
            raise ValueError(
                "O imóvel não possui inventário ativo para gerar o checklist"
            )

        if found is not None:
            # Sempre alinha com o inventário atual ao abrir a conferência
            before_ids = {
                item.inventory_item_id
                for item in found.items
                if item.inventory_item_id is not None
            }
            await self._refresh_from_inventory(found, inventory_items)
            after_ids = {inv.id for inv in inventory_items}
            inventory_changed = before_ids != after_ids
            if found.status == ChecklistStatus.COMPLETED and inventory_changed:
                # Inventário mudou depois da conclusão — precisa conferir de novo
                found.status = ChecklistStatus.DRAFT
                found.performed_by_user_id = None
                found.performed_at = None
            await self.db.commit()
            return await self.get_by_id(found.id)  # type: ignore[return-value]

        checklist = StayChecklist(
            property_id=revenue.property_id,
            rental_revenue_id=revenue.id,
            checklist_type=checklist_type,
            status=ChecklistStatus.DRAFT,
            performed_by_user_id=performed_by_user_id,
        )
        self.db.add(checklist)
        await self.db.flush()
        # Inicializa a collection sem disparar lazy-load (MissingGreenlet no async)
        set_committed_value(checklist, "items", [])
        await self._refresh_from_inventory(checklist, inventory_items)

        await self.db.commit()
        return await self.get_by_id(checklist.id)  # type: ignore[return-value]

    async def update_items(
        self,
        checklist: StayChecklist,
        items_data: list[dict],
        general_notes: str | None = None,
    ) -> StayChecklist:
        if checklist.status == ChecklistStatus.COMPLETED:
            raise ValueError("Checklist concluído não pode ser editado")

        items_by_id = {item.id: item for item in checklist.items}
        for payload in items_data:
            item = items_by_id.get(payload["id"])
            if item is None:
                raise ValueError(f"Item {payload['id']} não pertence a este checklist")
            if "quantity_found" in payload and payload["quantity_found"] is not None:
                item.quantity_found = payload["quantity_found"]
            if "condition" in payload and payload["condition"] is not None:
                item.condition = payload["condition"]
            if "incident_notes" in payload:
                notes = payload["incident_notes"]
                item.incident_notes = notes.strip() if isinstance(notes, str) and notes.strip() else None
            if "incident_image_url" in payload:
                image = payload["incident_image_url"]
                item.incident_image_url = (
                    image.strip() if isinstance(image, str) and image.strip() else None
                )

        if general_notes is not None:
            checklist.general_notes = general_notes

        checklist.has_incidents = self._compute_has_incidents(checklist)
        await self.db.commit()
        return await self.get_by_id(checklist.id)  # type: ignore[return-value]

    async def complete(
        self,
        checklist: StayChecklist,
        performed_by_user_id: uuid.UUID,
        general_notes: str | None = None,
    ) -> StayChecklist:
        if checklist.status == ChecklistStatus.COMPLETED:
            raise ValueError("Checklist já está concluído")

        if general_notes is not None:
            checklist.general_notes = general_notes

        checklist.has_incidents = self._compute_has_incidents(checklist)
        checklist.status = ChecklistStatus.COMPLETED
        checklist.performed_by_user_id = performed_by_user_id
        checklist.performed_at = datetime.utcnow()
        await self.db.commit()
        return await self.get_by_id(checklist.id)  # type: ignore[return-value]

    async def reopen(self, checklist: StayChecklist) -> StayChecklist:
        if checklist.status != ChecklistStatus.COMPLETED:
            raise ValueError("Checklist não está concluído")

        checklist.status = ChecklistStatus.DRAFT
        checklist.performed_by_user_id = None
        checklist.performed_at = None
        inventory_items = await self._load_active_inventory(checklist.property_id)
        if inventory_items:
            _ = checklist.items
            await self._refresh_from_inventory(checklist, inventory_items)
        await self.db.commit()
        return await self.get_by_id(checklist.id)  # type: ignore[return-value]

    def _compute_has_incidents(self, checklist: StayChecklist) -> bool:
        for item in checklist.items:
            if item.condition != ChecklistItemCondition.OK:
                return True
            if item.incident_notes and item.incident_notes.strip():
                return True
            if item.incident_image_url and item.incident_image_url.strip():
                return True
            if (
                item.quantity_found is not None
                and item.quantity_found != item.quantity_expected
            ):
                return True
        if checklist.general_notes and checklist.general_notes.strip():
            # general notes alone don't force incident unless already flagged
            pass
        return False
