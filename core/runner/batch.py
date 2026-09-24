"""批量并发执行器（S9 + S10）。

- 并发只用于 HTTP 调用（asyncio + Semaphore 限流 + 失败重试一次）
- 结果统一收集后写库，避免 SQLite 并发写锁
- judge: llm 的载荷自动交给 LLM 裁判二次判定
"""

import asyncio

import httpx

from core.db import get_db
from core.judge.llm_judge import judge_async
from core.judge.rule_judge import judge
from core.mutators import apply_mutation
from core.providers.async_client import chat_completion_async
from core.runner.prompts import build_system_prompt, new_canary
from core.runner.runner import PROVIDER_KEYS


async def _run_one(client, sem, payload, model, mutation, guardrail_on, retry=1):
    async with sem:
        canary = new_canary()
        user_text = apply_mutation(payload["text"], mutation)
        messages = [
            {"role": "system", "content": build_system_prompt(payload["category"], canary)},
            {"role": "user", "content": user_text},
        ]
        api_key = PROVIDER_KEYS.get(model["provider"], "")

        result = {
            "payload_id": payload["id"],
            "model_id": model["id"],
            "mutation": mutation,
            "guardrail_on": guardrail_on,
            "prompt": user_text,
            "response": None,
            "success": None,
            "judge_method": None,
            "judge_reason": None,
            "latency_ms": None,
            "error": None,
            "code": payload["code"],
            "name": payload["name"],
            "category": payload["category"],
        }

        for attempt in range(retry + 1):
            try:
                response, latency_ms = await chat_completion_async(
                    client, model["base_url"], api_key, model["model_id"], messages
                )
                result["response"] = response
                result["latency_ms"] = latency_ms

                success, reason = judge(payload["judge"], payload["target"], response, canary)
                if success is None and payload["judge"] == "llm":
                    success, reason = await judge_async(
                        client,
                        model["base_url"],
                        api_key,
                        model["model_id"],
                        payload["text"],
                        response,
                        canary,
                    )
                result["success"] = success
                result["judge_method"] = payload["judge"]
                result["judge_reason"] = reason
                result["error"] = None
                break
            except Exception as exc:
                result["error"] = f"{type(exc).__name__}: {exc}"
                if attempt < retry:
                    await asyncio.sleep(2)

        return result


def run_batch(payloads, model, mutation="none", concurrency=5, guardrail_on=0) -> list[dict]:
    """批量执行并写入 runs 表，返回结果列表。"""

    async def _main():
        sem = asyncio.Semaphore(concurrency)
        async with httpx.AsyncClient() as client:
            coros = [
                _run_one(client, sem, p, model, mutation, guardrail_on) for p in payloads
            ]
            results = []
            done = 0
            for coro in asyncio.as_completed(coros):
                result = await coro
                results.append(result)
                done += 1
                if result["error"]:
                    flag = "ERROR"
                elif result["success"] == 1:
                    flag = "攻破"
                elif result["success"] == 0:
                    flag = "守住"
                else:
                    flag = "跳过"
                print(
                    f"[{done:>3}/{len(payloads)}] {result['code']:<7} "
                    f"{result['name']:<16} {flag}"
                )
            return results

    results = asyncio.run(_main())

    with get_db() as db:
        for r in results:
            db.execute(
                """
                INSERT INTO runs (payload_id, model_id, mutation, guardrail_on, prompt,
                                  response, success, judge_method, judge_reason, latency_ms, error)
                VALUES (:payload_id, :model_id, :mutation, :guardrail_on, :prompt,
                        :response, :success, :judge_method, :judge_reason, :latency_ms, :error)
                """,
                r,
            )
    return results
