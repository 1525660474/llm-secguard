"""导出 runs 记录为 CSV，用于人工抽检与裁判校准。

用法：
    venv\\Scripts\\python scripts\\export_runs.py --limit 50
    venv\\Scripts\\python scripts\\export_runs.py --category unsafe_output
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import BASE_DIR
from core.db import get_db

FIELDS = [
    "id", "code", "category", "model", "mutation", "guardrail_on",
    "success", "judge_method", "judge_reason", "prompt", "response",
    "latency_ms", "error", "created_at",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="导出测试记录为 CSV")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--category", type=str, default=None)
    parser.add_argument("--out", type=str, default=str(BASE_DIR / "data" / "exports" / "runs.csv"))
    args = parser.parse_args()

    sql = """
        SELECT r.id, p.code, p.category, m.name AS model, r.mutation, r.guardrail_on,
               r.success, r.judge_method, r.judge_reason, r.prompt, r.response,
               r.latency_ms, r.error, r.created_at
        FROM runs r
        JOIN payloads p ON p.id = r.payload_id
        JOIN models m ON m.id = r.model_id
    """
    params: list = []
    if args.category:
        sql += " WHERE p.category = ?"
        params.append(args.category)
    sql += " ORDER BY r.id DESC LIMIT ?"
    params.append(args.limit)

    with get_db() as db:
        rows = db.execute(sql, params).fetchall()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in FIELDS})

    print(f"[+] 已导出 {len(rows)} 条记录到 {out_path}")


if __name__ == "__main__":
    main()
