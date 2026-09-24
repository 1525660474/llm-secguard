"""统计脚本：查看测试结果概览（按模型 / 变异 / 类别统计 ASR）。

用法：
    venv\\Scripts\\python scripts\\stats.py
    venv\\Scripts\\python scripts\\stats.py --mutation none
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import get_db


def main() -> None:
    parser = argparse.ArgumentParser(description="测试结果统计")
    parser.add_argument("--mutation", type=str, default=None, help="只看某个变异策略")
    args = parser.parse_args()

    with get_db() as db:
        sql = """
            SELECT m.name AS model, r.mutation, r.guardrail_on, p.category,
                   COUNT(*) AS total,
                   SUM(CASE WHEN r.success = 1 THEN 1 ELSE 0 END) AS hit,
                   SUM(CASE WHEN r.success = 0 THEN 1 ELSE 0 END) AS miss,
                   SUM(CASE WHEN r.success IS NULL THEN 1 ELSE 0 END) AS skipped
            FROM runs r
            JOIN payloads p ON p.id = r.payload_id
            JOIN models m ON m.id = r.model_id
        """
        params: list = []
        if args.mutation:
            sql += " WHERE r.mutation = ?"
            params.append(args.mutation)
        sql += " GROUP BY m.name, r.mutation, r.guardrail_on, p.category ORDER BY m.name, r.mutation, r.guardrail_on, p.category"
        rows = db.execute(sql, params).fetchall()

        if not rows:
            print("[!] runs 表还没有数据，先运行 scripts/run_batch.py")
            raise SystemExit(0)

        header = (
            f"{'模型':<12} {'变异':<10} {'防护':<4} {'类别':<18} "
            f"{'总数':>4} {'攻破':>4} {'守住':>4} {'跳过':>4} {'ASR':>7}"
        )
        print(header)
        print("-" * len(header))

        total_hit = total_judged = 0
        for row in rows:
            hit = row["hit"] or 0
            miss = row["miss"] or 0
            skipped = row["skipped"] or 0
            judged = hit + miss
            asr = f"{hit / judged * 100:.1f}%" if judged else "-"
            guard = "开" if row["guardrail_on"] else "关"
            print(
                f"{row['model']:<12} {row['mutation']:<10} {guard:<4} {row['category']:<18} "
                f"{row['total']:>4} {hit:>4} {miss:>4} {skipped:>4} {asr:>7}"
            )
            total_hit += hit
            total_judged += judged

        if total_judged:
            print("-" * len(header))
            print(
                f"{'总体':<12} {'':<10} {'':<4} {'':<18} {'':>4} {total_hit:>4} "
                f"{total_judged - total_hit:>4} {'':>4} {total_hit / total_judged * 100:>6.1f}%"
            )


if __name__ == "__main__":
    main()
