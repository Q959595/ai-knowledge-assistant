"""接口冒烟测试：验证 FastAPI 应用能正常启动、路由能访问。

运行方式（在项目根目录）:
    cd backend && python -m pytest ../tests -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)


def test_health():
    """健康检查接口应返回 ok。"""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_requires_file():
    """不带文件调用上传接口，应返回 422（参数校验失败）。"""
    r = client.post("/api/documents/upload")
    assert r.status_code == 422
