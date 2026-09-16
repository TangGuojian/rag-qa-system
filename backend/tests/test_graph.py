import pytest
from unittest.mock import patch, MagicMock


class TestGraphAPI:
    def test_graph_data_no_auth(self, client):
        resp = client.get("/api/v1/graph/data")
        assert resp.status_code in (401, 403)

    def test_build_graph_no_auth(self, client):
        resp = client.post("/api/v1/graph/build")
        assert resp.status_code in (401, 403)

    def test_build_graph_non_admin(self, client, user_headers):
        resp = client.post("/api/v1/graph/build", headers=user_headers)
        assert resp.status_code == 403

    @patch("app.api.graph.run_build")
    def test_build_graph_success(self, mock_build, client, admin_headers):
        mock_build.return_value = None
        resp = client.post("/api/v1/graph/build", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "图谱构建完成"
