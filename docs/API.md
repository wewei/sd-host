# SD-Host API Documentation

SD-Host 提供了一套完整的 RESTful API 来管理 Stable Diffusion 模型和图像生成服务。

## API 概述

- **设计原则**: RESTful 架构，JSON 数据交换
- **API 前缀**: `/api/v1`
- **实时通信**: Server-Sent Events (SSE)
- **目标场景**: 单用户本地部署或局域网使用

---

## 1. 模型管理类 (Model Management)

管理 Stable Diffusion 模型的增删查改操作。

### API 端点

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/v1/models` | 获取所有可用模型列表 |
| GET | `/api/v1/models/{model_sha256}` | 智能获取模型信息（支持 SSE 下载进度） |
| POST | `/api/v1/models/add-from-civitai` | 从 Civitai 添加新模型 |
| DELETE | `/api/v1/models/{model_sha256}` | 删除指定模型 |

📖 **详细文档**: [Model Management API](./model-management.md)

---

## 2. 任务管理类 (Task Management)

调度主机资源，完成图像渲染任务。

### API 端点

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/v1/tasks/queue` | SSE 实时推送任务队列状态 |
| POST | `/api/v1/tasks` | 创建新任务（智能调度） |
| DELETE | `/api/v1/tasks` | 取消任务列表（批量取消） |
| PUT | `/api/v1/tasks/priority` | 提升任务列表优先级（批量调整） |

📖 **详细文档**: [Task Management API](./task-management.md)

---

## 3. 图像管理类 (Image Management)

管理所有类型的图像和元数据系统。

### API 端点

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/v1/images/{image_hash}` | 获取图像数据（直接返回图像文件内容） |
| POST | `/api/v1/images/{image_hash}/metadata` | 为图像设置元数据属性 |
| GET | `/api/v1/images` | 查询图像（按属性过滤） |
| DELETE | `/api/v1/images` | 删除图像（支持批量删除） |

📖 **详细文档**: [Image Management API](./image-management.md)

---

## 4. 系统功能类 (System Features)

提供系统基本信息查询功能。

### API 端点

| 方法 | 端点 | 功能描述 |
|------|------|----------|
| GET | `/api/v1/version` | 获取 API 版本信息 |
| GET | `/api/v1/config` | 获取系统配置（非敏感信息） |

📖 **详细文档**: [System Features API](./system-features.md)
