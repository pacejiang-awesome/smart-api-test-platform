# 3 - ai_assist/case_generator

## 背景

项目探索 AI 辅助测试工程实践，核心目标是根据接口文档描述自动生成测试用例草稿，减少手工设计用例的重复劳动。

---

## 选型：DeepSeek API（deepseek-v4-pro）

### 为什么不用 Claude API

原计划使用 Claude API，但受网络访问限制无法在当前开发环境中完成集成。

### 为什么从 GLM 迁移到 DeepSeek

- 最初选择 GLM 的主要原因是新用户免费额度；额度耗尽后，该选型前提不再成立
- DeepSeek API 同样兼容 OpenAI Chat Completions 格式，现有 `requests` 调用可以直接迁移，无需增加 SDK
- 最初迁移到 `deepseek-v4-flash`，但真实 API 验证中连续返回语法损坏的 JSON，包含加强提示后的重试仍未通过
- 最终改用 `deepseek-v4-pro` 提高结构化输出可靠性，并显式关闭思考模式以控制延迟和费用
- 旧模型名 `deepseek-chat` 将于 2026-07-24 停用，因此直接使用 V4 模型名

### Flash → Pro 真实试错记录（2026-07-16）

本次验证的目标不是比较模型的通用能力，而是确认它能否稳定履行本模块最重要的契约：返回可被 `json.loads()` 解析，并且包含 `cases` 数组及四个必需字段。

为减少无关变量，所有真实请求都使用同一份虚构的“示例查询接口”规格，不发送项目源码或真实业务数据；请求均关闭思考模式、开启 `response_format=json_object`，并设置 `max_tokens=4096`。

| 阶段 | 模型与处理 | 实际结果 | 结论 |
|------|------------|----------|------|
| 1. 最小迁移 | `deepseek-v4-flash`，只使用 JSON Output | 请求成功，但返回内容存在 JSON 语法错误，解析失败 | 鉴权、网络和接口兼容性正常；结构化输出未通过 |
| 2. 加强提示 | Flash 首次失败后，用更严格提示自动重试一次 | 同一轮首次和重试响应仍无法解析；Flash 实际到达 API 的 3 次请求全部失败 | 问题不能仅靠一句更严格的 prompt 稳定解决 |
| 3. 仅切模型 | 保持请求结构、校验规则和重试保护不变，只改为 `deepseek-v4-pro` | 1 次请求成功返回 5 条用例，全部通过 `name`、`params`、`expected`、`description` 契约校验 | 当前项目选择 Pro |

另有一次 Flash 调用在本机沙箱内被 `WinError 10013` 阻止，连接没有到达 DeepSeek，因此不计入模型失败次数。

这次结果是小样本迁移验收，不代表 Flash 在所有任务中都无法生成 JSON。它能支持的结论是：在本项目当前 prompt 和结构化用例场景下，Flash 连续 3 次未达到可用标准，而 Pro 在同条件下通过。若未来调用量扩大，应记录成功率、重试率、延迟和 token 费用，再决定是否重新评估 Flash。

### 为什么不在本地“猜着修复”坏 JSON

自动补逗号、引号等语法看似省一次模型调用，但可能悄悄改变 `params` 或 `expected` 的业务含义。测试用例本身是后续判断系统正确与否的依据，因此这里选择“严格校验 → 最多重试一次 → 仍失败就明确报错”，不把无法确认语义的内容修补成表面合法的数据。

### 放弃的方案

- **继续使用 GLM API**：免费额度已经耗尽，继续保留会让 AI 功能不可用
- **deepseek-v4-flash**：成本和延迟更低，但本项目的真实 JSON Output 验证连续失败
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
- 模型返回无效 JSON 或不满足字段契约时，用更严格提示最多重试一次；HTTP 错误不重试，避免认证、余额或限流问题产生重复费用
