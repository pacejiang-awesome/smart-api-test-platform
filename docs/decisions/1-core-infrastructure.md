# 1 - core/config & core/http_client

## 背景

项目需要对高德开放 API 发起 HTTP 请求，所有测试用例共享同一套鉴权和连接配置。

---

## config.py — 配置与密钥管理

### 选型：python-dotenv + 自定义 Config 类

- 用 `python-dotenv` 在模块导入时加载 `.env`，本地开发和 CI 环境无需改代码，只改环境变量注入方式
- 用自定义 `Config` 类而非模块级常量，在实例化时立即校验必填项，缺少 Key 时启动阶段即报错，不会等到用例执行才暴露

### 放弃的方案

- **pydantic-settings**：功能更强，但引入了额外依赖和学习成本，当前需求用标准库 + dotenv 足够

### 关键约束

- `.env` 文件不提交 git（已加入 `.gitignore`）
- `.env.example` 提交 git，作为环境变量清单模板

---

## http_client.py — HTTP 封装层

### 选型：requests.Session 封装成类

- 用 `requests.Session` 而非裸 `requests.get`，对同一主机复用 TCP 连接，减少测试套件整体耗时
- 封装成类（`AMapClient`），在 `__init__` 统一注入 base_url，在 `get` 方法统一注入 API Key 和 timeout，测试用例只传业务参数
- 返回原始 `requests.Response` 对象，保留状态码、响应时间、响应头等信息，供测试用例按需断言

### 放弃的方案

- **函数式封装**：无法复用连接，测试规模扩大后性能劣势明显
- **httpx**：支持异步，但当前测试全为同步场景，引入异步增加不必要复杂度

### 关键约束

- Week 1 只实现 `get`，重试逻辑和请求日志推迟到 Week 2 按需加入
- `client = AMapClient()` 在模块末尾创建单例，避免多处实例化浪费连接
- `TIMEOUT = 5`：实测高德 API 正常响应在几十到几百毫秒量级，5 秒在正常请求与真实超时之间留有足够余量
