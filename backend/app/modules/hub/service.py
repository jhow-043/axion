from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.administration.repository import TenantRepository
from app.modules.hub.repository import ModuleRepository
from app.modules.hub.schemas import (
    ModuleCatalogItem,
    TenantEnabledModule,
    TenantModulesResponse,
)


class PlatformModuleService:
    def __init__(
        self,
        module_repo: ModuleRepository,
        tenant_repo: TenantRepository,
    ) -> None:
        self._modules = module_repo
        self._tenants = tenant_repo

    async def list_catalog(self) -> list[ModuleCatalogItem]:
        modules = await self._modules.list_catalog()
        return [ModuleCatalogItem.model_validate(m) for m in modules]

    async def get_tenant_modules(self, tenant_id: UUID) -> TenantModulesResponse:
        tenant = await self._tenants.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Empresa não encontrada.")

        catalog_models = await self._modules.list_catalog()
        enabled_rows = await self._modules.list_tenant_modules_with_code(tenant_id)

        return TenantModulesResponse(
            catalog=[ModuleCatalogItem.model_validate(m) for m in catalog_models],
            enabled=[
                TenantEnabledModule(
                    module_id=module_id,
                    module_code=module_code,
                    enabled_at=enabled_at,
                )
                for module_id, module_code, enabled_at in enabled_rows
            ],
        )

    async def enable_module(self, tenant_id: UUID, module_id: UUID) -> None:
        tenant = await self._tenants.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Empresa não encontrada.")

        module = await self._modules.get_by_id(module_id)
        if module is None:
            raise NotFoundError("Módulo não encontrado.")

        # Idempotent — enable_for_tenant is a no-op when already enabled
        await self._modules.enable_for_tenant(tenant_id, module_id)

    async def revoke_module(self, tenant_id: UUID, module_id: UUID) -> None:
        tenant = await self._tenants.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Empresa não encontrada.")

        removed = await self._modules.revoke_for_tenant(tenant_id, module_id)
        if not removed:
            raise NotFoundError("Módulo não está liberado para esta empresa.")
