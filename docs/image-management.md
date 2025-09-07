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

查询图像，使用 OData 标准查询协议进行过滤，返回图像哈希列表和属性。

📖 **查询语法详细说明**: [实体查询协议 (OData)](./entity-query-protocol.md)

**基础查询参数:**

- `$skip` - 跳过记录数 (分页偏移，默认 0)
- `$top` - 获取记录数 (分页大小，默认 50，最大 200)
- `$orderby` - 排序表达式 (默认 `created_at desc`)
- `$select` - 选择返回字段
- `$filter` - OData 过滤表达式

**过滤表达式示例 ($filter):**

- `width ge 1024` - 按宽度过滤
- `seed eq 1234567890` - 按随机种子过滤
- `tags/any(t: t eq 'landscape')` - 包含风景标签
- `not tags/any(t: t eq 'nsfw')` - 排除成人内容标签
- `task_id eq 'uuid-123'` - 按关联任务过滤

**响应:**

```json
{
  "images": [
    {
      "hash": "abc123...",
      "metadata": {
        "type": "generated",
        "model": "stable-diffusion-v1-5",
        "width": 512,
        "height": 512,
        "rating": 4.5,
        "tag_landscape": true,
        "tag_high_quality": true,
        "is_favorite": true,
        "is_nsfw": false
      }
    }
  ],
  "pagination": {
    "total": 156,
    "skip": 0,
    "take": 20,
    "has_more": true
  }
}
```

### 2. GET /api/images/{image_hash}

获取指定图像的元数据信息。

**响应:**

```json
{
  "hash": "abc123...",
  "task_id": "uuid-789...",
  "width": 512,
  "height": 512,
  "size": 1024000,
  "seed": 1234567890,
  "created_at": "2024-01-01T00:00:00Z",
  "tags": ["landscape", "nature", "high_quality"]
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
GET /api/images?is_favorite&rating>=4.5&tag_high_quality
```

**2. 按模型和分辨率过滤:**

```http
GET /api/images?model~stable-diffusion&width>=1024&height>=1024
```

**3. 查找特定风格图像，排除成人内容:**

```http
GET /api/images?tag_landscape&tag_nature&!is_nsfw&take=50
```

**4. 按生成参数查询:**

```http
GET /api/images?steps>=20&cfg_scale>=7.0&!tag_nsfw
```

### 批量操作示例

**批量设置评分:**

```http
POST /api/images
{
  "abc123...": {"rating": 5.0, "tag_masterpiece": true},
  "def456...": {"rating": 4.8, "is_favorite": true}
}
```

**批量删除低质量图像:**

```http
DELETE /api/images
{
  "hashes": ["hash1...", "hash2...", "hash3..."]
}
```
