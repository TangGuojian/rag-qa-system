import pytest
import io
from app.models.document import DocStatus


@pytest.fixture
def test_kb(client, admin_headers):
    resp = client.post("/api/v1/knowledge-bases", json={"name": "测试知识库"}, headers=admin_headers)
    return resp.json()


class TestDocumentsAPI:
    def test_upload_txt(self, client, admin_headers, test_kb, uploads_dir):
        kb_id = test_kb["id"]
        resp = client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "doc_id" in data
        assert data["status"] == DocStatus.COMPLETED.value

    def test_upload_pdf(self, client, admin_headers, test_kb):
        kb_id = test_kb["id"]
        resp = client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 mock content"), "application/pdf")},
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_upload_md(self, client, admin_headers, test_kb):
        kb_id = test_kb["id"]
        resp = client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("test.md", io.BytesIO(b"# Markdown"), "text/markdown")},
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_upload_invalid_type(self, client, admin_headers, test_kb):
        kb_id = test_kb["id"]
        resp = client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("test.exe", io.BytesIO(b"binary"), "application/octet-stream")},
            headers=admin_headers,
        )
        assert resp.status_code == 400
        assert "格式" in resp.json()["detail"]

    def test_upload_non_admin(self, client, user_headers, test_kb):
        kb_id = test_kb["id"]
        resp = client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
            headers=user_headers,
        )
        assert resp.status_code == 403

    def test_upload_with_tags(self, client, admin_headers, test_kb):
        kb_id = test_kb["id"]
        resp = client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id, "tags": "重要,2026"},
            files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")},
            headers=admin_headers,
        )
        assert resp.status_code == 201

    def test_list_documents(self, client, admin_headers, test_kb):
        kb_id = test_kb["id"]
        client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("a.txt", io.BytesIO(b"aaa"), "text/plain")},
            headers=admin_headers,
        )
        client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("b.txt", io.BytesIO(b"bbb"), "text/plain")},
            headers=admin_headers,
        )

        resp = client.get(f"/api/v1/documents?kb_id={kb_id}", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_list_documents_filter_by_status(self, client, admin_headers, test_kb):
        kb_id = test_kb["id"]
        client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("a.txt", io.BytesIO(b"aaa"), "text/plain")},
            headers=admin_headers,
        )
        resp = client.get(f"/api/v1/documents?kb_id={kb_id}&status=pending", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 0

        resp = client.get(f"/api/v1/documents?kb_id={kb_id}&status=completed", headers=admin_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_delete_document(self, client, admin_headers, test_kb):
        kb_id = test_kb["id"]
        create = client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("test.txt", io.BytesIO(b"delete me"), "text/plain")},
            headers=admin_headers,
        )
        doc_id = create.json()["doc_id"]

        resp = client.delete(f"/api/v1/documents/{doc_id}", headers=admin_headers)
        assert resp.status_code == 204

        resp = client.get(f"/api/v1/documents?kb_id={kb_id}", headers=admin_headers)
        assert len(resp.json()) == 0

    def test_delete_document_not_found(self, client, admin_headers):
        resp = client.delete("/api/v1/documents/999", headers=admin_headers)
        assert resp.status_code == 404

    def test_upload_large_file_rejected(self, client, admin_headers, test_kb):
        kb_id = test_kb["id"]
        big = b"x" * (1024 * 1024 * 1024 + 1)
        resp = client.post(
            "/api/v1/documents/upload",
            data={"kb_id": kb_id},
            files={"file": ("big.txt", io.BytesIO(big), "text/plain")},
            headers=admin_headers,
        )
        assert resp.status_code == 400
