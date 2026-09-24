"""OpenAI 兼容接口调用客户端（httpx 同步版）。

目前所有支持的厂商（DeepSeek / 通义 / 智谱 / Ollama）都兼容
POST {base_url}/chat/completions 接口，因此一个函数即可覆盖。
W2 会扩展为异步并发版本。
"""

import time

import httpx


def chat_completion(
    base_url: str,
    api_key: str,
    model_id: str,
    messages: list[dict],
    temperature: float = 0.0,
    timeout: float = 60.0,
) -> tuple[str, int]:
    """调用 /chat/completions，返回 (回复文本, 耗时毫秒)。失败抛异常，由调用方捕获。"""
    start = time.perf_counter()
    resp = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model_id, "messages": messages, "temperature": temperature},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    latency_ms = int((time.perf_counter() - start) * 1000)
    return data["choices"][0]["message"]["content"], latency_ms
