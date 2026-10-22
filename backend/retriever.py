"""检索器 v1：基于 BM25 的关键词检索（自己实现的算法，面试可讲）。

流程：
  1. 用 jieba 对用户问题和每个分块做中文分词；
  2. 统计每个词的 IDF（逆文档频率，衡量词在语料里的区分度）；
  3. 按 BM25 公式给每个分块打分，返回得分最高的 Top-K 个片段。

为什么用 BM25：
  - 纯关键词匹配会忽略"词频"和"罕见词的价值"，BM25 用两个参数修正：
    k1 控制词频的边际收益（不是出现越多分越高），b 对长文档做惩罚；
  - 效果稳定、实现简单、无额外依赖，适合作为项目第一版。
  后续可升级为向量检索（Embedding），见 README「优化方向」。

注意：当前实现每次查询会扫描全部分块，几百块规模没有问题；
      数据量变大后可改用 MySQL 全文索引或向量数据库。
"""
import math
from collections import Counter

import jieba

from db import query

K1 = 1.5   # BM25 词频饱和参数（越大词频影响越大）
B = 0.75   # BM25 文档长度归一化参数（越大长文档惩罚越大）


def _tokenize(text: str) -> list[str]:
    """jieba 中文分词：转小写并过滤空白。"""
    return [w.strip().lower() for w in jieba.lcut(text) if w.strip()]


def _bm25_score(query_tokens, chunk_tokens, doc_len, avg_dl, idf_map, k1=K1, b=B):
    """计算"一个查询"与"一个分块"的 BM25 相关性得分。"""
    freq = Counter(chunk_tokens)  # 每个词在该分块中出现的次数
    score = 0.0
    for t in set(query_tokens):  # 对查询中的每个词累加贡献
        if t not in idf_map or t not in freq:
            continue
        tf = freq[t]
        idf = idf_map[t]
        # BM25 核心公式：词频越大得分越高，但受 k1 限制不会无限增长；
        # 文档越长，b 参数会按比例惩罚得分
        score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_dl))
    return score


def retrieve(question: str, top_k: int = 3) -> list[dict]:
    """检索与问题最相关的 top_k 个分块。

    返回格式: [{"chunk_id": int, "document_id": int, "content": str, "score": float}]
    """
    chunks = query("SELECT id, document_id, content, token_count FROM chunks")
    if not chunks:
        return []

    # 预分词，并记录每个分块的长度（BM25 文档长度项用）
    for c in chunks:
        c["tokens"] = _tokenize(c["content"])
        c["doc_len"] = max(len(c["tokens"]), 1)

    avg_dl = sum(c["doc_len"] for c in chunks) / len(chunks)

    # 计算 IDF：df 是包含该词的分块数量
    df = Counter()
    for c in chunks:
        for t in set(c["tokens"]):
            df[t] += 1
    n = len(chunks)
    idf_map = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    q_tokens = _tokenize(question)
    scored = [
        (_bm25_score(q_tokens, c["tokens"], c["doc_len"], avg_dl, idf_map), c)
        for c in chunks
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    # 过滤得分 <= 0 的块（查询词一个都没命中）
    return [
        {
            "chunk_id": c["id"],
            "document_id": c["document_id"],
            "content": c["content"],
            "score": round(s, 4),
        }
        for s, c in scored[:top_k]
        if s > 0
    ]
