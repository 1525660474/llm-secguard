"""异步并发调用客户端：httpx.AsyncClient + Semaphore 限流。

配合 asyncio.as_completed 实现进度实时输出。
"""

import time

import httpx


async def chat_completion_async(
    client: httpx.AsyncClient,
    base_url: str,
    api_key: str,
    model_id: str,
    messages: list[dict],
    temperature: float = 0.0,
    timeout: float = 60.0,
) -> tuple[str, int]:
    """异步调用 /chat/completions，返回 (回复文本, 耗时毫秒)。失败抛异常。"""
    start = time.perf_counter()
    resp = await client.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model_id, "messages": messages, "temperature": temperature},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    latency_ms = int((time.perf_counter() - start) * 1000)
    return data["choices"][0]["message"]["content"], latency_ms
