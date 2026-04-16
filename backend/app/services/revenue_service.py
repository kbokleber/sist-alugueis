import uuid
from datetime import date
import re
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import RentalRevenue


class RevenueService:
    _IMPORT_HINT_FIELDS = ("is_pending", "payment_status", "pending_text", "status")

    def __init__(self, db: AsyncSession):
        self.db = db

    @classmethod
    def _calculate_gross_amount(
        cls,
        net_amount: float | int,
        cleaning_fee: float | int = 0,
        platform_fee: float | int = 0,
    ) -> float:
        return float(net_amount or 0) + float(cleaning_fee or 0) + float(platform_fee or 0)

    @classmethod
    def _get_reference_date(cls, checkin_date: date | None, fallback_date: date) -> date:
        if checkin_date is not None and 2000 <= checkin_date.year <= 2100:
            return checkin_date
        return fallback_date

    @classmethod
    def _calculate_year_month(cls, reference_date: date) -> str:
        year = reference_date.year
        month = reference_date.month + 1
        if month == 13:
            year += 1
            month = 1
        return f"{year}-{month:02d}"

    @classmethod
    def _parse_brazilian_currency_text(cls, value: str) -> float | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        cleaned = cleaned.replace("R$", "").replace(" ", "")
        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    @classmethod
    def _extract_pending_amount_from_text(cls, text: str) -> float | None:
        match = re.search(
            r"pendente(?:\s*[:\-]?\s*)(R\$\s*[\d\.\,]+|[\d\.\,]+)",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        return cls._parse_brazilian_currency_text(match.group(1))

    @classmethod
    def _has_pending_signal(cls, value: str | None) -> bool:
        return bool(value and "pendente" in value.casefold())

    @classmethod
    def _derive_pending_amount(
        cls,
        payload: dict,
        fallback_net_amount: float | int | None = None,
    ) -> float | None:
        if payload.get("pending_amount") is not None:
            return float(payload["pending_amount"])

        text_candidates = [
            payload.get("pending_text"),
            payload.get("payment_status"),
            payload.get("status"),
            payload.get("notes"),
        ]
        has_pending_label = any(cls._has_pending_signal(text) for text in text_candidates)

        for text in text_candidates:
            if not isinstance(text, str):
                continue
            amount = cls._extract_pending_amount_from_text(text)
            if amount is not None:
                return amount

        if payload.get("is_pending") is True or has_pending_label:
            reference_net = payload.get("net_amount", fallback_net_amount)
            if reference_net is not None:
                return float(reference_net)

        return None

    @classmethod
    def _sanitize_import_hint_fields(cls, payload: dict) -> None:
        for field in cls._IMPORT_HINT_FIELDS:
            payload.pop(field, None)

    async def get_by_id(self, revenue_id: uuid.UUID, user_id: uuid.UUID | None = None) -> RentalRevenue | None:
        query = (
            select(RentalRevenue)
            .options(selectinload(RentalRevenue.property))
            .where(RentalRevenue.id == revenue_id)
        )
        if user_id is not None:
            query = query.where(RentalRevenue.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        user_id: uuid.UUID | None,
        property_id: uuid.UUID | None = None,
        year_month: str | None = None,
        start_month: str | None = None,
        end_month: str | None = None,
        listing_source: str | None = None,
        external_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[RentalRevenue], int, dict]:
        query = select(RentalRevenue).options(selectinload(RentalRevenue.property))
        count_query = select(func.count(RentalRevenue.id))
        totals_query = select(
            func.coalesce(func.sum(RentalRevenue.gross_amount), 0).label("total_gross"),
            func.coalesce(func.sum(RentalRevenue.net_amount), 0).label("total_net"),
            func.coalesce(func.sum(RentalRevenue.pending_amount), 0).label("total_pending"),
        )

        if user_id is not None:
            query = query.where(RentalRevenue.user_id == user_id)
            count_query = count_query.where(RentalRevenue.user_id == user_id)
            totals_query = totals_query.where(RentalRevenue.user_id == user_id)

        if property_id:
            query = query.where(RentalRevenue.property_id == property_id)
            count_query = count_query.where(RentalRevenue.property_id == property_id)
            totals_query = totals_query.where(RentalRevenue.property_id == property_id)
        if year_month:
            query = query.where(RentalRevenue.year_month == year_month)
            count_query = count_query.where(RentalRevenue.year_month == year_month)
            totals_query = totals_query.where(RentalRevenue.year_month == year_month)
        if start_month:
            query = query.where(RentalRevenue.year_month >= start_month)
            count_query = count_query.where(RentalRevenue.year_month >= start_month)
            totals_query = totals_query.where(RentalRevenue.year_month >= start_month)
        if end_month:
            query = query.where(RentalRevenue.year_month <= end_month)
            count_query = count_query.where(RentalRevenue.year_month <= end_month)
            totals_query = totals_query.where(RentalRevenue.year_month <= end_month)
        if listing_source:
            query = query.where(RentalRevenue.listing_source == listing_source)
            count_query = count_query.where(RentalRevenue.listing_source == listing_source)
            totals_query = totals_query.where(RentalRevenue.listing_source == listing_source)
        if external_id:
            external_id_term = f"%{external_id.strip()}%"
            query = query.where(RentalRevenue.external_id.ilike(external_id_term))
            count_query = count_query.where(RentalRevenue.external_id.ilike(external_id_term))
            totals_query = totals_query.where(RentalRevenue.external_id.ilike(external_id_term))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        totals_result = await self.db.execute(totals_query)
        totals_row = totals_result.one()
        totals = {
            "total_gross": float(totals_row.total_gross or 0),
            "total_net": float(totals_row.total_net or 0),
            "total_pending": float(totals_row.total_pending or 0),
            "total_net_after_pending": float(totals_row.total_net or 0) - float(totals_row.total_pending or 0),
        }

        query = query.order_by(RentalRevenue.date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total, totals

    async def create(self, user_id: uuid.UUID, data: dict) -> RentalRevenue:
        pending_amount = self._derive_pending_amount(data)
        if pending_amount is not None:
            data["pending_amount"] = pending_amount
        self._sanitize_import_hint_fields(data)

        reference_date = self._get_reference_date(data.get("checkin_date"), data.get("date"))
        if reference_date is not None:
            data["year_month"] = self._calculate_year_month(reference_date)
        data["gross_amount"] = self._calculate_gross_amount(
            data.get("net_amount", 0),
            data.get("cleaning_fee", 0),
            data.get("platform_fee", 0),
        )
        revenue = RentalRevenue(user_id=user_id, **data)
        self.db.add(revenue)
        await self.db.commit()
        await self.db.refresh(revenue)
        return revenue

    async def update(self, revenue: RentalRevenue, data: dict) -> RentalRevenue:
        pending_amount = self._derive_pending_amount(data, fallback_net_amount=revenue.net_amount)
        if pending_amount is not None:
            data["pending_amount"] = pending_amount
        self._sanitize_import_hint_fields(data)

        provided_year_month = data.get("year_month")
        if not provided_year_month:
            reference_date = self._get_reference_date(
                data.get("checkin_date", revenue.checkin_date),
                data.get("date", revenue.date),
            )
            if reference_date is not None:
                data["year_month"] = self._calculate_year_month(reference_date)
        if data.get("gross_amount") is None and any(
            field in data for field in ("net_amount", "cleaning_fee", "platform_fee")
        ):
            data["gross_amount"] = self._calculate_gross_amount(
                data.get("net_amount", revenue.net_amount),
                data.get("cleaning_fee", revenue.cleaning_fee),
                data.get("platform_fee", revenue.platform_fee),
            )
        for field, value in data.items():
            if value is not None:
                setattr(revenue, field, value)
        await self.db.commit()
        await self.db.refresh(revenue)
        return revenue

    async def delete(self, revenue: RentalRevenue) -> None:
        await self.db.delete(revenue)
        await self.db.commit()

    async def get_summary(
        self,
        user_id: uuid.UUID | None,
        property_id: uuid.UUID | None = None,
        year_month: str | None = None,
    ) -> dict:
        query = select(
            func.coalesce(func.sum(RentalRevenue.gross_amount), 0).label("total_gross"),
            func.coalesce(func.sum(RentalRevenue.net_amount), 0).label("total_net"),
            func.coalesce(func.sum(RentalRevenue.nights), 0).label("total_nights"),
            func.count(RentalRevenue.id).label("total_bookings"),
            func.coalesce(func.sum(RentalRevenue.cleaning_fee), 0).label("total_cleaning"),
            func.coalesce(func.sum(RentalRevenue.platform_fee), 0).label("total_platform_fee"),
        )

        if user_id is not None:
            query = query.where(RentalRevenue.user_id == user_id)

        if property_id:
            query = query.where(RentalRevenue.property_id == property_id)
        if year_month:
            query = query.where(RentalRevenue.year_month == year_month)

        result = await self.db.execute(query)
        row = result.one()
        return {
            "year_month": year_month or "all",
            "total_gross": float(row.total_gross or 0),
            "total_net": float(row.total_net or 0),
            "total_nights": row.total_nights or 0,
            "total_bookings": row.total_bookings or 0,
            "total_cleaning": float(row.total_cleaning or 0),
            "total_platform_fee": float(row.total_platform_fee or 0),
        }

    async def get_calendar_reservations(
        self,
        user_id: uuid.UUID | None,
        property_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[RentalRevenue]:
        query = (
            select(RentalRevenue)
            .options(selectinload(RentalRevenue.property))
            .where(RentalRevenue.property_id == property_id)
        )

        if user_id is not None:
            query = query.where(RentalRevenue.user_id == user_id)

        query = query.where(
            or_(
                and_(
                    RentalRevenue.checkin_date.is_not(None),
                    RentalRevenue.checkout_date.is_not(None),
                    RentalRevenue.checkout_date >= start_date,
                    RentalRevenue.checkin_date <= end_date,
                ),
                and_(
                    RentalRevenue.checkin_date.is_(None),
                    RentalRevenue.checkout_date.is_(None),
                    RentalRevenue.date >= start_date,
                    RentalRevenue.date <= end_date,
                ),
            )
        )

        query = query.order_by(
            func.coalesce(RentalRevenue.checkin_date, RentalRevenue.date).asc(),
            RentalRevenue.checkout_date.asc(),
            RentalRevenue.date.asc(),
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
