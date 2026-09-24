"""S6：单链路测试。取 N 条未测试载荷，调用 DeepSeek，判定并写入数据库。

用法：
    venv\\Scripts\\python scripts\\run_once.py --limit 10
    venv\\Scripts\\python scripts\\run_once.py --category unsafe_output --limit 5
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from core.db import get_db
from core.runner.runner import ensure_model, run_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="单链路攻击测试")
    parser.add_argument("--limit", type=int, default=10, help="本次测试载荷条数")
    parser.add_argument("--category", type=str, default=None, help="只测某个类别")
    args = parser.parse_args()

    model_id = ensure_model("DeepSeek-V3", "deepseek", DEEPSEEK_MODEL, DEEPSEEK_BASE_URL)

    with get_db() as db:
        model = db.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()
        sql = """
            SELECT * FROM payloads
            WHERE enabled = 1
              AND id NOT IN (SELECT payload_id FROM runs WHERE model_id = ?)
        """
        params: list = [model_id]
        if args.category:
            sql += " AND category = ?"
            params.append(args.category)
        sql += " ORDER BY id LIMIT ?"
        params.append(args.limit)
        payloads = db.execute(sql, params).fetchall()

    if not payloads:
        print("[!] 没有待测试的载荷（都测过了，或换一个 --category）")
        return

    hit = miss = skipped = 0
    for i, payload in enumerate(payloads, 1):
        result = run_payload(payload, model)
        if result["error"]:
            status = f"ERROR {result['error'][:60]}"
        elif result["success"] == 1:
            status = f"攻破（{result['judge_reason']}）"
            hit += 1
        elif result["success"] == 0:
            status = "守住"
            miss += 1
        else:
            status = f"跳过（{result['judge_reason']}）"
            skipped += 1
        print(f"[{i:>2}/{len(payloads)}] {payload['code']:<7} {payload['name']:<16} {status}")

    print(f"\n[+] 本次结果：攻破 {hit} / 守住 {miss} / 跳过 {skipped}")


if __name__ == "__main__":
    main()
