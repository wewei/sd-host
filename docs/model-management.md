# Model Management API

模型管理 API 负责 Stable Diffusion 模型的下载、查询和管理功能。

## 设计特性

- **唯一标识**: 所有模型使用 SHA256 hash 作为唯一标识符
- **智能查询**: 单一 API 处理模型信息查询和下载进度追踪
- **实时追踪**: 支持 Server-Sent Events (SSE) 实时进度追踪
- **Civitai 集成**: 专用 API 从 Civitai 平台下载模型
- **多类型支持**: 支持 Checkpoint、LoRA、ControlNet、VAE、Embedding 等模型类型

## 支持的模型类型

| 类型 | 描述 | 典型用途 | 文件扩展名 |
|------|------|----------|------------|
| `checkpoint` | 基础模型检查点 | 主要生成模型 | `.safetensors`, `.ckpt` |
| `lora` | 低秩适应模型 | 风格调节、特定对象 | `.safetensors` |
| `controlnet` | 控制网络模型 | 姿态控制、边缘检测 | `.safetensors` |
| `vae` | 变分自编码器 | 图像质量优化 | `.safetensors`, `.pt` |
| `embedding` | 文本嵌入模型 | 负面提示、风格词 | `.pt`, `.bin` |

---

## API 端点详情

### 1. GET /api/models

获取可用模型列表，支持基于 JSON API 标准的高级查询和过滤。

📖 **查询语法详细说明**: [实体查询协议 (JSON API)](./entity-query-protocol.md)

**基础查询参数:**

- `page[number]` - 页码 (从 1 开始，默认 1)
- `page[size]` - 每页大小 (默认 50，最大 200)
- `sort` - 排序表达式 (默认 `-created_at`)
- `fields[model]` - 选择返回字段
- `filter[field]` - JSON API 过滤表达式
- `include` - 包含关联资源

**过滤表达式示例 (filter):**

- `filter[model_type]=checkpoint` - 按模型类型过滤
- `filter[name][contains]=landscape` - 按名称模糊搜索
- `filter[size][gte]=1000000000` - 按文件大小范围过滤
- `filter[tags][any]=anime` - 包含动漫标签
- `filter[tags][none]=nsfw` - 排除成人内容标签
- `filter[base_model][in]=SD1.5,SDXL` - 按基础模型过滤

**请求示例:**

```http
# 基础查询
GET /api/models?filter[model_type]=checkpoint&page[size]=20&sort=name

# 标签过滤 (使用 JSON API 过滤语法)
GET /api/models?filter[model_type]=lora&filter[tags][any]=anime&filter[tags][none]=nsfw&page[size]=20

# 大小和基础模型过滤
GET /api/models?filter[size][gte]=1000000000&filter[base_model]=SD1.5

# 基础模型过滤
GET /api/models?filter[model_type]=checkpoint&filter[base_model][contains]=SD1.5

# 名称模糊搜索
GET /api/models?filter[name][contains]=landscape&filter[model_type]=lora&filter[tags][any]=landscape

# 复合查询
GET /api/models?filter[model_type]=checkpoint&filter[tags][any]=photorealistic&filter[base_model][contains]=SDXL&filter[tags][any]=commercial
```

### 2. GET /api/models/{model_hash}

获取指定模型的元数据信息。

**响应:**

```json
{
  "data": {
    "type": "model",
    "id": "abc123...",
    "attributes": {
      "name": "stable-diffusion-v1-5",
      "model_type": "checkpoint",
      "base_model": "SD1.5",
      "size": 4200000000,
      "source_url": "https://civitai.com/models/...",
      "metadata": {
        "resolution": "512x512",
        "trigger_words": ["masterpiece"],
        "training_epochs": 100
      },
      "description": "# Stable Diffusion v1.5\n\n这是一个通用的文生图模型，适合生成各种风格的图像。\n\n## 使用建议\n- 推荐分辨率：512x512\n- CFG Scale：7-12\n- 采样步数：20-50",
      "status": "ready",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    "relationships": {
      "tags": {
        "data": [
          {"type": "tag", "id": "photorealistic"},
          {"type": "tag", "id": "general"},
          {"type": "tag", "id": "portrait"},
          {"type": "tag", "id": "commercial"}
        ]
      },
      "cover_image": {
        "data": {"type": "image", "id": "def456..."}
      }
    }
  }
}
```
```

### 3. GET /api/models/{model_hash}/content

直接下载模型文件内容 (safetensors 格式)。

**响应:** 直接返回模型文件内容

**Headers:**

```http
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="model_name.safetensors"
Content-Length: 4200000000
```

### 4. POST /api/models/{model_hash}

修改指定模型的元数据。

**请求参数:**

```json
{
  "tag_high_quality": true,
  "rating": 4.8,
  "is_favorite": true,
  "custom_note": "Updated description"
}
```

**响应:**

```json
{
  "success": true,
  "updated_fields": ["tag_high_quality", "rating", "is_favorite", "custom_note"]
}
```

### 5. POST /api/models

批量修改多个模型的元数据。

**请求参数:**

```json
{
  "abc123...": {
    "tag_high_quality": true,
    "rating": 4.8
  },
  "def456...": {
    "is_favorite": true,
    "tag_anime": true
  }
}
```

**响应:**

```json
{
  "success": ["abc123...", "def456..."],
  "failed": [
    {
      "hash": "ghi789...",
      "error": "Model not found"
    }
  ]
}
```

### 6. DELETE /api/models/{model_hash}

删除指定模型。

**响应:**

```json
{
  "success": true,
  "message": "Model deleted successfully"
}
```

### 7. DELETE /api/models

批量删除多个模型。

**请求参数:**

```json
{
  "hashes": ["abc123...", "def456...", "ghi789..."]
}
```

**响应:**

```json
{
  "deleted": ["abc123...", "def456..."],
  "failed": [
    {
      "hash": "ghi789...",
      "reason": "Model in use by active task"
    }
  ],
  "count": 2
}
```

### 8. POST /api/models/add-from-civitai

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
  "hash": "abc123...",
  "status": "downloading",
  "tracking_url": "/api/models/add-from-civitai/abc123..."
}
```

### 9. GET /api/models/add-from-civitai/{model_hash}

SSE 实时追踪模型下载进度。

**SSE 下载进度示例:**

```json
data: {"status": "downloading", "progress": 45.2, "speed": "2.3MB/s", "eta": "00:02:30"}

data: {"status": "downloading", "progress": 67.8, "speed": "2.1MB/s", "eta": "00:01:45"}

data: {"status": "completed", "model_info": {...}}
```

---

## 查询示例和最佳实践

### 常见查询场景

**1. 获取所有可用的 Checkpoint 模型:**

```http
GET /api/models?type=checkpoint&status=ready&sort=name&order=asc
```

**2. 搜索特定风格的 LoRA 模型:**

```http
GET /api/models?type=lora&search=anime&take=20
```

**3. 按标签过滤写实风格模型 (必须包含 "photorealistic" 标签):**

```http
GET /api/models?type=checkpoint&tags=photorealistic&base_model=SD1.5
```

**4. 获取动漫风格但排除成人内容的 LoRA:**

```http
GET /api/models?type=lora&tags=anime&exclude_tags=nsfw,adult&take=20
```

**5. 多标签组合查询 (同时包含 "landscape" 和 "nature" 标签):**

```http
GET /api/models?tags=landscape,nature&exclude_tags=cartoon,anime
```

**6. 基础模型过滤 (只获取 SDXL 模型):**

```http
GET /api/models?base_model=SDXL&type=checkpoint&status=ready
```

**7. 分页浏览所有模型:**

```http
GET /api/models?skip=0&take=50         # 第一页
GET /api/models?skip=50&take=50        # 第二页
GET /api/models?skip=100&take=50       # 第三页
```

**8. 按大小排序查找大型模型:**

```http
GET /api/models?sort=size&order=desc&take=10
```

### 性能优化建议

- **分页查询**: 建议使用 `take` 参数限制返回数量，默认 50 条，最大 200 条
- **类型过滤**: 优先使用 `type` 参数过滤，可显著减少查询时间
- **状态过滤**: 使用 `status=ready` 只获取可用模型，避免显示下载中的模型
- **搜索优化**: `search` 参数支持模糊匹配，但建议输入至少 3 个字符
- **标签过滤**: 标签查询支持 AND 逻辑，多个标签用逗号分隔表示必须同时包含
- **排除标签**: 使用 `exclude_tags` 可以有效过滤不需要的内容类型

### 标签过滤详细说明

**正向标签过滤 (`tags`):**

- 多个标签用逗号分隔，表示 AND 关系（必须同时包含）
- 示例：`tags=anime,portrait` 表示模型必须同时有 "anime" 和 "portrait" 标签
- 标签匹配不区分大小写

**负向标签过滤 (`exclude_tags`):**

- 排除包含指定标签的模型
- 多个排除标签用逗号分隔，任意一个匹配都会被排除
- 示例：`exclude_tags=nsfw,violence` 表示排除包含 "nsfw" 或 "violence" 标签的模型

**组合使用示例:**

```http
# 查找动漫风格的人像模型，但排除成人内容
GET /api/models?type=lora&tags=anime,portrait&exclude_tags=nsfw,adult

# 查找写实风格模型，排除卡通和动漫风格
GET /api/models?tags=photorealistic&exclude_tags=cartoon,anime,stylized
```

**常用标签分类:**

- **风格标签**: `photorealistic`, `anime`, `cartoon`, `artistic`, `stylized`
- **内容标签**: `portrait`, `landscape`, `character`, `object`, `architecture`
- **质量标签**: `high-quality`, `detailed`, `professional`, `masterpiece`
- **限制标签**: `nsfw`, `adult`, `violence`, `explicit` (通常用于排除)

### 错误处理

**查询参数验证错误 (400 Bad Request):**

```json
{
  "error": "Invalid parameter",
  "details": {
    "type": "Invalid model type. Allowed: checkpoint, lora, controlnet, vae, embedding",
    "take": "Take parameter must be between 1 and 200"
  }
}
```
