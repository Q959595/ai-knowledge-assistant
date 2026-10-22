"""检索器单元测试：只测纯函数，不依赖数据库。

运行方式（在项目根目录）:
    cd backend && python -m pytest ../tests -v
"""
import sys
import os

# 把 backend 目录加入模块搜索路径，保证能 import retriever
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from retriever import _bm25_score, _tokenize  # noqa: E402


def test_tokenize_chinese():
    """中文分词应该能把关键词切出来。"""
    tokens = _tokenize("数据库事务是什么")
    assert "数据库" in tokens
    assert "事务" in tokens


def test_bm25_related_higher():
    """与查询词重叠越多的分块，BM25 得分应越高。"""
    idf = {"数据库": 1.2, "事务": 1.2, "索引": 1.0}
    score_related = _bm25_score(
        ["数据库", "事务"], ["数据库", "事务", "索引"], doc_len=3, avg_dl=3, idf_map=idf
    )
    score_unrelated = _bm25_score(
        ["数据库", "事务"], ["今天", "天气", "很好"], doc_len=3, avg_dl=3, idf_map=idf
    )
    assert score_related > score_unrelated
