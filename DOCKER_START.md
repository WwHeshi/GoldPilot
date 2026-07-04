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

说明：

- MySQL 用户为 `root`，密码为 `goldmind123`，数据库名为 `gold_analysis`。
- 默认不需要 AI API Key。未配置 Key 时，AI 刷新类功能会使用缓存/默认数据或降级结果。
- 如果后续要启用真实 AI 分析，在 `docker-compose.yml` 的 `backend.environment` 中填入 `ZHIPU_API_KEY` 和 `DEEPSEEK_API_KEY` 即可。
