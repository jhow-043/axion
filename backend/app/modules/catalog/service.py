from __future__ import annotations

from uuid import UUID

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.catalog.repository import (
    CategoryRepository,
    PendingReasonRepository,
    PriorityRepository,
    StatusRepository,
)
from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
    PendingReasonCreate,
    PendingReasonListResponse,
    PendingReasonResponse,
    PendingReasonUpdate,
    PriorityCreate,
    PriorityListResponse,
    PriorityResponse,
    PriorityUpdate,
    StatusListResponse,
    StatusResponse,
    StatusUpdate,
)


class PriorityService:
    def __init__(self, repo: PriorityRepository) -> None:
        self._repo = repo

    async def create(self, data: PriorityCreate) -> PriorityResponse:
        if await self._repo.find_by_code(data.code) is not None:
            raise ConflictError("Código de prioridade já cadastrado neste tenant.")
        priority = await self._repo.create(
            {
                "name": data.name,
                "code": data.code,
                "color": data.color,
                "order": data.order,
                "is_default": False,
            }
        )
        return PriorityResponse.model_validate(priority)

    async def get(self, priority_id: UUID) -> PriorityResponse:
        priority = await self._repo.get(priority_id)
        if priority is None:
            raise NotFoundError("Prioridade não encontrada.")
        return PriorityResponse.model_validate(priority)

    async def list(
        self, *, page: int, page_size: int, is_active: bool | None = None
    ) -> PriorityListResponse:
        offset = (page - 1) * page_size
        items = await self._repo.list_filtered(is_active=is_active, offset=offset, limit=page_size)
        total = await self._repo.count_filtered(is_active=is_active)
        return PriorityListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[PriorityResponse.model_validate(p) for p in items],
        )

    async def update(self, priority_id: UUID, data: PriorityUpdate) -> PriorityResponse:
        priority = await self._repo.get(priority_id)
        if priority is None:
            raise NotFoundError("Prioridade não encontrada.")

        changes: dict = {}
        if data.name is not None:
            changes["name"] = data.name
        if "color" in data.model_fields_set:
            changes["color"] = data.color
        if data.order is not None:
            changes["order"] = data.order

        if changes:
            await self._repo.update(priority_id, changes)
        return await self.get(priority_id)

    async def deactivate(self, priority_id: UUID) -> PriorityResponse:
        priority = await self._repo.get(priority_id)
        if priority is None:
            raise NotFoundError("Prioridade não encontrada.")
        if not priority.is_active:
            raise BusinessRuleError("Prioridade já está inativa.")
        await self._repo.update(priority_id, {"is_active": False})
        return await self.get(priority_id)


class StatusService:
    def __init__(self, repo: StatusRepository) -> None:
        self._repo = repo

    async def get(self, status_id: UUID) -> StatusResponse:
        status = await self._repo.get(status_id)
        if status is None:
            raise NotFoundError("Status não encontrado.")
        return StatusResponse.model_validate(status)

    async def list(
        self, *, page: int, page_size: int, is_active: bool | None = None
    ) -> StatusListResponse:
        offset = (page - 1) * page_size
        items = await self._repo.list_filtered(is_active=is_active, offset=offset, limit=page_size)
        total = await self._repo.count_filtered(is_active=is_active)
        return StatusListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[StatusResponse.model_validate(s) for s in items],
        )

    async def update(self, status_id: UUID, data: StatusUpdate) -> StatusResponse:
        # INV-03 / ADR-0003: StatusUpdate schema (extra="forbid") already rejects behavioral flags.
        # Only name and order are editable on any status.
        status = await self._repo.get(status_id)
        if status is None:
            raise NotFoundError("Status não encontrado.")

        changes: dict = {}
        if data.name is not None:
            changes["name"] = data.name
        if data.order is not None:
            changes["order"] = data.order

        if changes:
            await self._repo.update(status_id, changes)
        return await self.get(status_id)


class CategoryService:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    async def create(self, data: CategoryCreate) -> CategoryResponse:
        if await self._repo.find_by_name(data.name) is not None:
            raise ConflictError("Nome de categoria já cadastrado neste tenant.")
        category = await self._repo.create({"name": data.name, "description": data.description})
        return CategoryResponse.model_validate(category)

    async def get(self, category_id: UUID) -> CategoryResponse:
        category = await self._repo.get(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada.")
        return CategoryResponse.model_validate(category)

    async def list(
        self, *, page: int, page_size: int, is_active: bool | None = None
    ) -> CategoryListResponse:
        offset = (page - 1) * page_size
        items = await self._repo.list_filtered(is_active=is_active, offset=offset, limit=page_size)
        total = await self._repo.count_filtered(is_active=is_active)
        return CategoryListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[CategoryResponse.model_validate(c) for c in items],
        )

    async def update(self, category_id: UUID, data: CategoryUpdate) -> CategoryResponse:
        category = await self._repo.get(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada.")

        changes: dict = {}
        if data.name is not None and data.name != category.name:
            if await self._repo.find_by_name(data.name) is not None:
                raise ConflictError("Nome de categoria já cadastrado neste tenant.")
            changes["name"] = data.name
        if "description" in data.model_fields_set:
            changes["description"] = data.description

        if changes:
            await self._repo.update(category_id, changes)
        return await self.get(category_id)

    async def deactivate(self, category_id: UUID) -> CategoryResponse:
        category = await self._repo.get(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada.")
        if not category.is_active:
            raise BusinessRuleError("Categoria já está inativa.")
        await self._repo.update(category_id, {"is_active": False})
        return await self.get(category_id)


class PendingReasonService:
    def __init__(self, repo: PendingReasonRepository) -> None:
        self._repo = repo

    async def create(self, data: PendingReasonCreate) -> PendingReasonResponse:
        if await self._repo.find_by_name(data.name) is not None:
            raise ConflictError("Nome de motivo de pendência já cadastrado neste tenant.")
        reason = await self._repo.create({"name": data.name, "description": data.description})
        return PendingReasonResponse.model_validate(reason)

    async def get(self, reason_id: UUID) -> PendingReasonResponse:
        reason = await self._repo.get(reason_id)
        if reason is None:
            raise NotFoundError("Motivo de pendência não encontrado.")
        return PendingReasonResponse.model_validate(reason)

    async def list(
        self, *, page: int, page_size: int, is_active: bool | None = None
    ) -> PendingReasonListResponse:
        offset = (page - 1) * page_size
        items = await self._repo.list_filtered(is_active=is_active, offset=offset, limit=page_size)
        total = await self._repo.count_filtered(is_active=is_active)
        return PendingReasonListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[PendingReasonResponse.model_validate(r) for r in items],
        )

    async def update(self, reason_id: UUID, data: PendingReasonUpdate) -> PendingReasonResponse:
        reason = await self._repo.get(reason_id)
        if reason is None:
            raise NotFoundError("Motivo de pendência não encontrado.")

        changes: dict = {}
        if data.name is not None and data.name != reason.name:
            if await self._repo.find_by_name(data.name) is not None:
                raise ConflictError("Nome de motivo de pendência já cadastrado neste tenant.")
            changes["name"] = data.name
        if "description" in data.model_fields_set:
            changes["description"] = data.description

        if changes:
            await self._repo.update(reason_id, changes)
        return await self.get(reason_id)

    async def deactivate(self, reason_id: UUID) -> PendingReasonResponse:
        reason = await self._repo.get(reason_id)
        if reason is None:
            raise NotFoundError("Motivo de pendência não encontrado.")
        if not reason.is_active:
            raise BusinessRuleError("Motivo de pendência já está inativo.")
        await self._repo.update(reason_id, {"is_active": False})
        return await self.get(reason_id)
