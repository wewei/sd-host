# SD-Host API Documentation

SD-Host 提供了一套完整的 RESTful API 来管理 Stable Diffusion 模型和下载任务。

## API 概述

- **设计原则**: RESTful 架构，JSON 数据交换
- **API 前缀**: `/api`
- **实时通信**: Server-Sent Events (SSE)
- **目标场景**: 单用户本地部署或局域网使用
- **查询系统**: 基于 JSON API 标准的实体查询协议

📖 **查询协议详细文档**: [实体查询协议 (JSON API)](./entity-query-protocol.md)

📊 **数据库设计文档**: [SQLite 数据库表结构](./database-schema.md)

---

## RESTful API 设计原则

SD-Host 遵循以下 RESTful API 设计原则，确保 API 的一致性和可预测性：

### 1. 实体列表查询 - `GET /{entities}`

- **用途**: 仅用于获取实体列表，支持按条件查询
- **数据格式**: 实体对象以**列表项的简洁形式**表达，包含核心字段
- **示例**: `GET /api/models` - 获取模型列表，每个模型包含基本信息如 hash、name、type 等

### 2. 实体详情获取 - `GET /{entities}/{entity-id}`

- **用途**: 仅用于获取单个实体的详细信息
- **数据格式**: 返回实体对象的**完整形式 JSON**，包含所有详细字段
- **示例**: `GET /api/models/{hash}` - 获取指定模型的完整元数据

### 3. 实体删除 - `DELETE /{entities}/{entity-id}`

- **用途**: 用于删除指定的单个实体
- **标准操作**: 使用标准的 HTTP DELETE 方法
- **示例**: `DELETE /api/models/{hash}` - 删除指定的模型

### 4. 实体操作 - `POST /{entities}/{action-name}`

- **用途**: 所有的实体操作必须有明确的操作名称
- **命名规范**: 操作名使用清晰的动词或动词短语，采用 kebab-case 格式
- **示例**:
  - `POST /api/models/batch-update` - 批量更新模型
  - `POST /api/models/add-from-civitai` - 从 Civitai 添加模型
  - `POST /api/models/download-tasks/{hash}/action` - 控制下载任务

### 5. 设计优势

- **可预测性**: 开发者可以根据 URL 模式预测 API 行为
- **数据效率**: 列表查询返回简洁数据，详情查询返回完整数据
- **操作明确**: 所有操作都有明确的语义，避免歧义
- **扩展性**: 新操作可以轻松添加而不破坏现有 API 结构

---

## 1. 模型管理类 (Model Management)

管理 Stable Diffusion 模型的增删查改操作和下载任务管理。

### 1.1 模型 CRUD 操作

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/models` | 获取模型列表（支持 JSON API 查询） |
| GET | `/api/models/{hash}` | 获取指定模型元数据 |
| GET | `/api/models/{hash}/content` | 下载模型文件内容 |
| POST | `/api/models/batch-update` | 批量修改模型元数据 |
| DELETE | `/api/models/{hash}` | 删除指定模型 |
| DELETE | `/api/models` | 批量删除模型 |

### 1.2 Civitai 集成

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| POST | `/api/models/add-from-civitai` | 从 Civitai 添加新模型 |
| GET | `/api/models/add-from-civitai/{hash}` | SSE 追踪下载进度 |
| POST | `/api/models/validate-civitai-url` | 验证 Civitai URL |
| GET | `/api/models/download-status/{hash}` | 获取下载状态 |

### 1.3 下载任务管理

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/models/download-tasks` | 获取所有下载任务列表 |
| GET | `/api/models/download-tasks/{hash}` | 获取指定下载任务详情 |
| POST | `/api/models/download-tasks/{hash}/action` | 控制下载任务（暂停/恢复/取消/删除） |
| POST | `/api/models/download-tasks/batch-action` | 批量控制下载任务 |
| DELETE | `/api/models/download-tasks/completed` | 清理已完成的下载任务 |
| POST | `/api/models/download-tasks/mock` | 创建测试下载任务（开发模式） |

📖 **详细文档**: [Model Management API](./model-management.md)

---

## 2. 系统功能类 (System Features)

提供系统基本信息查询功能。

### API 端点

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/` | 获取服务基本信息 |
| GET | `/health` | 健康检查端点 |

📖 **详细文档**: [System Features API](./system-features.md)

---

## 🚧 开发中的功能

以下功能已设计但尚未实现，敬请期待：

### 任务管理类 (Task Management)
> 计划功能：调度主机资源，完成图像渲染任务

| 方法 | 端点 | 功能描述 | 状态 |
|------|------|----------|------|
| GET | `/api/tasks/queue` | SSE 实时推送任务队列状态 | 🚧 规划中 |
| POST | `/api/tasks` | 创建新任务（智能调度） | 🚧 规划中 |
| DELETE | `/api/tasks` | 取消任务列表（批量取消） | 🚧 规划中 |
| PUT | `/api/tasks/promote` | 提升任务列表执行优先级（批量提升） | � 规划中 |

### 图像管理类 (Image Management)
> 计划功能：管理所有类型的图像和元数据系统

| 方法 | 端点 | 功能描述 | 状态 |
|------|------|----------|------|
| GET | `/api/images` | 获取图像列表（支持 JSON API 查询） | 🚧 规划中 |
| GET | `/api/images/{hash}` | 获取指定图像元数据 | 🚧 规划中 |
| GET | `/api/images/{hash}/content` | 获取图像文件内容 | 🚧 规划中 |
| POST | `/api/images/{hash}` | 修改图像元数据 | 🚧 规划中 |
| POST | `/api/images` | 批量修改图像元数据 | 🚧 规划中 |
| DELETE | `/api/images/{hash}` | 删除指定图像 | 🚧 规划中 |
| DELETE | `/api/images` | 批量删除图像 | � 规划中 |

### 系统配置类 (System Configuration)
> 计划功能：系统配置管理

| 方法 | 端点 | 功能描述 | 状态 |
|------|------|----------|------|
| GET | `/api/config` | 获取系统配置（非敏感信息） | 🚧 规划中 |
| GET | `/api/version` | 获取 API 版本信息 | 🚧 规划中 |

---

## 快速开始

### 启动 API 服务
```bash
# 使用 CLI 启动
sdh service start

# 或直接运行 API
cd src
python -m api.main
```

### 访问 API 文档
- **交互式文档**: http://localhost:8000/docs (Swagger UI)
- **ReDoc 文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

### 基本使用示例
```bash
# 获取模型列表
curl http://localhost:8000/api/models

# 添加 Civitai 模型
curl -X POST http://localhost:8000/api/models/add-from-civitai \
  -H "Content-Type: application/json" \
  -d '{"model_id": "4201", "version_id": "130072"}'

# 查看下载任务
curl http://localhost:8000/api/models/download-tasks
```
