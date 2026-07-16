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
- CI 仅需 `AMAP_API_KEY`；`DEEPSEEK_API_KEY` 不注入 CI，AI 单元测试使用模拟响应

---

## 排错记录：CD 静默失败导致容器从未更新（2026-05-29）

### 现象

服务器运行的容器长期停留在旧版本，网页只显示 19 条旧测试结果，
新增的测试文件从未出现在容器内，CI 和 CD 在 Actions 里显示绿色。

### 根本原因

早期为移除 Co-Authored-By 签名做了一次 force push，重写了 git 历史。
服务器本地仓库未跟上，本地和 remote 各自积累了不同的提交，形成发散。

此后每次 CD 执行 `git pull` 都因无法 fast-forward 而失败，但脚本没有
对 `git pull` 的退出码做校验，后续的 `docker build` 继续用**旧代码**执行，
容器表面上重建了，实际内容从未更新。

### 修复

1. 服务器手动执行 `git fetch origin && git reset --hard origin/main` 对齐
2. CD 脚本将 `git pull` 替换为：
   ```bash
   git fetch origin
   git reset --hard origin/main
   ```
   `reset --hard` 无论历史是否发散都能强制对齐，force push 后同样适用。

### 设计约束

**CD 脚本不应使用 `git pull`**。`git pull` 在历史发散时静默失败（退出码非 0
但脚本 `|| true` 风格会吞掉错误），导致后续步骤用旧代码执行，问题极难察觉。
部署脚本应始终使用 `git fetch + git reset --hard origin/<branch>`。
