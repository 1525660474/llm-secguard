"""统计脚本：查看测试结果概览（按模型 / 类别统计 ASR）。

用法：
    venv\\Scripts\\python scripts\\stats.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import get_db

if __name__ == "__main__":
    with get_db() as db:
        rows = db.execute(
            """
            SELECT m.name AS model, p.category,
                   COUNT(*) AS total,
                   SUM(CASE WHEN r.success = 1 THEN 1 ELSE 0 END) AS hit,
                   SUM(CASE WHEN r.success = 0 THEN 1 ELSE 0 END) AS miss,
                   SUM(CASE WHEN r.success IS NULL THEN 1 ELSE 0 END) AS skipped
            FROM runs r
            JOIN payloads p ON p.id = r.payload_id
            JOIN models m ON m.id = r.model_id
            GROUP BY m.name, p.category
            ORDER BY m.name, p.category
            """
        ).fetchall()

        if not rows:
            print("[!] runs 表还没有数据，先运行 scripts/run_once.py")
            raise SystemExit(0)

        header = f"{'模型':<12} {'类别':<18} {'总数':>4} {'攻破':>4} {'守住':>4} {'跳过':>4} {'ASR':>7}"
        print(header)
        print("-" * len(header))

        total_hit = total_judged = 0
        for row in rows:
            hit = row["hit"] or 0
            miss = row["miss"] or 0
            skipped = row["skipped"] or 0
            judged = hit + miss
            asr = f"{hit / judged * 100:.1f}%" if judged else "-"
            print(
                f"{row['model']:<12} {row['category']:<18} {row['total']:>4} "
                f"{hit:>4} {miss:>4} {skipped:>4} {asr:>7}"
            )
            total_hit += hit
            total_judged += judged

        if total_judged:
            print("-" * len(header))
            print(f"{'总体':<12} {'':<18} {'':>4} {total_hit:>4} {total_judged - total_hit:>4} "
                  f"{'':>4} {total_hit / total_judged * 100:>6.1f}%")
