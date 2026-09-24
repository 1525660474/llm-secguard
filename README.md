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
- [ ] S5 规则判定器
- [ ] S6 单链路 runner
- [ ] S7 README / 首次推送

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
```

## 架构

（开发中，W1 完成后补充架构图）
