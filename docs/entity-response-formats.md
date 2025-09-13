# 数据实体响应格式定义

本文档定义了 SD-Host API 中各数据实体的简洁形式（列表查询）和完整形式（详情查询）的响应格式。

## 设计原则

遵循 RESTful API 设计原则：

1. **简洁形式** (`GET /{entities}`) - 列表查询返回核心字段，优化传输效率
2. **完整形式** (`GET /{entities}/{entity-id}`) - 详情查询返回所有字段和关联关系
3. **字段选择** - 支持通过 `fields[type]` 参数自定义返回字段
4. **关联包含** - 支持通过 `include` 参数包含关联实体

---

## 1. Model（模型）实体

### 简洁形式 - `GET /api/models`

用于模型列表展示，包含核心标识和状态信息：

```json
{
  "type": "model",
  "id": "sha256_hash",
  "attributes": {
    "name": "模型名称",
    "model_type": "checkpoint|lora|controlnet|vae|embedding",
    "base_model": "SD1.5|SDXL|SD2|null",
    "size": 1234567890,
    "status": "ready|downloading|error",
    "created_at": "2024-01-01T00:00:00Z",
    "cover_image_hash": "image_hash|null"
  }
}
```

### 完整形式 - `GET /api/models/{hash}`

包含所有详细信息和关联关系：

```json
{
  "type": "model",
  "id": "sha256_hash",
  "attributes": {
    "name": "模型名称",
    "model_type": "checkpoint",
    "base_model": "SD1.5",
    "size": 1234567890,
    "source_url": "https://civitai.com/...",
    "model_metadata": {"训练参数": "详细JSON数据"},
    "description": "模型描述文档（Markdown格式）",
    "cover_image_hash": "image_hash",
    "status": "ready",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "relationships": {
    "tags": {"data": [{"type": "tag", "id": "tag_name"}]},
    "cover_image": {"data": {"type": "image", "id": "image_hash"}}
  }
}
```

---

## 2. Task（任务）实体

### 简洁形式 - `GET /api/tasks`

用于任务队列展示，包含基本状态和关键参数：

```json
{
  "type": "task",
  "id": "task_uuid",
  "attributes": {
    "status": "pending|completed|failed|cancelled",
    "prompt": "提示词前100字符...",
    "width": 512,
    "height": 512,
    "checkpoint_name": "主模型名称",
    "created_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:00:00Z|null",
    "image_count": 4
  }
}
```

### 完整形式 - `GET /api/tasks/{id}`

包含完整生成参数和关联信息：

```json
{
  "type": "task",
  "id": "task_uuid",
  "attributes": {
    "status": "completed",
    "prompt": "完整提示词内容",
    "negative_prompt": "负面提示词",
    "width": 512,
    "height": 512,
    "seed": 12345,
    "steps": 20,
    "cfg_scale": 7.0,
    "sampler": "DPM++ 2M Karras",
    "batch_size": 4,
    "error_message": null,
    "created_at": "2024-01-01T00:00:00Z",
    "promoted_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "relationships": {
    "checkpoint": {"data": {"type": "model", "id": "model_hash"}},
    "vae": {"data": {"type": "model", "id": "vae_hash"}},
    "images": {"data": [{"type": "image", "id": "image_hash"}]},
    "additional_models": {"data": [{"type": "model", "id": "lora_hash"}]},
    "tags": {"data": [{"type": "tag", "id": "tag_name"}]}
  }
}
```

---

## 3. Image（图像）实体

### 简洁形式 - `GET /api/images`

用于图像网格展示，包含基本尺寸和关联信息：

```json
{
  "type": "image",
  "id": "image_hash",
  "attributes": {
    "width": 512,
    "height": 512,
    "size": 1048576,
    "task_id": "task_uuid|null",
    "created_at": "2024-01-01T00:00:00Z",
    "thumbnail_url": "/api/images/hash/thumbnail"
  }
}
```

### 完整形式 - `GET /api/images/{hash}`

包含生成参数和完整关联信息：

```json
{
  "type": "image",
  "id": "image_hash",
  "attributes": {
    "width": 512,
    "height": 512,
    "size": 1048576,
    "seed": 12345,
    "task_id": "task_uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "content_url": "/api/images/hash/content",
    "thumbnail_url": "/api/images/hash/thumbnail"
  },
  "relationships": {
    "task": {"data": {"type": "task", "id": "task_uuid"}},
    "tags": {"data": [{"type": "tag", "id": "tag_name"}]}
  }
}
```

---

## 4. DownloadTask（下载任务）实体

### 简洁形式 - `GET /api/models/download-tasks`

用于下载进度监控，包含状态和进度信息：

```json
{
  "type": "download_task",
  "id": "download_hash",
  "attributes": {
    "model_name": "模型名称",
    "model_type": "checkpoint|lora|controlnet|vae|embedding",
    "status": "pending|downloading|paused|completed|failed|cancelled",
    "progress": 75.5,
    "speed": "1.2 MB/s",
    "eta": "2m 30s",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### 完整形式 - `GET /api/models/download-tasks/{hash}`

包含完整下载配置和错误信息：

```json
{
  "type": "download_task",
  "id": "download_hash",
  "attributes": {
    "model_hash": "target_model_hash|null",
    "model_name": "模型名称",
    "version_name": "版本名称",
    "model_type": "checkpoint",
    "source_url": "https://civitai.com/api/download/...",
    "source_type": "civitai",
    "status": "downloading",
    "total_size": 2147483648,
    "downloaded_size": 1610612736,
    "resume_position": 1610612736,
    "download_speed": 1258291.2,
    "eta_seconds": 150,
    "temp_file_path": "/tmp/download_hash.tmp",
    "final_file_path": "/models/model_name.safetensors",
    "civitai_model_id": 4201,
    "civitai_version_id": 130072,
    "download_metadata": {"additional": "metadata"},
    "error_message": null,
    "retry_count": 0,
    "max_retries": 3,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "started_at": "2024-01-01T00:05:00Z",
    "completed_at": null
  }
}
```

---

## 字段说明

### 通用字段

- **id**: 实体的唯一标识符
- **type**: 实体类型标识
- **created_at**: 创建时间（ISO 8601格式）
- **updated_at**: 更新时间（ISO 8601格式）

### 状态字段

- **status**: 实体当前状态，使用枚举值确保一致性
- **progress**: 进度百分比（0-100）
- **size**: 文件大小（字节）

### 关联字段

- **relationships**: JSON API 标准的关联数据结构
- **_hash / _id**: 外键关联字段

### 性能优化

- 简洁形式避免大文本字段（如完整prompt、description）
- 截断长文本到合理长度
- 预计算聚合字段（如image_count）
- 提供缩略图URL而非完整图像数据
