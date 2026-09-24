"""S3 验证脚本：初始化数据库并打印表结构。

用法：
    venv\\Scripts\\python scripts\\init_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import DB_PATH, get_db, init_db

if __name__ == "__main__":
    init_db()
    print(f"[+] 数据库已初始化: {DB_PATH}")

    with get_db() as db:
        tables = [
            row["name"]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        print(f"[+] 表清单: {', '.join(tables)}")

        for table in ("payloads", "models", "runs"):
            count = db.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
            print(f"    - {table:<8} 字段数 {len(db.execute(f'PRAGMA table_info({table})').fetchall())}，当前 {count} 条记录")
