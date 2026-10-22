"""大模型客户端：封装 OpenAI 兼容接口。

只要服务商提供 OpenAI 兼容的接口（DeepSeek / Kimi / 通义千问 / OpenAI 等），
在 .env 里改 base_url、api_key、model 三个配置即可切换，业务代码不用动。
"""
from openai import OpenAI

from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE

_client = None  # 全局单例，避免每次请求都新建连接


def get_client() -> OpenAI:
    """惰性创建 OpenAI 客户端。"""
    global _client
    if _client is None:
        if not LLM_API_KEY:
            raise RuntimeError("未配置 LLM_API_KEY，请在项目根目录的 .env 中填写")
        _client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    return _client


def chat(messages: list[dict], temperature: float = LLM_TEMPERATURE) -> str:
    """调用大模型对话接口，返回回答文本。

    参数:
      messages: OpenAI 标准消息列表，如
                [{"role": "system", "content": "..."},
                 {"role": "user", "content": "..."}]
    """
    resp = get_client().chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()
