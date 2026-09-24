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
- [x] S8 变异引擎（4 策略 + 单测）
- [x] S9 并发执行器（asyncio 限流 + 重试）
- [x] S10 LLM-as-judge（编码/分片类载荷判定）
- [x] S11 批量评测（685 次真实运行）
- [x] S12 防护代理（FastAPI，OpenAI 兼容接口）
- [x] S13 输入防护（规则 + 编码归一化 + 载荷相似度）
- [x] S14 输出防护（验证码拦截 + PII 脱敏）
- [x] S15 对比实验（防护前后 ASR + 误报率 + 泛化测试）

## 测试数据（W2 基线，DeepSeek-V3）

5 种变异策略 × 137 条载荷 = **685 次真实测试**，总体 ASR **11.2%**。

### 变异策略对比

| 变异策略 | 攻破/总数 | ASR |
|---|---|---|
| none（原始载荷） | 16/137 | 11.7% |
| roleplay（角色扮演包装） | 21/137 | 15.3% |
| base64（Base64 编码） | 15/137 | 10.9% |
| zero_width（零宽字符混淆） | 14/137 | 10.2% |
| hex（十六进制编码） | 11/137 | 8.0% |

### 分类别 ASR（none → roleplay）

| 类别 | ASR |
|---|---|
| direct_injection | 0% → 0% |
| indirect_injection | 0% → 0% |
| jailbreak | 0% → 0% |
| system_prompt_leak | 4.5% → 9.1% |
| sensitive_info | 13.6% → 13.6% |
| **unsafe_output** | **54.5% → 72.7%** |

### 关键发现

- 模型对指令注入类防御较强（DI/II/JB 全守住），对**输出侧安全处理**最薄弱
- 角色扮演包装显著提升不安全输出成功率（+18.2pp）
- 编码混淆对泄露类载荷有小幅提升，但对 UO 类反而下降（模型解码后更谨慎）
- 人工抽检与统计口径：`scripts/export_runs.py` / `scripts/stats.py`

## 防护对比实验（W3）

防护代理对同一批载荷的拦截效果（DeepSeek-V3）：

| 实验组 | 攻破/总数 | ASR |
|---|---|---|
| 基线（无防护，原始载荷） | 16/137 | 11.7% |
| 基线（无防护，角色扮演变异） | 21/137 | 15.3% |
| **开启防护（原始载荷）** | **0/137** | **0%** |
| **开启防护（角色扮演变异）** | **0/137** | **0%** |
| 正常业务问题 50 条 | 误拦截 0 条 | 误报率 **0%** |

> 274 次防护运行全部在输入侧拦截（规则命中 / 编码还原 / 相似度匹配），未到达模型。

### 诚实边界：泛化测试

签名式防护（规则 + 相似度）对已知载荷 100% 拦截，但 10 条手写改写攻击 **10/10 全部绕过**。
下一步迭代方向：语义向量检测（sentence-transformers）+ 阈值调优，用同一套泛化测试集量化提升。

### 防护代理用法

```powershell
venv\Scripts\python -m uvicorn proxy.app:app --port 8000
# 客户端 base_url 指向 http://127.0.0.1:8000/v1 即可透明启用防护
```

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

# 6. 运行测试并查看统计
venv\Scripts\python scripts\run_once.py --limit 10                              # 单链路（顺序）
venv\Scripts\python scripts\run_batch.py --limit 50                             # 批量并发
venv\Scripts\python scripts\run_batch.py --mutation roleplay --limit 50         # 指定变异策略
venv\Scripts\python scripts\run_batch.py --guardrail --limit 50                 # 开启防护对比
venv\Scripts\python scripts\stats.py                                            # ASR 统计
venv\Scripts\python scripts\export_runs.py --limit 50                           # 导出抽检 CSV
venv\Scripts\python scripts\test_false_positive.py                              # 误报率测试
venv\Scripts\python scripts\test_generalization.py                              # 泛化测试
```

## 架构

```
载荷库(YAML 137条) → 变异引擎(4策略) → 批量评测引擎 → 判定器(规则+LLM裁判) → SQLite(runs) → 统计/CSV
                                          │
                                          ▼
                        FastAPI 防护代理 ─ 输入防护(规则/编码还原/相似度)
                                          └ 输出防护(验证码拦截/PII脱敏)
                                          │
                                          ▼
                                    DeepSeek / 多模型
```
