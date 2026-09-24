"""S11：批量并发测试脚本。

用法：
    venv\\Scripts\\python scripts\\run_batch.py --limit 50
    venv\\Scripts\\python scripts\\run_batch.py --mutation base64 --limit 50
    venv\\Scripts\\python scripts\\run_batch.py --category jailbreak --concurrency 5
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from core.db import get_db
from core.mutators import MUTATORS
from core.runner.batch import run_batch
from core.runner.runner import ensure_model


def main() -> None:
    parser = argparse.ArgumentParser(description="批量并发攻击测试")
    parser.add_argument("--limit", type=int, default=50, help="本次测试上限")
    parser.add_argument("--category", type=str, default=None, help="只测某个类别")
    parser.add_argument(
        "--mutation",
        type=str,
        default="none",
        choices=["none", *MUTATORS.keys()],
        help="变异策略",
    )
    parser.add_argument("--concurrency", type=int, default=5, help="并发数")
    parser.add_argument("--guardrail", action="store_true", help="启用输入/输出防护")
    args = parser.parse_args()
    guardrail_on = 1 if args.guardrail else 0

    model_id = ensure_model("DeepSeek-V3", "deepseek", DEEPSEEK_MODEL, DEEPSEEK_BASE_URL)

    with get_db() as db:
        model = db.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()
        sql = """
            SELECT * FROM payloads
            WHERE enabled = 1
              AND id NOT IN (
                  SELECT payload_id FROM runs
                  WHERE model_id = ? AND mutation = ? AND guardrail_on = ?
              )
        """
        params: list = [model_id, args.mutation, guardrail_on]
        if args.category:
            sql += " AND category = ?"
            params.append(args.category)
        sql += " ORDER BY id LIMIT ?"
        params.append(args.limit)
        payloads = db.execute(sql, params).fetchall()

    if not payloads:
        print("[!] 没有待测试的载荷组合（试试换 --mutation / --category）")
        return

    print(
        f"[i] 待测 {len(payloads)} 条 | 模型 {model['name']} | "
        f"变异 {args.mutation} | 防护 {'开' if guardrail_on else '关'} | 并发 {args.concurrency}"
    )
    results = run_batch(
        payloads,
        model,
        mutation=args.mutation,
        concurrency=args.concurrency,
        guardrail_on=guardrail_on,
    )

    hit = sum(1 for r in results if r["success"] == 1)
    miss = sum(1 for r in results if r["success"] == 0)
    skipped = sum(1 for r in results if r["success"] is None and not r["error"])
    errors = sum(1 for r in results if r["error"])
    print(f"\n[+] 本次结果：攻破 {hit} / 守住 {miss} / 跳过 {skipped} / 失败 {errors}")


if __name__ == "__main__":
    main()
