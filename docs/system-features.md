# System Features API

系统功能 API 提供基本的系统信息查询功能，适用于单用户本地部署或局域网访问场景。

## 设计特性

- **无认证设计**: 单用户系统，无需登录/登出功能
- **本地优化**: 针对本地或局域网使用场景优化
- **极简配置**: 只保留版本信息和配置查询功能

---

## API 端点详情

### 1. GET /api/version

获取 API 版本信息和系统版本。

**响应:**

```json
{
  "api_version": "1.0.0",
  "system_version": "2024.1.0",
  "build_date": "2024-01-01T00:00:00Z",
  "git_commit": "abc123...",
  "python_version": "3.11.5",
  "pytorch_version": "2.1.0",
  "cuda_version": "12.1",
  "platform": "linux-x86_64"
}
```

### 2. GET /api/config

获取系统配置信息（不包含敏感信息）。

**响应:**

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 1
  },
  "storage": {
    "models_path": "/app/models",
    "images_path": "/app/images",
    "cache_path": "/app/cache"
  },
  "generation": {
    "default_steps": 20,
    "default_cfg_scale": 7.0,
    "max_batch_size": 4,
    "safety_checker": true
  },
  "hardware": {
    "device": "cuda",
    "gpu_count": 1,
    "memory_gb": 24
  },
  "features": {
    "civitai_enabled": true,
    "auto_download": true,
    "queue_enabled": true
  }
}
```

## 使用场景

### 版本检查

客户端可以使用版本 API 来验证兼容性：

```javascript
const response = await fetch('/api/version');
const version = await response.json();
if (version.api_version !== '1.0.0') {
  console.warn('API version mismatch');
}
```

### 配置验证

获取当前系统配置来调整客户端行为：

```javascript
const response = await fetch('/api/config');
const config = await response.json();
if (!config.features.civitai_enabled) {
  // 隐藏 Civitai 相关功能
}
```
