# Image Management API

图像管理 API 负责所有类型图像的存储、查询和元数据管理功能。

## 设计特性

- **唯一标识**: 所有图像使用文件内容的哈希值作为唯一标识符（SHA256）
- **自动去重**: 天然实现图像去重，相同内容的图像共享同一个 ID
- **统一API**: 与模型管理API保持完全一致的设计模式
- **元数据系统**: 使用统一的查询语法，支持类型推断

---

## API 端点详情

### 1. GET /api/images

查询图像，使用 JSON API 标准查询协议进行过滤，返回图像哈希列表和属性。

📖 **查询语法详细说明**: [实体查询协议 (JSON API)](./entity-query-protocol.md)

**基础查询参数:**

- `page[number]` - 页码 (从 1 开始，默认 1)
- `page[size]` - 每页大小 (默认 50，最大 200)
- `sort` - 排序表达式 (默认 `-created_at`)
- `fields[image]` - 选择返回字段
- `filter[field]` - JSON API 过滤表达式
- `include` - 包含关联资源

**过滤表达式示例 (filter):**

- `filter[width][gte]=1024` - 按宽度过滤
- `filter[seed]=1234567890` - 按随机种子过滤
- `filter[tags][any]=landscape` - 包含风景标签
- `filter[tags][none]=nsfw` - 排除成人内容标签
- `filter[task_id]=uuid-123` - 按关联任务过滤

**响应:**

```json
{
  "data": [
    {
      "type": "image",
      "id": "abc123...",
      "attributes": {
        "width": 512,
        "height": 512,
        "size": 1024000,
        "seed": 1234567890,
        "created_at": "2024-01-01T00:00:00Z"
      },
      "relationships": {
        "task": {
          "data": {"type": "task", "id": "uuid-789..."}
        },
        "tags": {
          "data": [
            {"type": "tag", "id": "landscape"},
            {"type": "tag", "id": "high_quality"},
            {"type": "tag", "id": "favorite"}
          ]
        }
      }
    }
  ],
  "meta": {
    "total": 156,
    "page": {
      "number": 1,
      "size": 20,
      "total": 8
    }
  },
  "links": {
    "self": "/api/images?page[number]=1&page[size]=20",
    "next": "/api/images?page[number]=2&page[size]=20"
  }
}
```

### 2. GET /api/images/{image_hash}

获取指定图像的元数据信息。

**响应:**

```json
{
  "data": {
    "type": "image",
    "id": "abc123...",
    "attributes": {
      "width": 512,
      "height": 512,
      "size": 1024000,
      "seed": 1234567890,
      "created_at": "2024-01-01T00:00:00Z"
    },
    "relationships": {
      "task": {
        "data": {"type": "task", "id": "uuid-789..."}
      },
      "tags": {
        "data": [
          {"type": "tag", "id": "landscape"},
          {"type": "tag", "id": "nature"},
          {"type": "tag", "id": "high_quality"}
        ]
      }
    }
  }
}
```

### 3. GET /api/images/{image_hash}/content

直接获取图像文件内容。

**响应:** 直接返回图像文件（PNG/JPEG/WebP 等格式）

**Headers:**

```http
Content-Type: image/png
Content-Length: 1234567
```

### 4. POST /api/images/{image_hash}

修改指定图像的元数据。

**请求参数:**

```json
{
  "rating": 4.8,
  "tag_masterpiece": true,
  "is_favorite": true,
  "custom_note": "Beautiful composition"
}
```

**响应:**

```json
{
  "success": true,
  "updated_fields": ["rating", "tag_masterpiece", "is_favorite", "custom_note"]
}
```

### 5. POST /api/images

批量修改多个图像的元数据。

**请求参数:**

```json
{
  "abc123...": {
    "rating": 4.8,
    "is_favorite": true
  },
  "def456...": {
    "tag_masterpiece": true,
    "is_public": true
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
      "error": "Image not found"
    }
  ]
}
```

### 6. DELETE /api/images/{image_hash}

删除指定图像。

**响应:**

```json
{
  "success": true,
  "message": "Image deleted successfully"
}
```

### 7. DELETE /api/images

批量删除多个图像。

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
      "reason": "File not found"
    }
  ],
  "count": 2
}
```

---

## 元数据查询示例

### 常见查询场景

**1. 查找收藏的高质量图像:**

```http
GET /api/images?filter[tags][all]=favorite,high_quality
```

**2. 按分辨率过滤:**

```http
GET /api/images?filter[width][gte]=1024&filter[height][gte]=1024
```

**3. 查找特定风格图像，排除成人内容:**

```http
GET /api/images?filter[tags][any]=landscape,nature&filter[tags][none]=nsfw&page[size]=50
```

**4. 按关联任务查询:**

```http
GET /api/images?filter[task_id][not_null]=true&include=task
```

### 批量操作示例

**批量设置标签:**

```http
POST /api/images
{
  "abc123...": {"tags": ["masterpiece", "favorite"]},
  "def456...": {"tags": ["high_quality", "landscape"]}
}
```

**批量删除低质量图像:**

```http
DELETE /api/images
{
  "data": [
    {"type": "image", "id": "hash1..."},
    {"type": "image", "id": "hash2..."},
    {"type": "image", "id": "hash3..."}
  ]
}
```
