# SD-Host API Documentation

SD-Host 提供了一套完整的 RESTful API 来管理 Stable Diffusion 模型和图像生成服务。

## API 概述

API 基于 RESTful 设计原则，使用 JSON 格式进行数据交换。所有 API 都以 `/api/v1` 为前缀。

## API 分类

### 1. 模型管理类 (Model Management)

管理 Stable Diffusion 模型的增删查改操作。

**设计特性：**

- 所有模型使用 SHA256 hash 作为唯一标识符
- TrackingId 与模型 SHA256 相同，实现统一标识和幂等下载
- 下载追踪 URL 与添加操作形成语义闭环：`add-from-civitai/{model_sha256}`
- 支持 Server-Sent Events (SSE) 实时进度追踪

- `GET /api/v1/models` - 获取所有可用模型列表
- `GET /api/v1/models/{model_sha256}` - 获取指定模型详细信息（使用 SHA256 hash）
- `POST /api/v1/models/add-from-civitai` - 从 Civitai 添加新模型（返回模型版本的 SHA256 作为 TrackingId）
- `GET /api/v1/models/add-from-civitai/{model_sha256}` - SSE 实时追踪模型下载进度（支持幂等操作）
- `DELETE /api/v1/models/{model_sha256}` - 删除模型

### 2. 核心渲染类 (Rendering Core)

调度主机资源，完成图像渲染任务。


#### Pipeline 管理

**设计特性：**

- 始终保持单一 checkpoint 在线，避免内存浪费
- checkpoint 加载具有智能检查机制，避免重复加载
- LoRA 支持追加和替换两种加载模式
- 统一状态接口提供完整的 pipeline 和系统信息

- `GET /api/v1/pipeline/status` - 获取当前 pipeline 完整状态（checkpoint、lora 列表、device、系统信息和负载）
- `POST /api/v1/pipeline/load-checkpoint/{model_sha256}` - 加载 checkpoint（智能检查，避免重复加载）
- `POST /api/v1/pipeline/load-loras` - 加载 LoRA 列表（支持追加模式，默认替换模式）

#### 任务管理

- `POST /api/v1/generate` - 创建图像生成任务
- `GET /api/v1/tasks` - 获取任务列表（支持分页和过滤）
- `GET /api/v1/tasks/{task_id}` - 获取指定任务详情
- `DELETE /api/v1/tasks/{task_id}` - 取消/删除任务

**批量任务：**

- `POST /api/v1/generate/batch` - 创建批量生成任务
- `GET /api/v1/batch/{batch_id}` - 获取批量任务状态
- `POST /api/v1/batch/{batch_id}/cancel` - 取消批量任务

**队列管理：**

- `GET /api/v1/queue` - 获取当前任务队列状态
- `POST /api/v1/queue/pause` - 暂停任务队列
- `POST /api/v1/queue/resume` - 恢复任务队列
- `POST /api/v1/queue/clear` - 清空队列

### 3. 输出管理类 (Output Management)

管理输出的图像和生成信息。

#### 建议 API 列表：

**图像 CRUD：**
- `GET /api/v1/images` - 获取图像列表（支持分页、过滤、搜索）
- `GET /api/v1/images/{image_id}` - 获取指定图像文件
- `GET /api/v1/images/{image_id}/metadata` - 获取图像元数据
- `DELETE /api/v1/images/{image_id}` - 删除图像
- `POST /api/v1/images/{image_id}/copy` - 复制图像

**图像集合管理：**
- `GET /api/v1/collections` - 获取图像集合列表
- `POST /api/v1/collections` - 创建新集合
- `GET /api/v1/collections/{collection_id}` - 获取集合详情
- `PUT /api/v1/collections/{collection_id}` - 更新集合信息
- `DELETE /api/v1/collections/{collection_id}` - 删除集合
- `POST /api/v1/collections/{collection_id}/images` - 添加图像到集合
- `DELETE /api/v1/collections/{collection_id}/images/{image_id}` - 从集合移除图像

**导出和分享：**
- `POST /api/v1/images/export` - 批量导出图像
- `POST /api/v1/images/{image_id}/share` - 生成图像分享链接
- `GET /api/v1/shared/{share_id}` - 访问分享的图像

**存储管理：**
- `GET /api/v1/storage/stats` - 获取存储统计信息
- `POST /api/v1/storage/cleanup` - 清理过期文件
- `GET /api/v1/storage/usage` - 获取存储使用情况

## 通用特性

**认证和授权：**
- `POST /api/v1/auth/login` - 用户登录（如启用认证）
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/profile` - 获取用户信息

**系统管理：**
- `GET /api/v1/health` - 健康检查
- `GET /api/v1/version` - 获取 API 版本信息
- `GET /api/v1/config` - 获取系统配置（非敏感信息）

---

## 📋 更新后的 API 统计

### 1. **模型管理类** (5个 API)
- 模型 CRUD：4个（专用 Civitai 添加，使用 SHA256 作为模型 ID 和 TrackingId）
- SSE 下载追踪：1个（实时进度更新，支持幂等操作）

### 2. **核心渲染类** (13个 API)
- Pipeline 管理：3个（优先级最高，checkpoint + LoRA 管理）
- 任务管理：4个
- 批量任务：3个
- 队列管理：4个
- 系统资源：2个

### 3. **输出管理类** (14个 API)
- 图像 CRUD：5个
- 集合管理：7个
- 导出分享：3个
- 存储管理：3个

### 4. **通用特性** (6个 API)
- 认证授权：3个
- 系统管理：3个

---

## API 审阅说明

以上是基于您的三大分类设计的 API 列表建议。每个分类都包含了核心功能和扩展功能，请逐一审阅：

1. **是否有遗漏的重要 API？**
2. **是否有不必要的 API？**
3. **API 命名是否合理？**
4. **分类是否恰当？**

请告诉我您的反馈，我将根据您的意见调整和完善 API 设计。
