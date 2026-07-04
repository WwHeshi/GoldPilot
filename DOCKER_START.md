# Docker 启动

本项目现在默认使用 Docker Compose 启动前端、后端和 MySQL，不需要复制或编辑 `.env` 文件。

```powershell
cd C:\Users\HEtu_saaa\Desktop\GoldPilot
docker compose up -d --build
```

查看状态：

```powershell
docker compose ps
docker compose logs -f backend
```

访问地址：

- 前端：http://localhost
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

停止服务：

```powershell
docker compose down
```

清空数据库并停止：

```powershell
docker compose down -v
```

## 热更新开发版

开发时使用 `docker-compose.dev.yml`。它会挂载本地源码：

- 修改 `app/src` 后，前端 Vite 会热更新。
- 修改 `backend/app` 后，后端 Uvicorn 会自动 reload。
- 端口和普通 Docker 版错开，避免冲突。

```powershell
cd C:\Users\HEtu_saaa\Desktop\GoldPilot
docker compose -f docker-compose.dev.yml up --build
```

访问地址：

- 前端热更新：http://localhost:5173
- 后端 API：http://localhost:8001
- API 文档：http://localhost:8001/docs
- MySQL：localhost:3307

停止热更新版：

```powershell
docker compose -f docker-compose.dev.yml down
```

清空热更新版数据库：

```powershell
docker compose -f docker-compose.dev.yml down -v
```

说明：

- MySQL 用户为 `root`，密码为 `goldmind123`，数据库名为 `gold_analysis`。
- 默认不需要 AI API Key。未配置 Key 时，AI 刷新类功能会使用缓存/默认数据或降级结果。
- 如果后续要启用真实 AI 分析，打开页面右上角的 `AI 设置`，填写 `Base URL`、`Model` 和 `API Key` 即可。
