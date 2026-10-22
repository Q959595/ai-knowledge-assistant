"""FastAPI 入口：创建应用、注册路由、配置跨域。

启动方式（在 backend 目录下）:
    uvicorn main:app --reload --port 8000
启动后访问 http://127.0.0.1:8000/docs 可查看自动生成的接口文档（Swagger）。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat, documents

app = FastAPI(
    title="AI 知识库问答助手",
    description="上传文档建立私有知识库，基于大模型做智能问答（RAG）",
    version="1.0.0",
)

# 跨域配置：允许 Vite 开发服务器（前端）访问后端
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由模块
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    """健康检查接口：验证服务是否正常启动。"""
    return {"status": "ok", "service": "ai-knowledge-assistant"}
