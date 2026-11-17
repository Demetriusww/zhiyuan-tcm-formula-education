# 知源 · 中医方剂通识平台

面向普通公众的中医方剂科普网站，以方剂通识教育和组成配伍解说为核心。项目将方剂、中药、古籍来源和 AI 问答整合在同一套学习流程中，帮助不了解中医的人从一味药、一首方开始理解方源、组成、传统功用、君臣佐使与安全边界。

> 本项目仅用于中医药文化传播与通识学习，不提供疾病诊断、个人处方、剂量、加减或用药建议。

## 主要功能

- 方剂 AI 问答：使用 DeepSeek `deepseek-chat` 解释方剂出处、组成和配伍思路。
- 方剂拆解：从君臣佐使、药性归经和方证语境理解经典方剂。
- 方剂与中药知识库：检索方剂、药材、出处、功用、主治与关联资料。
- 中药图鉴：结合本地药材图片和分类浏览，建立直观认识。
- 方剂知识图谱、相似方比较和资料可视化。
- 方剂科普内容评估、来源核验与学习指南。
- 面向公众的学习任务、收藏和科普运营功能。

## 技术栈

- 前端：React 18、TypeScript、Vite、Ant Design、ECharts、AntV G6
- 后端：FastAPI、SQLAlchemy、Alembic、SQLite
- 大模型：DeepSeek OpenAI 兼容接口

## 目录结构

```text
.
├─ backend/
│  ├─ app/                 FastAPI 应用、模型、服务与算法
│  ├─ migrations/          Alembic 数据库迁移
│  ├─ seed/                方剂、中药与古籍种子数据
│  ├─ tests/               后端测试
│  └─ requirements.txt
└─ frontend/
   ├─ public/images/herbs/ 本地中药图片资源
   ├─ src/                 页面、组件、样式与前端数据
   └─ package.json
```

## 本地运行

### 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

在 `backend/.env` 中配置 DeepSeek：

```dotenv
LLM_API_KEY=your_deepseek_api_key
LLM_API_BASE=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

后端启动时会自动创建 SQLite 数据库并灌入种子数据。接口文档位于 `http://127.0.0.1:8000/api/docs`，健康检查位于 `http://127.0.0.1:8000/health`。

### 前端

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问 `http://127.0.0.1:5173`。

## 测试与构建

```powershell
cd backend
pytest

cd ..\frontend
npm run build
```

## 配置与数据说明

- 真实 API Key 仅保存在本地 `backend/.env`，该文件不会提交到仓库。
- SQLite 数据库、日志、测试缓存、依赖目录和前端构建产物均为本地生成文件。
- 方剂、中药和古籍的初始内容来自 `backend/seed/`，应用首次启动时自动导入。
- 前端使用 `frontend/public/images/herbs/` 中的本地图片资源。
