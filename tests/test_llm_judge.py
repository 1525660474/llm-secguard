"""LLM 裁判解析函数单元测试（不调用真实 API）。"""

from core.judge.llm_judge import parse_judge_reply


def test_parse_plain_json():
    success, reason = parse_judge_reply('{"success": true, "reason": "泄露了验证码"}')
    assert success == 1
    assert "泄露" in reason


def test_parse_json_with_noise():
    text = '判定如下：\n{"success": false, "reason": "模型拒绝回答"}\n以上。'
    success, reason = parse_judge_reply(text)
    assert success == 0
    assert "拒绝" in reason


def test_parse_string_boolean():
    success, _ = parse_judge_reply('{"success": "false", "reason": "无泄露"}')
    assert success == 0


def test_parse_bad_output():
    success, reason = parse_judge_reply("我无法判断这个结果")
    assert success is None
    assert "JSON" in reason


def test_parse_empty_output():
    success, _ = parse_judge_reply("")
    assert success is None
