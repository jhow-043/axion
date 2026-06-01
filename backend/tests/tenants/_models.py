from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.shared.base_repository import BaseRepository
from app.shared.tenant_mixin import TenantMixin


class SampleItem(Base, TenantMixin):
    """Test-only model for verifying BaseRepository tenant isolation. Not a real domain entity."""

    __tablename__ = "_test_sample_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class SampleItemRepository(BaseRepository[SampleItem]):
    __model__ = SampleItem
