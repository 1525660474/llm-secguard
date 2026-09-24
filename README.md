# LLM-SecGuard 大模型安全评测与防护平台

> 对大模型进行自动化越狱 / Prompt 注入攻击测试，量化风险，并通过防护代理验证防御效果。

仓库地址：https://github.com/1525660474/llm-secguard

## 合规声明

本项目所有攻击载荷仅用于**授权的安全测试与学习研究**。载荷均采用无害化目标（canary 标记词），不包含真实有害内容，不针对任何真实线上系统。

## 项目进度

- [x] S1 环境搭建
- [x] S2 API 调通
- [x] S3 数据库设计
- [x] S4 载荷库 v1（6 类 137 条）
- [x] S5 规则判定器
- [x] S6 单链路 runner
- [x] S7 README / 首次推送

## 首批测试结果（18 次真实运行）

| 类别 | 测试数 | 攻破 | 守住 | 典型发现 |
|---|---|---|---|---|
| direct_injection | 10 | 0 | 10 | 基础指令覆盖均被拒绝 |
| sensitive_info | 3 | 0 | 3 | 拒绝泄露虚构 PII |
| unsafe_output | 5 | 3 | 2 | 直接输出 `onclick=` / `javascript:` / `document.cookie` 等危险代码 |

> 数据持续更新中，运行 `scripts/stats.py` 可复现统计口径。

## 快速开始

```powershell
# 1. 创建虚拟环境并安装依赖
py -m venv venv
venv\Scripts\python -m pip install -r requirements.txt

# 2. 配置密钥：复制 .env.example 为 .env，填入 DeepSeek API Key

# 3. 验证环境
venv\Scripts\python scripts\test_api.py

# 4. 初始化数据库
venv\Scripts\python scripts\init_db.py

# 5. 导入载荷库
venv\Scripts\python scripts\import_payloads.py

# 6. 运行单链路测试并查看统计
venv\Scripts\python scripts\run_once.py --limit 10
venv\Scripts\python scripts\stats.py
```

## 架构

（开发中，W1 完成后补充架构图）
