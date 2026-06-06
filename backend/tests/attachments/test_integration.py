"""Testes de integração — P11 Anexos e Evidências.

Cobrem: upload-url, confirm, list, download-url, delete, controle de acesso.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.models import Attachment
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import User


@pytest.mark.asyncio
async def test_upload_url_invalid_mime_returns_422(requester_client, sample_ticket: Ticket):
    resp = await requester_client.post(
        f"/api/v1/tickets/{sample_ticket.id}/attachments/upload-url",
        json={"filename": "doc.pdf", "mime_type": "application/pdf", "size_bytes": 1024},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_url_image_too_large_returns_422(requester_client, sample_ticket: Ticket):
    over_limit = 10 * 1024 * 1024 + 1
    resp = await requester_client.post(
        f"/api/v1/tickets/{sample_ticket.id}/attachments/upload-url",
        json={"filename": "foto.jpg", "mime_type": "image/jpeg", "size_bytes": over_limit},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_url_video_too_large_returns_422(requester_client, sample_ticket: Ticket):
    over_limit = 200 * 1024 * 1024 + 1
    resp = await requester_client.post(
        f"/api/v1/tickets/{sample_ticket.id}/attachments/upload-url",
        json={"filename": "video.mp4", "mime_type": "video/mp4", "size_bytes": over_limit},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_url_valid_returns_200(requester_client, sample_ticket: Ticket):
    resp = await requester_client.post(
        f"/api/v1/tickets/{sample_ticket.id}/attachments/upload-url",
        json={"filename": "foto.jpg", "mime_type": "image/jpeg", "size_bytes": 1024},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "upload_url" in body
    assert "storage_key" in body
    assert body["expires_in"] == 300


@pytest.mark.asyncio
async def test_upload_url_storage_key_has_tenant_prefix(
    requester_client, sample_ticket: Ticket, seeded_tenant: Tenant
):
    resp = await requester_client.post(
        f"/api/v1/tickets/{sample_ticket.id}/attachments/upload-url",
        json={"filename": "foto.jpg", "mime_type": "image/jpeg", "size_bytes": 512},
    )
    key = resp.json()["storage_key"]
    assert key.startswith(str(seeded_tenant.id))


@pytest.mark.asyncio
async def test_confirm_creates_attachment_and_timeline(
    requester_client,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    requester_user: User,
):
    storage_key = f"{seeded_tenant.id}/{sample_ticket.id}/abc123.jpg"
    resp = await requester_client.post(
        f"/api/v1/tickets/{sample_ticket.id}/attachments/confirm",
        json={
            "storage_key": storage_key,
            "filename": "foto.jpg",
            "mime_type": "image/jpeg",
            "size_bytes": 1024,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "foto.jpg"
    assert body["mime_type"] == "image/jpeg"
    assert body["uploaded_by"] == str(requester_user.id)


@pytest.mark.asyncio
async def test_confirm_wrong_tenant_prefix_returns_422(requester_client, sample_ticket: Ticket):
    resp = await requester_client.post(
        f"/api/v1/tickets/{sample_ticket.id}/attachments/confirm",
        json={
            "storage_key": "wrong-tenant/wrong-ticket/file.jpg",
            "filename": "foto.jpg",
            "mime_type": "image/jpeg",
            "size_bytes": 1024,
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_attachments_returns_items(
    requester_client,
    sample_ticket: Ticket,
    sample_attachment: Attachment,
):
    resp = await requester_client.get(f"/api/v1/tickets/{sample_ticket.id}/attachments")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(a["id"] == str(sample_attachment.id) for a in body["items"])


@pytest.mark.asyncio
async def test_list_attachments_empty_when_none(requester_client, sample_ticket: Ticket):
    resp = await requester_client.get(f"/api/v1/tickets/{sample_ticket.id}/attachments")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_download_url_returns_url(requester_client, sample_attachment: Attachment):
    resp = await requester_client.get(f"/api/v1/attachments/{sample_attachment.id}/download-url")
    assert resp.status_code == 200
    body = resp.json()
    assert "download_url" in body
    assert body["expires_in"] == 3600


@pytest.mark.asyncio
async def test_delete_attachment_removes_record(
    requester_client,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    requester_user: User,
    mock_storage,
):
    import uuid

    from app.modules.attachments.models import Attachment as AttModel

    att = AttModel(
        tenant_id=seeded_tenant.id,
        ticket_id=sample_ticket.id,
        uploaded_by=requester_user.id,
        filename="del.jpg",
        storage_key=f"{seeded_tenant.id}/{sample_ticket.id}/{uuid.uuid4()}.jpg",
        mime_type="image/jpeg",
        size_bytes=512,
    )
    db_session.add(att)
    await db_session.flush()

    resp = await requester_client.delete(f"/api/v1/attachments/{att.id}")
    assert resp.status_code == 204
    mock_storage.delete_object.assert_called_once_with(att.storage_key)


@pytest.mark.asyncio
async def test_delete_by_admin_succeeds(
    admin_client,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    requester_user: User,
):
    import uuid

    from app.modules.attachments.models import Attachment as AttModel

    att = AttModel(
        tenant_id=seeded_tenant.id,
        ticket_id=sample_ticket.id,
        uploaded_by=requester_user.id,
        filename="del2.jpg",
        storage_key=f"{seeded_tenant.id}/{sample_ticket.id}/{uuid.uuid4()}.jpg",
        mime_type="image/jpeg",
        size_bytes=512,
    )
    db_session.add(att)
    await db_session.flush()

    resp = await admin_client.delete(f"/api/v1/attachments/{att.id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_upload_url_non_participant_returns_403(outsider_client, sample_ticket: Ticket):
    resp = await outsider_client.post(
        f"/api/v1/tickets/{sample_ticket.id}/attachments/upload-url",
        json={"filename": "foto.jpg", "mime_type": "image/jpeg", "size_bytes": 512},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_non_participant_returns_403(outsider_client, sample_ticket: Ticket):
    resp = await outsider_client.get(f"/api/v1/tickets/{sample_ticket.id}/attachments")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_download_url_non_participant_returns_403(
    outsider_client, sample_attachment: Attachment
):
    resp = await outsider_client.get(f"/api/v1/attachments/{sample_attachment.id}/download-url")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_endpoints_require_auth(anon_client, sample_ticket: Ticket):
    resp = await anon_client.post(
        f"/api/v1/tickets/{sample_ticket.id}/attachments/upload-url",
        json={"filename": "f.jpg", "mime_type": "image/jpeg", "size_bytes": 100},
    )
    assert resp.status_code == 401

    resp = await anon_client.get(f"/api/v1/tickets/{sample_ticket.id}/attachments")
    assert resp.status_code == 401
