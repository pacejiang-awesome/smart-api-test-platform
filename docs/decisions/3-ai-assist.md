# 3 - ai_assist/case_generator

## 背景

项目探索 AI 辅助测试工程实践，核心目标是根据接口文档描述自动生成测试用例草稿，减少手工设计用例的重复劳动。

---

## 选型：GLM API（智谱AI，glm-4.5-air）

### 为什么不用 Claude API

原计划使用 Claude API，但受网络访问限制无法在当前开发环境中完成集成。

### 为什么选 GLM

- 智谱 AI 提供新用户免费资源包，零成本完成 Week 5 功能验证
- GLM API 兼容 OpenAI 接口格式，只需 `requests` 直接调用，无需额外 SDK
- glm-4.5-air 是轻量快速模型，对"结构化文本生成"类任务足够，不需要重量级推理

### 放弃的方案

- **DeepSeek API**：能力略强，但用户已有 GLM 免费额度，优先零成本方案
- **本地模型（Ollama 等）**：部署成本高，与项目"快速验证"的阶段目标不符

---

## case_generator.py 设计决策

### 输入：结构化字典

接口规格由调用方整理成结构化字典（`api_name`、`params`、`rules`），而非直接喂入原始文档文本。

理由：原始文档格式不一，结构化输入能让 prompt 更稳定，生成质量更可控。

### 输出：`list[dict]`

每条用例包含 `name`、`params`、`expected`、`description` 四个字段，返回给调用方使用，模块本身不负责写文件或写数据库。

### Prompt 设计

- **system**：固定角色约束，强制 JSON-only 输出，要求参数值为具体字符串而非表达式
- **user**：动态拼接接口规格，给出输出格式示例

分开 system/user 的原因：模型被训练为优先遵守 system 约束，格式规则放在 system 比放在 user 更稳定。

### 关键约束

- `timeout=120`：glm-4.5-air 生成完整用例列表约需 60-120 秒，低于此值频繁超时
- 模型输出有时包含 ` ```json ``` ` 代码块包裹，需在解析前剥离
- `GLM_API_KEY` 通过 `.env` 注入，不硬编码，不提交 git
