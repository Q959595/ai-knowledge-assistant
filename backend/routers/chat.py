"""对话接口：会话管理 + 基于知识库的问答（RAG 核心链路）。

问答流程（重点考察点：能读懂 AI 生成的代码、能拆步骤、能调接口）：
  1. 校验会话存在；
  2. 用检索器从知识库找出与问题最相关的 Top-K 分块；
  3. 把分块拼进 system/user 提示词，调用大模型生成回答；
  4. 把用户问题和回答写入 messages 表（同一事务），并刷新会话更新时间。
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import TOP_K
from db import execute, get_conn, query
from llm_client import chat
from retriever import retrieve

router = APIRouter(prefix="/api", tags=["chat"])


# ---------- 请求体模型（Pydantic 自动做参数校验） ----------
class ConversationCreate(BaseModel):
    title: str = "新对话"


class ChatRequest(BaseModel):
    conversation_id: int
    question: str


# ---------- 会话管理 ----------
@router.post("/conversations")
def create_conversation(body: ConversationCreate):
    """新建一个对话。"""
    conv_id = execute("INSERT INTO conversations (title) VALUES (%s)", (body.title,))
    return {"conversation_id": conv_id, "title": body.title}


@router.get("/conversations")
def list_conversations():
    """会话列表（含每个会话的消息数，按最近更新时间倒序）。"""
    return query(
        "SELECT c.id, c.title, c.created_at, "
        "(SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS msg_count "
        "FROM conversations c "
        "ORDER BY c.updated_at DESC"
    )


@router.get("/conversations/{conversation_id}/messages")
def list_messages(conversation_id: int):
    """某个会话的全部历史消息。"""
    return query(
        "SELECT id, role, content, created_at FROM messages "
        "WHERE conversation_id=%s ORDER BY id",
        (conversation_id,),
    )


# ---------- 核心问答 ----------
@router.post("/chat")
def chat_with_kb(body: ChatRequest):
    """基于知识库的问答：检索 → 拼提示词 → 大模型生成 → 存历史。"""
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    conv = query(
        "SELECT id FROM conversations WHERE id=%s", (body.conversation_id,), one=True
    )
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 1. 检索相关知识片段
    sources = retrieve(question, TOP_K)
    if sources:
        context = "\n\n".join(
            f"【片段{i + 1}】\n{s['content']}" for i, s in enumerate(sources)
        )
    else:
        context = "（知识库中未找到相关内容，请如实告知用户并建议其补充资料。）"

    # 2. 拼提示词：把检索结果作为上下文交给大模型，避免它凭空编造
    system_prompt = (
        "你是一个基于内部知识库的智能问答助手。"
        "请优先依据提供的资料片段回答；资料不足时明确说明，并给出通用建议。"
        "回答使用简体中文，条理清晰。"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"资料片段：\n{context}\n\n用户问题：{question}"},
    ]

    # 3. 调用大模型（失败时给出明确提示，而不是 500 裸错误）
    try:
        answer = chat(messages)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"调用大模型失败：{e}")

    # 4. 用户问题 + 回答一起写入数据库（同一事务）
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (conversation_id, role, content) "
                "VALUES (%s, 'user', %s)",
                (body.conversation_id, question),
            )
            cur.execute(
                "INSERT INTO messages (conversation_id, role, content) "
                "VALUES (%s, 'assistant', %s)",
                (body.conversation_id, answer),
            )
            cur.execute(
                "UPDATE conversations SET updated_at = NOW() WHERE id=%s",
                (body.conversation_id,),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "answer": answer,
        "sources": [
            {"document_id": s["document_id"], "content": s["content"]} for s in sources
        ],
    }
