# Model Management API

模型管理 API 负责 Stable Diffusion 模型的下载、查询和管理功能。

## 设计特性

- **唯一标识**: 所有模型使用 SHA256 hash 作为唯一标识符
- **智能查询**: 单一 API 处理模型信息查询和下载进度追踪
- **实时追踪**: 支持 Server-Sent Events (SSE) 实时进度追踪
- **Civitai 集成**: 专用 API 从 Civitai 平台下载模型

---

## API 端点详情

### 1. GET /api/v1/models

获取所有可用模型列表。

**响应格式:**
```json
{
  "models": [
    {
      "sha256": "abc123...",
      "name": "stable-diffusion-v1-5",
      "size": "4.2GB",
      "status": "ready",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 2. GET /api/v1/models/{model_sha256}

智能获取模型信息，根据模型状态返回不同内容。

**返回场景:**

| 模型状态 | HTTP 状态码 | 返回方式 | 说明 |
|----------|-------------|----------|------|
| 不存在 | 404 Not Found | JSON | 模型未找到 |
| 下载中 | 200 OK | SSE Stream | 保持连接，实时推送下载进度 |
| 已完成 | 200 OK | JSON | 立即返回完整模型信息 |

**SSE 下载进度示例:**
```
data: {"status": "downloading", "progress": 45.2, "speed": "2.3MB/s", "eta": "00:02:30"}

data: {"status": "downloading", "progress": 67.8, "speed": "2.1MB/s", "eta": "00:01:45"}

data: {"status": "completed", "model_info": {...}}
```

**完成状态响应:**
```json
{
  "sha256": "abc123...",
  "name": "stable-diffusion-v1-5",
  "size": "4.2GB",
  "status": "ready",
  "path": "/models/stable-diffusion-v1-5",
  "metadata": {
    "source": "civitai",
    "version": "1.5",
    "description": "..."
  }
}
```

### 3. POST /api/v1/models/add-from-civitai

从 Civitai 添加新模型。

**请求参数:**
```json
{
  "model_id": "4201",
  "version_id": "130072"
}
```

**响应:**
```json
{
  "sha256": "abc123...",
  "status": "downloading",
  "tracking_url": "/api/v1/models/abc123..."
}
```

### 4. DELETE /api/v1/models/{model_sha256}

删除指定模型。

**响应:**
```json
{
  "success": true,
  "message": "Model deleted successfully"
}
```
