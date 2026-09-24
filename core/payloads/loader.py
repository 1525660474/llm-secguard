"""载荷加载器：读取本目录下的 YAML 载荷文件并导入数据库。

设计约定：
- 载荷文本写的是"诱导模型泄露系统验证码"类指令，**不包含验证码本身**；
  验证码由 runner 在每次测试时随机生成并注入 system prompt（S6 实现）。
- 重复执行导入是安全的：按 code 覆盖更新（upsert）。
"""

from pathlib import Path

import yaml

from core.db import get_db

PAYLOAD_DIR = Path(__file__).resolve().parent
REQUIRED_FIELDS = ("code", "name", "text")


def load_records() -> list[dict]:
    """解析目录下所有 *.yaml，返回扁平的载荷记录列表。"""
    records: list[dict] = []
    for path in sorted(PAYLOAD_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        category = data["category"]
        for item in data["payloads"]:
            missing = [f for f in REQUIRED_FIELDS if not item.get(f)]
            if missing:
                raise ValueError(f"{path.name}: {item.get('code', '?')} 缺少必填字段 {missing}")
            records.append(
                {
                    "code": item["code"],
                    "category": category,
                    "name": item["name"],
                    "text": item["text"].strip(),
                    "lang": item.get("lang", "zh"),
                    "judge": item.get("judge", "canary"),
                    "target": item.get("target"),
                }
            )
    return records


def import_payloads() -> list[tuple[str, int]]:
    """把载荷导入数据库，返回 [(category, count), ...] 统计。"""
    records = load_records()
    with get_db() as db:
        for r in records:
            db.execute(
                """
                INSERT INTO payloads (code, category, name, text, lang, judge, target)
                VALUES (:code, :category, :name, :text, :lang, :judge, :target)
                ON CONFLICT(code) DO UPDATE SET
                    category = excluded.category,
                    name     = excluded.name,
                    text     = excluded.text,
                    lang     = excluded.lang,
                    judge    = excluded.judge,
                    target   = excluded.target,
                    enabled  = 1
                """,
                r,
            )

    stats: dict[str, int] = {}
    for r in records:
        stats[r["category"]] = stats.get(r["category"], 0) + 1
    return sorted(stats.items())
