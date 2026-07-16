# 3 - ai_assist/case_generator

## 背景

项目探索 AI 辅助测试工程实践，核心目标是根据接口文档描述自动生成测试用例草稿，减少手工设计用例的重复劳动。

---

## 选型：DeepSeek API（deepseek-v4-flash）

### 为什么不用 Claude API

原计划使用 Claude API，但受网络访问限制无法在当前开发环境中完成集成。

### 为什么从 GLM 迁移到 DeepSeek

- 最初选择 GLM 的主要原因是新用户免费额度；额度耗尽后，该选型前提不再成立
- DeepSeek API 同样兼容 OpenAI Chat Completions 格式，现有 `requests` 调用可以直接迁移，无需增加 SDK
- `deepseek-v4-flash` 更适合轻量结构化生成；显式关闭思考模式以控制延迟和费用
- 旧模型名 `deepseek-chat` 将于 2026-07-24 停用，因此直接使用 V4 模型名

### 放弃的方案

- **继续使用 GLM API**：免费额度已经耗尽，继续保留会让 AI 功能不可用
- **deepseek-v4-pro**：能力更强，但当前任务不需要更高成本和延迟
- **deepseek-chat**：临近官方停用日期，不应作为新迁移目标
- **本地模型（Ollama 等）**：部署成本高，与项目"快速验证"的阶段目标不符

---

## case_generator.py 设计决策

### 输入：结构化字典

接口规格由调用方整理成结构化字典（`api_name`、`params`、`rules`），而非直接喂入原始文档文本。

理由：原始文档格式不一，结构化输入能让 prompt 更稳定，生成质量更可控。

### 输出：`list[dict]`

DeepSeek 使用 JSON Output 返回 `{"cases": [...]}` 对象，模块校验后仍向调用方返回 `list[dict]`，保持原有 Python 接口不变。每条用例必须包含 `name`、`params`、`expected`、`description` 四个字段，模块本身不负责写文件或写数据库。

### Prompt 设计

- **system**：固定角色约束，强制输出带 `cases` 根字段的 JSON 对象，要求参数值为具体字符串而非表达式
- **user**：动态拼接接口规格，给出输出格式示例

分开 system/user 的原因：模型被训练为优先遵守 system 约束，格式规则放在 system 比放在 user 更稳定。

### 关键约束

- `timeout=120`：保留较宽松的网络超时，避免外部模型响应波动造成误判
- `thinking.type=disabled`：结构化用例生成不需要推理链，避免额外延迟和 token 消耗
- `response_format=json_object`：让服务端约束 JSON 语法；本地代码继续校验根结构和字段类型
- `max_tokens=4096`：为完整 JSON 留出空间，并在 `finish_reason=length` 时明确报截断错误
- `DEEPSEEK_API_KEY` 通过 `.env` 注入，不硬编码、不提交 git，也不兼容回退到旧 `GLM_API_KEY`
- 响应异常只记录有限长度预览，不把完整外部响应写入错误信息
