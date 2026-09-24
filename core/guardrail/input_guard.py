"""输入侧防护：识别提示词注入 / 越狱 / 编码绕过 / 已知载荷变体。

三层检测：
1. 归一化：剥离零宽字符，尝试 Base64 / Hex / ROT13 解码
2. 规则层：注入/越狱/套取机密等特征正则
3. 相似度层：与载荷库做字符 3-gram Jaccard 相似度（轻量"签名匹配"）
"""

import base64
import codecs
import re
from dataclasses import dataclass, field

from core.db import get_db

ZERO_WIDTH = "\u200b\u200c\u200d\ufeff"
SIM_THRESHOLD = 0.62

RULE_PATTERNS: list[tuple[str, str]] = [
    (r"忽略.{0,8}(之前|上面|以上|所有|一切).{0,6}(指令|规则|要求)", "忽略指令"),
    (r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions", "忽略指令(EN)"),
    (r"(系统|内部).{0,4}验证码|verification\s+code", "索取验证码"),
    (r"系统提示|system\s*prompt|初始指令|初始消息|system\s*message", "套取系统提示"),
    (r"(逐字|原样|完整|一字不漏).{0,10}(重复|输出|复述|引用|重述)", "套取原文"),
    (r"开发者模式|developer\s+mode|\bDAN\b|越狱", "越狱模式"),
    (r"(没有任何|不受|无).{0,6}限制.{0,8}(AI|助手|模型|机器人)", "无限制角色扮演"),
    (r"(base64|rot13|十六进制|hex).{0,16}(解码|decode)", "编码指令要求"),
    (r"解码.{0,12}(执行|指令)", "编码指令要求"),
    (r"(机密|密码|密钥|口令).{0,10}(告诉|输出|泄露|提供)", "索取机密"),
]

COMPILED_RULES = [(re.compile(pattern, re.IGNORECASE), label) for pattern, label in RULE_PATTERNS]

_CORPUS_CACHE: list[str] | None = None


@dataclass
class InputCheck:
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)
    decoded_texts: list[str] = field(default_factory=list)
    similarity: float = 0.0


def normalize(text: str) -> str:
    """剥离零宽字符。"""
    return "".join(ch for ch in text if ch not in ZERO_WIDTH)


def decode_variants(text: str) -> list[str]:
    """尝试还原常见编码（Base64 / Hex / ROT13），返回可能含明文的候选文本。"""
    variants: list[str] = []
    for token in re.findall(r"[A-Za-z0-9+/]{16,}={0,2}", text):
        try:
            decoded = base64.b64decode(token + "=" * (-len(token) % 4)).decode("utf-8")
            if len(decoded) >= 8 and decoded.isprintable():
                variants.append(decoded)
        except Exception:
            pass
    for token in re.findall(r"\b[0-9a-fA-F]{24,}\b", text):
        try:
            decoded = bytes.fromhex(token).decode("utf-8")
            if len(decoded) >= 8 and decoded.isprintable():
                variants.append(decoded)
        except Exception:
            pass
    variants.append(codecs.decode(text, "rot_13"))
    return variants


def _payload_corpus() -> list[str]:
    global _CORPUS_CACHE
    if _CORPUS_CACHE is None:
        with get_db() as db:
            rows = db.execute("SELECT text FROM payloads WHERE enabled = 1").fetchall()
        _CORPUS_CACHE = [row["text"] for row in rows]
    return _CORPUS_CACHE


def _ngrams(text: str, n: int = 3) -> set[str]:
    cleaned = re.sub(r"\s+", "", text)
    if len(cleaned) < n:
        return {cleaned}
    return {cleaned[i : i + n] for i in range(len(cleaned) - n + 1)}


def max_similarity(text: str) -> float:
    """与载荷库的字符 3-gram Jaccard 最大相似度。"""
    grams = _ngrams(text)
    if not grams:
        return 0.0
    best = 0.0
    for ref in _payload_corpus():
        ref_grams = _ngrams(ref)
        inter = len(grams & ref_grams)
        if inter:
            score = inter / len(grams | ref_grams)
            if score > best:
                best = score
    return best


def check_input(text: str) -> InputCheck:
    """检测用户输入；blocked=True 表示应拦截。"""
    result = InputCheck()
    normalized = normalize(text)
    candidates = [text, normalized, *decode_variants(normalized)]
    result.decoded_texts = candidates[2:]

    for candidate in candidates:
        for pattern, label in COMPILED_RULES:
            if pattern.search(candidate) and label not in result.reasons:
                result.reasons.append(label)

    result.similarity = max_similarity(normalized)
    if result.similarity >= SIM_THRESHOLD:
        result.reasons.append(f"与已知载荷相似度 {result.similarity:.0%}")

    result.blocked = bool(result.reasons)
    return result
