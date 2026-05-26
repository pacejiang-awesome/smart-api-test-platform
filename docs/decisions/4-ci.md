# 4 - GitHub Actions CI

## 背景

项目完成 Docker 部署后，需要一套持续集成机制：每次 push 或 PR 自动运行测试，防止改动破坏已有功能。

---

## 选型：GitHub Actions

### 为什么不用其他 CI

- Jenkins：需要自行维护服务器，与项目"轻量个人项目"定位不符
- GitLab CI：项目托管在 GitHub，迁移成本高
- GitHub Actions：与仓库原生集成，公开仓库完全免费，零额外配置

### 为什么测试用真实 HTTP 请求，而不是 Mock

- 项目核心价值是验证高德 API 的真实行为，Mock 测试无法发现接口协议变化
- GitHub Actions runner 在 Azure 境外节点，经验证可正常访问 `restapi.amap.com`
- API Key 通过 GitHub Secrets 注入，不暴露在代码中

### 放弃的方案

- **`responses` / `pytest-mock` 库**：引入 Mock 层需改造现有测试代码，收益低于成本
- **CD（自动部署到腾讯云）**：涉及服务器 SSH 密钥管理，超出当前阶段目标，暂不引入

---

## 关键决策

**分两步验证**：先用 `network-check.yml`（手动触发）确认 runner 能访问高德 API，再写正式 CI，避免在不确定网络连通性的情况下调试 workflow。

**触发条件**：push 到 main 和向 main 发 PR 时触发，覆盖日常开发和代码合并两个场景。

### 关键约束

- `pip install` 不加国内镜像——runner 在境外，PyPI 直连正常
- 仅需 `AMAP_API_KEY` 一个 Secret，`GLM_API_KEY` 未参与测试流程
