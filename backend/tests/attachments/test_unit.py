"""Testes unitários — P11 Anexos e Evidências.

Cobrem: validação de MIME, validação de tamanho, geração de storage_key.
"""

from __future__ import annotations

import pytest

from app.core.exceptions import UnprocessableError
from app.modules.attachments.service import AttachmentService, _build_storage_key


class TestMimeAndSizeValidation:
    def test_valid_image_passes(self):
        AttachmentService._validate_mime_and_size("image/jpeg", 1024)

    def test_valid_video_passes(self):
        AttachmentService._validate_mime_and_size("video/mp4", 1024)

    def test_invalid_mime_raises_422(self):
        with pytest.raises(UnprocessableError, match="Tipo MIME"):
            AttachmentService._validate_mime_and_size("application/pdf", 1024)

    def test_invalid_mime_svg_raises_422(self):
        with pytest.raises(UnprocessableError, match="Tipo MIME"):
            AttachmentService._validate_mime_and_size("image/svg+xml", 1024)

    def test_image_exceeds_max_raises_422(self):
        over_limit = 10 * 1024 * 1024 + 1
        with pytest.raises(UnprocessableError, match="Imagem excede"):
            AttachmentService._validate_mime_and_size("image/jpeg", over_limit)

    def test_video_exceeds_max_raises_422(self):
        over_limit = 200 * 1024 * 1024 + 1
        with pytest.raises(UnprocessableError, match="Vídeo excede"):
            AttachmentService._validate_mime_and_size("video/mp4", over_limit)

    def test_image_at_max_boundary_passes(self):
        AttachmentService._validate_mime_and_size("image/png", 10 * 1024 * 1024)

    def test_video_at_max_boundary_passes(self):
        AttachmentService._validate_mime_and_size("video/quicktime", 200 * 1024 * 1024)

    def test_webp_image_accepted(self):
        AttachmentService._validate_mime_and_size("image/webp", 512)


class TestStorageKeyGeneration:
    def test_key_contains_tenant_id(self):
        import uuid

        tenant_id = uuid.uuid4()
        ticket_id = uuid.uuid4()
        key = _build_storage_key(tenant_id, ticket_id, "foto.jpg")
        assert key.startswith(f"{tenant_id}/")

    def test_key_contains_ticket_id(self):
        import uuid

        tenant_id = uuid.uuid4()
        ticket_id = uuid.uuid4()
        key = _build_storage_key(tenant_id, ticket_id, "foto.jpg")
        assert f"/{ticket_id}/" in key

    def test_key_preserves_extension(self):
        import uuid

        key = _build_storage_key(uuid.uuid4(), uuid.uuid4(), "video.mp4")
        assert key.endswith(".mp4")

    def test_key_lowercases_extension(self):
        import uuid

        key = _build_storage_key(uuid.uuid4(), uuid.uuid4(), "FOTO.JPG")
        assert key.endswith(".jpg")

    def test_keys_are_unique(self):
        import uuid

        tid = uuid.uuid4()
        tickid = uuid.uuid4()
        keys = {_build_storage_key(tid, tickid, "foto.jpg") for _ in range(10)}
        assert len(keys) == 10

    def test_key_format_is_three_segments(self):
        import uuid

        tid = uuid.uuid4()
        tickid = uuid.uuid4()
        key = _build_storage_key(tid, tickid, "foto.jpg")
        parts = key.split("/")
        assert len(parts) == 3  # {tenant_id}/{ticket_id}/{uuid}.ext
