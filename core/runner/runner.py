"""单链路执行器：一条载荷 × 一个模型 → 调用 → 判定 → 写入 runs 表。"""

from core.config import DEEPSEEK_API_KEY
from core.db import get_db
from core.judge.rule_judge import judge
from core.providers.client import chat_completion
from core.runner.prompts import build_system_prompt, new_canary

PROVIDER_KEYS = {
    "deepseek": DEEPSEEK_API_KEY,
}


def ensure_model(name: str, provider: str, model_id: str, base_url: str) -> int:
    """确保 models 表中存在该模型，返回其 id。"""
    with get_db() as db:
        row = db.execute("SELECT id FROM models WHERE name = ?", (name,)).fetchone()
        if row:
            return row["id"]
        cur = db.execute(
            "INSERT INTO models (name, provider, model_id, base_url) VALUES (?, ?, ?, ?)",
            (name, provider, model_id, base_url),
        )
        return cur.lastrowid


def run_payload(payload, model) -> dict:
    """执行一条载荷。payload / model 为 sqlite3.Row，结果写入 runs 表并返回。"""
    canary = new_canary()
    messages = [
        {"role": "system", "content": build_system_prompt(payload["category"], canary)},
        {"role": "user", "content": payload["text"]},
    ]

    result = {
        "payload_id": payload["id"],
        "model_id": model["id"],
        "mutation": "none",
        "guardrail_on": 0,
        "prompt": payload["text"],
        "response": None,
        "success": None,
        "judge_method": None,
        "judge_reason": None,
        "latency_ms": None,
        "error": None,
    }

    try:
        response, latency_ms = chat_completion(
            model["base_url"],
            PROVIDER_KEYS.get(model["provider"], ""),
            model["model_id"],
            messages,
        )
        result["response"] = response
        result["latency_ms"] = latency_ms
        success, reason = judge(payload["judge"], payload["target"], response, canary)
        result["success"] = success
        result["judge_method"] = payload["judge"]
        result["judge_reason"] = reason
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    with get_db() as db:
        db.execute(
            """
            INSERT INTO runs (payload_id, model_id, mutation, guardrail_on, prompt,
                              response, success, judge_method, judge_reason, latency_ms, error)
            VALUES (:payload_id, :model_id, :mutation, :guardrail_on, :prompt,
                    :response, :success, :judge_method, :judge_reason, :latency_ms, :error)
            """,
            result,
        )
    return result
