"""W3 防护代理：OpenAI 兼容接口 + 输入/输出双向防护。

启动：
    venv\\Scripts\\python -m uvicorn proxy.app:app --host 0.0.0.0 --port 8000

客户端把 base_url 指向 http://127.0.0.1:8000/v1 即可透明使用。
"""

import time
import uuid

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from core.guardrail.input_guard import check_input
from core.guardrail.output_guard import check_output

app = FastAPI(title="LLM-SecGuard Guardrail Proxy")


def _completion_response(model: str, content: str) -> dict:
    """构造 OpenAI 兼容的补全返回体。"""
    return {
        "id": f"chatcmpl-guard-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])

    user_text = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            user_text = message.get("content", "")
            break

    check = check_input(user_text)
    if check.blocked:
        reason = "；".join(check.reasons)
        return _completion_response(
            body.get("model", "guarded"),
            f"抱歉，该请求触发了安全防护（{reason}），已被拦截。",
        )

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    async with httpx.AsyncClient() as client:
        upstream = await client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers=headers,
            json=body,
            timeout=90,
        )
    if upstream.status_code != 200:
        return JSONResponse(status_code=upstream.status_code, content=upstream.json())

    data = upstream.json()
    content = data["choices"][0]["message"]["content"]
    out = check_output(content)
    if out.changed:
        data["choices"][0]["message"]["content"] = out.text
    data["guardrail"] = {"changed": out.changed, "reasons": out.reasons}
    return data
