-- AI 知识库问答助手 数据库初始化脚本
-- 用法: mysql -u root -p < schema.sql
-- 演示了: 建表、主键、外键（级联删除）、索引、枚举字段

CREATE DATABASE IF NOT EXISTS ai_kb
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ai_kb;

-- 1. 文档表：记录每份上传的文档
CREATE TABLE IF NOT EXISTS documents (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  title       VARCHAR(255) NOT NULL COMMENT '原始文件名',
  file_name   VARCHAR(255) NOT NULL COMMENT '服务器保存名（uuid 前缀，防重名）',
  file_type   VARCHAR(20)  DEFAULT '' COMMENT '扩展名',
  file_size   INT          DEFAULT 0 COMMENT '字节数',
  status      VARCHAR(20)  DEFAULT 'ready' COMMENT '处理状态',
  created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
  KEY idx_created (created_at)
) ENGINE = InnoDB;

-- 2. 文本分块表：文档被切成若干小块，供检索使用
CREATE TABLE IF NOT EXISTS chunks (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  document_id  INT NOT NULL,
  chunk_index  INT NOT NULL COMMENT '块序号（文档内从 0 开始）',
  content      TEXT NOT NULL,
  token_count  INT DEFAULT 0 COMMENT '分词后的词数（供 BM25 计算文档长度）',
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_doc (document_id),
  CONSTRAINT fk_chunk_doc FOREIGN KEY (document_id)
    REFERENCES documents (id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- 3. 会话表：一次对话
CREATE TABLE IF NOT EXISTS conversations (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  title       VARCHAR(255) DEFAULT '新对话',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_updated (updated_at)
) ENGINE = InnoDB;

-- 4. 消息表：会话里的每条问答（role 枚举限定只能存 user / assistant）
CREATE TABLE IF NOT EXISTS messages (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  conversation_id  INT NOT NULL,
  role             ENUM ('user', 'assistant') NOT NULL,
  content          TEXT NOT NULL,
  created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_conv (conversation_id),
  CONSTRAINT fk_msg_conv FOREIGN KEY (conversation_id)
    REFERENCES conversations (id) ON DELETE CASCADE
) ENGINE = InnoDB;
