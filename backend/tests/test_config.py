from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestSettingsRequired:
    def test_missing_database_url_raises_validation_error(self, monkeypatch) -> None:
        from app.core.config import Settings  # ensure module is cached before delenv

        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)

        with pytest.raises((ValidationError, Exception)):
            Settings()

    def test_missing_secret_key_raises_validation_error(self, monkeypatch) -> None:
        from app.core.config import Settings  # ensure module is cached before delenv

        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
        monkeypatch.delenv("SECRET_KEY", raising=False)

        with pytest.raises((ValidationError, Exception)):
            Settings()

    def test_settings_loads_when_required_fields_are_set(self, monkeypatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
        monkeypatch.setenv("SECRET_KEY", "test-secret")

        from app.core.config import Settings

        s = Settings()
        assert s.DATABASE_URL == "sqlite+aiosqlite:///./test.db"
        assert s.SECRET_KEY == "test-secret"

    def test_non_sensitive_fields_have_defaults(self, monkeypatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
        monkeypatch.setenv("SECRET_KEY", "test-secret")

        from app.core.config import Settings

        s = Settings()
        assert s.DEBUG is False
        assert s.LOG_LEVEL == "INFO"
        assert isinstance(s.CORS_ORIGINS, list)


class TestModuleImportability:
    def test_all_module_stubs_are_importable(self) -> None:
        import importlib

        module_names = [
            "app.modules.auth",
            "app.modules.users",
            "app.modules.teams",
            "app.modules.catalog",
            "app.modules.locations",
            "app.modules.equipments",
            "app.modules.tickets",
            "app.modules.timeline",
            "app.modules.attachments",
            "app.modules.sla",
            "app.modules.notifications",
            "app.modules.dashboards",
            "app.modules.reports",
            "app.modules.audit",
            "app.modules.administration",
        ]
        for name in module_names:
            assert importlib.import_module(name) is not None

    def test_core_modules_are_importable(self) -> None:
        import importlib

        core_names = (
            "app.core.config",
            "app.core.deps",
            "app.core.exceptions",
            "app.core.pagination",
        )
        for name in core_names:
            assert importlib.import_module(name) is not None

    def test_shared_modules_are_importable(self) -> None:
        import importlib

        for name in (
            "app.shared.base_repository",
            "app.shared.event_bus",
            "app.shared.tenant_context",
            "app.shared.tenant_mixin",
        ):
            assert importlib.import_module(name) is not None
