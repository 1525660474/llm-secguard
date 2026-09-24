"""S4：把 YAML 载荷库导入数据库。可重复执行（按 code 更新）。

用法：
    venv\\Scripts\\python scripts\\import_payloads.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import get_db
from core.payloads.loader import import_payloads

if __name__ == "__main__":
    stats = import_payloads()
    print("[+] 本次导入：")
    for category, count in stats:
        print(f"    - {category:<20} {count:>3} 条")

    with get_db() as db:
        total = db.execute("SELECT COUNT(*) AS c FROM payloads").fetchone()["c"]
        rows = db.execute(
            "SELECT category, COUNT(*) AS c FROM payloads GROUP BY category ORDER BY category"
        ).fetchall()

    print(f"[+] 数据库载荷总数：{total}")
    for row in rows:
        print(f"    - {row['category']:<20} {row['c']:>3} 条")
