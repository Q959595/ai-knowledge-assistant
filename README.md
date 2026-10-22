# AI 知识库问答助手（RAG 应用）

基于大模型的私有知识库问答系统：上传文档 → 自动分块入库 → 提问时检索最相关内容 → 调用大模型生成回答。前后端分离，检索算法（BM25）完全自研实现。

> 简历项目・AI agent 应用开发实习生岗位・完整可运行的第一版（v1）

## 功能特性



* 📄 文档上传与解析：支持 `.txt` / `.md` / `.pdf`

* 🧩 中文文本分块：jieba 分词 + 自定义分块（含重叠衔接）

* 🔍 自研 BM25 相关性检索：不依赖第三方搜索库，面试可讲清原理

* 🤖 接入 OpenAI 兼容大模型：DeepSeek / Kimi / 通义千问可切换

* 💬 多会话管理、问答历史持久化

* 🗄️ MySQL 存储：文档、分块、会话、消息四张表（外键 + 索引 + 事务）

## 技术栈



| 层级  | 技术                                  | 说明                       |
| --- | ----------------------------------- | ------------------------ |
| 前端  | Vue 3 + Vite + Element Plus + Axios | 单页应用，页面与交互               |
| 后端  | Python FastAPI + Uvicorn            | REST API，自动生成 Swagger 文档 |
| 检索  | jieba 分词 + 自实现 BM25 算法              | 相关性排序取 Top-K             |
| 大模型 | OpenAI 兼容接口                         | 生成最终回答                   |
| 数据库 | MySQL 8                             | 四张表，外键级联、事务保证一致性         |

## 项目结构



```
ai-knowledge-assistant/

├── backend/                 # 后端

│   ├── main.py              # FastAPI 入口（注册路由 / 跨域）

│   ├── config.py            # 配置读取（.env）

│   ├── db.py                # pymysql 轻量封装（参数化 SQL，防注入）

│   ├── text\_splitter.py     # 文档分块算法

│   ├── retriever.py         # BM25 检索器（自研）

│   ├── llm\_client.py        # 大模型客户端（OpenAI 兼容）

│   └── routers/

│       ├── documents.py     # 文档上传 / 列表 / 删除

│       └── chat.py          # 会话管理 / 问答

├── frontend/                # 前端（Vue3 + Vite）

│   └── src/

│       ├── main.js          # 入口

│       ├── api.js           # axios 封装

│       └── App.vue          # 主页面（对话 + 知识库管理）

├── tests/                   # pytest 单元测试 / 接口冒烟测试

├── schema.sql               # 建库建表脚本

├── .env.example             # 环境变量模板（复制为 .env 填写）

├── requirements.txt         # Python 依赖

└── .gitignore
```

## 快速开始

**环境要求**：Python 3.10+、Node.js 18+、MySQL 5.7+/8.0



1. **初始化数据库**



```
mysql -u root -p < schema.sql
```



1. **配置环境变量**



```
cp .env.example .env   # Windows: copy .env.example .env
```

填写 `.env` 里的数据库密码和大模型 API Key（DeepSeek 注册即送额度）。



1. **启动后端**（端口 8000）



```
pip install -r requirements.txt

cd backend

uvicorn main:app --reload --port 8000
```

浏览器打开 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 可查看接口文档。



1. **启动前端**（端口 5173）



```
cd frontend

npm install

npm run dev
```

浏览器打开 [http://localhost:5173](http://localhost:5173) ，先「知识库管理」上传文档，再新建对话提问。

## API 一览



| 方法     | 路径                               | 说明                        |
| ------ | -------------------------------- | ------------------------- |
| POST   | /api/documents/upload            | 上传文档（multipart/form-data） |
| GET    | /api/documents                   | 文档列表（含分块数）                |
| DELETE | /api/documents/{id}              | 删除文档（分块级联删除）              |
| POST   | /api/conversations               | 新建会话                      |
| GET    | /api/conversations               | 会话列表                      |
| GET    | /api/conversations/{id}/messages | 会话历史消息                    |
| POST   | /api/chat                        | 问答（检索 + 大模型生成）            |

## 运行测试



```
cd backend

python -m pytest ../tests -v
```

## 核心设计说明（面试可讲）



1. **为什么要分块**：大模型上下文有限，检索需要 "小而准" 的单元；500 字符 + 50 重叠防止关键句被切断。

2. **BM25 为什么比关键词匹配好**：词频不是越高越好（k1 饱和），长文档要惩罚（b 归一化），罕见词权重更高（IDF）—— 三点都能展开讲。

3. **事务保证一致性**：上传文档时 "文档记录 + 全部分块" 在同一事务提交，任一步失败整体回滚，不会出现半截数据。

4. **SQL 基本功**：LEFT JOIN + GROUP BY + 子查询统计消息数；外键 ON DELETE CASCADE 级联清理；高频查询列建索引。

5. **参数化 SQL**：所有语句用 `%s` 占位，防 SQL 注入（面试安全题常问）。

## 后续优化方向



* [ ] 向量检索：接入 Embedding + 向量库，语义召回更强

* [ ] 用户登录与权限隔离

* [ ] 流式输出（SSE），回答逐字显示

* [ ] Docker + docker-compose 一键部署

* [ ] 前端展示回答引用的知识片段

## 常见问题



| 问题          | 解决                                                                   |
| ----------- | -------------------------------------------------------------------- |
| 端口 8000 被占用 | 换端口：`uvicorn main:app --reload --port 8001`，并同步改 `vite.config.js` 代理 |
| 中文乱码        | 确认建库使用 utf8mb4（schema.sql 已设置）；`.env` 密码含特殊字符时注意转义                   |
| 调用大模型报错     | 检查 `.env` 的 base\_url /api\_key/model 是否与服务商匹配；DeepSeek 需先在官网充值      |