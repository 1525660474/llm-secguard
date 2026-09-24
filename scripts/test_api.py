"""S2 验证脚本：调用一次 DeepSeek 接口，确认 Key、网络、JSON 解析全链路可用。

用法：
    venv\\Scripts\\python scripts\\test_api.py
"""

import sys
from pathlib import Path

# 让脚本能 import 项目根目录下的 core 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from core.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


def chat(prompt: str) -> str:
    """发送一条消息给模型，返回文本回复。"""
    response = httpx.post(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    if not DEEPSEEK_API_KEY:
        print("[!] 未找到 DEEPSEEK_API_KEY")
        print("    请把 .env.example 复制为 .env，并填入你的 DeepSeek API Key")
        sys.exit(1)

    reply = chat("用一句话介绍你自己")
    print("[+] API 调通，模型回复：")
    print(reply)
