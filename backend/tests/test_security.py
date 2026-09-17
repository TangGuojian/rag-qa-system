"""安全相关回归用例。

背景：早期版本存在两处典型安全问题，这里用测试锁死修复结果，防止回退。
1. JWT 密钥使用写死的默认值（"change-this-in-production"），
   任何人拿到源码即可用已知密钥伪造管理员令牌。
2. POST /api/v1/auth/init 无需登录且明文回传默认口令。
"""

from app.core.config import Settings


def _settings(**overrides):
    # 显式禁用 .env，保证断言不受本地配置影响
    return Settings(_env_file=None, **overrides)


class TestJwtSecretKey:
    def test_default_is_random_not_hardcoded(self):
        """未配置时每次实例化都应得到不同的随机密钥。"""
        first, second = _settings(), _settings()
        assert first.jwt_secret_key != second.jwt_secret_key
        assert len(first.jwt_secret_key) >= 32
        assert first.jwt_secret_key != "change-this-in-production"

    def test_ephemeral_flag_reflects_explicit_config(self):
        assert _settings().jwt_using_ephemeral_key is True
        assert _settings(jwt_secret_key="explicitly-set").jwt_using_ephemeral_key is False


class TestInitAdminEndpoint:
    def test_closed_by_default(self, client):
        resp = client.post("/api/v1/auth/init")
        assert resp.status_code == 403

    def test_password_not_leaked(self, client):
        from unittest.mock import patch
        from app.core.config import settings

        with patch.object(settings, "allow_init_admin", True):
            resp = client.post("/api/v1/auth/init")
        assert resp.status_code == 200
        assert "password" not in resp.json()
