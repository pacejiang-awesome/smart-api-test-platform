# Smart API Test Platform — CLAUDE.md

## 项目定位

个人技术学习与实验项目，探索 AI 辅助测试工程实践。
- **被测对象**：高德地图开放平台 API
- **项目重点探索方向**：集成 GLM API，根据接口文档自动生成测试用例
- **部署目标**：Docker 容器化，运行在腾讯云服务器，对外提供可访问的 URL

## 技术栈

| 层次 | 技术 |
|------|------|
| 测试框架 | pytest + requests + allure-pytest |
| 后端服务 | FastAPI + SQLite |
| 前端展示 | Bootstrap 5 |
| AI 模块 | GLM API（智谱AI，glm-4.5-air） |
| 部署 | Docker + 腾讯云服务器 |
| CI | GitHub Actions（只跑测试，不做 CD） |

## 开发环境

**IDE：** VS Code

**已安装扩展：**

| 扩展 | ID |
|------|----|
| Python | ms-python.python |
| Pylance | ms-python.vscode-pylance |
| Python Debugger | ms-python.debugpy |
| Even Better TOML | tamasfe.even-better-toml |
| DotENV | mikestead.dotenv |
| GitLens | eamodio.gitlens |
| YAML | redhat.vscode-yaml |
| Docker | ms-azuretools.vscode-docker |
| REST Client | humao.rest-client |
| autoDocstring | njpwerner.autodocstring |
| Markdown All in One | yzhang.markdown-all-in-one |
| Code Spell Checker | streetsidesoftware.code-spell-checker |
| Error Lens | usernamehw.errorlens |

## 目录结构

```
smart-api-test-platform/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── pytest.ini
├── conftest.py
├── .gitignore
├── tests/
│   ├── __init__.py
│   ├── test_geocode.py        # Week 1-2 重点，做透正常/异常/边界/参数化
│   └── test_poi_search.py     # Week 3 加入，其余接口暂不建文件
├── core/
│   ├── __init__.py
│   ├── http_client.py         # requests 封装层
│   ├── config.py              # 配置与密钥管理
│   └── db.py                  # SQLite 读写
├── api/
│   ├── __init__.py
│   └── main.py                # FastAPI，暴露测试结果接口
├── models/
│   ├── __init__.py
│   └── test_result.py         # 数据模型
├── ai_assist/
│   ├── __init__.py
│   └── case_generator.py      # GLM API 自动生成测试用例
├── web/
│   ├── templates/
│   │   └── index.html         # Bootstrap 5 看板
│   └── static/
├── docs/
│   └── decisions/             # 技术决策记录
├── allure-results/            # allure 原始数据（.gitignore 排除）
└── reports/                   # 生成的 HTML 报告
```

## 协作约定

### 开发节奏

本项目采用结对编程风格，偏好渐进式开发：
- **每个核心模块先讨论设计思路，确认后再进入实现阶段，不一次性给出完整模块代码。**
- **每次修改或新建文件前，必须先确认。**
- **已确认通过的代码不做改动。** 若确实需要修改，先说明原因和影响范围，确认后再动手。

### 解释方式

- **第一次出现的库**：用一两句话说明它是什么、为什么在这里用它，再给代码。
- **遇到报错**：先给出错误的关键信息，等开发者自行分析；收到"详细解释"指令后再展开完整分析，不主动剧透。
- **聊天中展示的代码**：每个函数、每个关键语句都加详细中文注释，标准是"零基础也能读懂"；写入文件时改回简洁风格，遵循「不重复描述显而易见的事」。

### 文档

- 每个核心模块完成后，在 `docs/decisions/` 下生成一篇决策记录：
  - 文件名格式：`N-模块名.md`（N 为递增序号）
  - 内容：选型理由、放弃的备选方案、关键约束

### 代码风格

- 变量、函数名统一使用英文蛇形命名（snake_case）
- 每条测试用例须有一行中文注释，说明测试意图（写"为什么"，不写"做了什么"）
- 不在注释中重复描述显而易见的事
- **Git commit message 用英文，遵循 Conventional Commits 规范**：
  - 格式：`<type>(<scope>): <description>`
  - type 取值：`feat` / `fix` / `docs` / `refactor` / `test` / `chore`
  - 示例：`feat(geocode): add boundary test cases for empty address input`

### 调试环境注意事项

涉及国内 API（高德、智谱等）时，若通过 Claude Code Bash 工具直接调用出现超时，优先排查代理设置——需将对应域名加入本地 `NO_PROXY`，不提交到 git。

### 工具与配置引导

不提前推荐工具或配置清单。当项目某个具体场景真正需要某个工具/配置时，再引入，并说明：
1. 为什么这个时间点需要它
2. 不装/不配的代价是什么
3. 具体操作步骤（点哪里、输入什么）

已安装的 VS Code 扩展见「开发环境」小节，不重复推荐。
