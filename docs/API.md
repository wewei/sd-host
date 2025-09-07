# SD-Host API Documentation

SD-Host 提供了一套完整的 RESTful API 来管理 Stable Diffusion 模型和图像生成服务。

## API 概述

- **设计原则**: RESTful 架构，JSON 数据交换
- **API 前缀**: `/api`
- **实时通信**: Server-Sent Events (SSE)
- **目标场景**: 单用户本地部署或局域网使用
- **查询系统**: 基于 JSON API 标准的实体查询协议

📖 **查询协议详细文档**: [实体查询协议 (JSON API)](./entity-query-protocol.md)

📊 **数据库设计文档**: [SQLite 数据库表结构](./database-schema.md)

---

## 1. 模型管理类 (Model Management)

管理 Stable Diffusion 模型的增删查改操作。

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/models` | 获取模型列表（支持 JSON API 查询） |
| GET | `/api/models/{hash}` | 获取指定模型元数据 |
| GET | `/api/models/{hash}/content` | 下载模型文件内容 |
| POST | `/api/models/{hash}` | 修改模型元数据 |
| POST | `/api/models` | 批量修改模型元数据 |
| DELETE | `/api/models/{hash}` | 删除指定模型 |
| DELETE | `/api/models` | 批量删除模型 |
| POST | `/api/models/add-from-civitai` | 从 Civitai 添加新模型 |
| GET | `/api/models/add-from-civitai/{hash}` | SSE 追踪下载进度 |

📖 **详细文档**: [Model Management API](./model-management.md)

---

## 2. 任务管理类 (Task Management)

调度主机资源，完成图像渲染任务。

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/tasks/queue` | SSE 实时推送任务队列状态 |
| POST | `/api/tasks` | 创建新任务（智能调度） |
| DELETE | `/api/tasks` | 取消任务列表（批量取消） |
| PUT | `/api/tasks/promote` | 提升任务列表执行优先级（批量提升） |

📖 **详细文档**: [Task Management API](./task-management.md)

---

## 3. 图像管理类 (Image Management)

管理所有类型的图像和元数据系统。

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/images` | 获取图像列表（支持 JSON API 查询） |
| GET | `/api/images/{hash}` | 获取指定图像元数据 |
| GET | `/api/images/{hash}/content` | 获取图像文件内容 |
| POST | `/api/images/{hash}` | 修改图像元数据 |
| POST | `/api/images` | 批量修改图像元数据 |
| DELETE | `/api/images/{hash}` | 删除指定图像 |
| DELETE | `/api/images` | 批量删除图像 |

📖 **详细文档**: [Image Management API](./image-management.md)

---

## 4. 系统功能类 (System Features)

提供系统基本信息查询功能。

### API 端点

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/version` | 获取 API 版本信息 |
| GET | `/api/config` | 获取系统配置（非敏感信息） |

📖 **详细文档**: [System Features API](./system-features.md)
