"""输出侧防护：对模型回复做泄露拦截与 PII 脱敏。

- 验证码泄露拦截（SECGUARD-XXXX-XXXX 格式）
- 密钥 / 手机号 / 证件号 / 邮箱脱敏
"""

import re
from dataclasses import dataclass, field

CANARY_RE = re.compile(r"SECGUARD-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}")
KEY_RE = re.compile(r"SK-[A-Za-z0-9-]{6,}")
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
ID_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

MASK_RULES = [
    (CANARY_RE, "验证码泄露已拦截", "[机密已拦截]", True),
    (KEY_RE, "密钥脱敏", "[密钥已脱敏]", False),
    (ID_RE, "证件号脱敏", "[证件号已脱敏]", False),
    (PHONE_RE, "手机号脱敏", "[手机号已脱敏]", False),
    (EMAIL_RE, "邮箱脱敏", "[邮箱已脱敏]", False),
]


@dataclass
class OutputCheck:
    text: str
    changed: bool = False
    leaked: bool = False
    reasons: list[str] = field(default_factory=list)


def check_output(text: str | None) -> OutputCheck:
    """对模型输出做脱敏；leaked=True 表示检测到验证码泄露并被拦截。"""
    result = OutputCheck(text=text or "")
    for pattern, label, replacement, is_leak in MASK_RULES:
        new_text, count = pattern.subn(replacement, result.text)
        if count:
            result.text = new_text
            result.changed = True
            result.reasons.append(f"{label} x{count}")
            if is_leak:
                result.leaked = True
    return result
