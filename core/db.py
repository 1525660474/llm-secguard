"""SQLite 数据层：负责建表与连接管理。

三张核心表：
- payloads  载荷库（攻击测试用例，每条含判定目标）
- models    被测模型配置（provider + 模型名 + API 地址）
- runs      运行记录（每一次「载荷 × 模型」的测试结果，含防护开关状态）
"""

import sqlite3
from contextlib import contextmanager

from core.config import BASE_DIR

DB_PATH = BASE_DIR / "data" / "secguard.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS payloads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT    NOT NULL UNIQUE,              -- 载荷编号，如 DI-001
    category    TEXT    NOT NULL,                     -- 类别，如 direct_injection
    name        TEXT    NOT NULL,                     -- 简短名称
    text        TEXT    NOT NULL,                     -- 载荷内容，{canary} 为占位符
    lang        TEXT    NOT NULL DEFAULT 'zh',        -- zh / en
    judge       TEXT    NOT NULL DEFAULT 'canary',    -- 判定方式：canary / regex / llm
    target      TEXT,                                 -- 判定目标（canary 值或正则）
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS models (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,              -- 显示名，如 DeepSeek-V3
    provider    TEXT    NOT NULL,                     -- deepseek / qwen / zhipu / ollama
    model_id    TEXT    NOT NULL,                     -- API 模型名，如 deepseek-chat
    base_url    TEXT    NOT NULL,
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    payload_id    INTEGER NOT NULL REFERENCES payloads(id),
    model_id      INTEGER NOT NULL REFERENCES models(id),
    mutation      TEXT    NOT NULL DEFAULT 'none',    -- 变异策略，如 base64
    guardrail_on  INTEGER NOT NULL DEFAULT 0,         -- 是否经过防护代理（W3 对比实验用）
    prompt        TEXT    NOT NULL,                   -- 实际发送的文本
    response      TEXT,                               -- 模型原始回复
    success       INTEGER,                            -- 1 攻击成功 / 0 失败 / NULL 待判定
    judge_method  TEXT,                               -- 实际使用的判定方式
    judge_reason  TEXT,                               -- 判定理由（LLM 裁判填写）
    latency_ms    INTEGER,
    error         TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_runs_model    ON runs(model_id);
CREATE INDEX IF NOT EXISTS idx_runs_payload  ON runs(payload_id);
CREATE INDEX IF NOT EXISTS idx_payloads_cat  ON payloads(category);
"""


@contextmanager
def get_db():
    """打开数据库连接，自动提交、自动关闭。用法：with get_db() as db: ..."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """创建所有表（已存在则跳过）。"""
    with get_db() as db:
        db.executescript(SCHEMA)
