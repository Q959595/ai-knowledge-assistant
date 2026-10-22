"""文本分块工具：把长文档按段落切分成固定大小的块，供检索使用。

为什么需要分块：
  大模型一次能接收的上下文有限，而且检索需要"小而准"的单元。
  把文档切成 500 字符左右的块，才能在提问时精确找到最相关的内容。
"""
import re


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """把一段长文本切成若干分块。

    参数:
      text:       原始文档全文
      chunk_size: 每个分块的目标字符数
      overlap:    相邻分块重叠的字符数（防止关键句子恰好被切在边界上）
    返回:
      分块字符串列表
    """
    # 防止 overlap 过大导致死循环
    overlap = max(0, min(overlap, chunk_size // 2))

    # 按换行切成段落（兼容空行分段），过滤空白段落
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    chunks: list[str] = []
    cur = ""

    for para in paragraphs:
        # 单个段落太长：先硬切，下一块从 overlap 处接续，保证衔接
        while len(para) > chunk_size:
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(para[:chunk_size])
            para = para[chunk_size - overlap:]

        # 正常段落：能并入当前块就并入，否则收尾当前块、另起新块
        if not cur:
            cur = para
        elif len(cur) + len(para) + 1 <= chunk_size:
            cur = f"{cur}\n{para}"
        else:
            chunks.append(cur)
            cur = para

    if cur:
        chunks.append(cur)
    return chunks
