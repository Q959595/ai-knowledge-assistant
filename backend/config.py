"""全局配置：从项目根目录的 .env 文件读取，统一管理所有可配置项。

这样做的目的：
  1. 数据库密码、API Key 等敏感信息不写死在代码里，上传 GitHub 时不会泄露；
  2. 换一台机器 / 换一个模型，只需改 .env，不用动代码。
"""
import os

from dotenv import load_dotenv

# 读取项目根目录的 .env（backend 目录的上一级）
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# ---------- 数据库配置 ----------
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_kb")

# ---------- 大模型配置（OpenAI 兼容接口，可切换 DeepSeek / Kimi / 通义千问等） ----------
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# ---------- 检索参数 ----------
TOP_K = int(os.getenv("TOP_K", "3"))            # 每次提问返回最相关的几个分块
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))     # 每个分块的目标字符数
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))  # 相邻分块重叠字符数
