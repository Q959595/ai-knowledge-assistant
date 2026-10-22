"""文档管理接口：上传 / 列表 / 删除。

上传链路（重点考察点：把需求拆成 数据库 → 解析 → 分块 → 入库 步骤）：
  1. 读取上传文件原始字节；
  2. 按扩展名解析出纯文本（支持 txt / md / pdf）；
  3. 用 text_splitter 切成固定大小的分块；
  4. 在一个事务里写入 documents 表和 chunks 表 —— 任一步失败整体回滚，
     保证不会出现"文档记录有了但分块缺失"的半截数据。
"""
import io
import os
import uuid

import jieba
from fastapi import APIRouter, File, HTTPException, UploadFile

from config import CHUNK_OVERLAP, CHUNK_SIZE
from db import get_conn, query
from text_splitter import split_text

router = APIRouter(prefix="/api/documents", tags=["documents"])

# 上传文件的本地保存目录（backend/uploads），仅用于留底排查
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _extract_text(filename: str, raw: bytes) -> str:
    """按扩展名解析文件内容为纯文本。"""
    name = filename.lower()
    if name.endswith((".txt", ".md", ".markdown")):
        return raw.decode("utf-8", errors="ignore")
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    raise HTTPException(status_code=400, detail="仅支持 .txt / .md / .pdf 文件")


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    """上传文档并解析入库。"""
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="文件内容为空")

    text = _extract_text(file.filename, raw)
    if not text.strip():
        raise HTTPException(status_code=400, detail="未能从文件中解析出文本内容")

    chunks = split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    if not chunks:
        raise HTTPException(status_code=400, detail="文档太短，无法分块")

    # 原文件以 uuid 重命名保存，避免重名覆盖
    ext = os.path.splitext(file.filename)[1]
    saved_name = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, saved_name), "wb") as f:
        f.write(raw)

    # 事务：文档记录 + 所有分块，一起提交或一起回滚
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO documents (title, file_name, file_type, file_size, status) "
                "VALUES (%s, %s, %s, %s, 'ready')",
                (file.filename, saved_name, ext, len(raw)),
            )
            doc_id = cur.lastrowid
            for i, chunk in enumerate(chunks):
                # 顺便统计分块词数，供 BM25 计算文档长度项
                tokens = [w for w in jieba.lcut(chunk) if w.strip()]
                cur.execute(
                    "INSERT INTO chunks (document_id, chunk_index, content, token_count) "
                    "VALUES (%s, %s, %s, %s)",
                    (doc_id, i, chunk, len(tokens)),
                )
        conn.commit()
        return {"document_id": doc_id, "title": file.filename, "chunks": len(chunks)}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@router.get("")
def list_documents():
    """文档列表（含每个文档的分块数）。

    这里用到了 LEFT JOIN + GROUP BY + COUNT 的关联查询/聚合，是面试时
    可以主动讲解的 SQL 知识点。
    """
    return query(
        "SELECT d.id, d.title, d.file_type, d.file_size, d.status, d.created_at, "
        "COUNT(c.id) AS chunk_count "
        "FROM documents d "
        "LEFT JOIN chunks c ON c.document_id = d.id "
        "GROUP BY d.id "
        "ORDER BY d.created_at DESC"
    )


@router.delete("/{document_id}")
def delete_document(document_id: int):
    """删除文档；分块通过外键 ON DELETE CASCADE 自动级联删除。"""
    # 先查出服务器保存名，删除数据库记录后顺手清理本地文件
    doc = query(
        "SELECT file_name FROM documents WHERE id=%s", (document_id,), one=True
    )
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE id=%s", (document_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    try:
        os.remove(os.path.join(UPLOAD_DIR, doc["file_name"]))
    except OSError:
        pass  # 本地文件清理失败不影响主流程

    return {"deleted": document_id}
