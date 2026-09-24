"""误报率测试：用正常用户问题跑输入防护，统计误拦截比例。

用法：
    venv\\Scripts\\python scripts\\test_false_positive.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.guardrail.input_guard import check_input

QUESTIONS_PATH = (
    Path(__file__).resolve().parent.parent / "core" / "guardrail" / "benign_questions.txt"
)


def main() -> None:
    questions = [
        line.strip()
        for line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    blocked: list[tuple[str, list[str]]] = []
    for question in questions:
        check = check_input(question)
        if check.blocked:
            blocked.append((question, check.reasons))

    rate = len(blocked) / len(questions) * 100 if questions else 0.0
    print(f"[+] 正常问题 {len(questions)} 条，误拦截 {len(blocked)} 条，误报率 {rate:.1f}%")
    for question, reasons in blocked:
        print(f"    - {question}  <- {'；'.join(reasons)}")


if __name__ == "__main__":
    main()
