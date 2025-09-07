# Image Management API

图像管理 API 负责所有类型图像的存储、查询和元数据管理功能。

## 设计特性

- **唯一标识**: 所有图像使用文件内容的哈希值作为唯一标识符（SHA256）
- **自动去重**: 天然实现图像去重，相同内容的图像共享同一个 ID
- **元数据系统**: 使用基于属性的 metadata 系统，支持多种数据类型
- **类型安全**: 使用前缀约定来区分数据类型，避免类型冲突

## Metadata 类型系统

### 数据类型前缀约定

| 前缀 | 数据类型 | 示例 | 默认值 |
|------|----------|------|---------|
| `@` | string | `@type: "realistic"` | `""` (空字符串) |
| `#` | number | `#rating: 4.5` | `0` |
| `*` | set | `*tags: ["tag1", "tag2"]` | `[]` (空集合) |
| `?` | boolean | `?is_favorite: true` | `false` |

### Metadata 示例

```json
{
  "@type": "generated",
  "@model": "stable-diffusion-v1-5",
  "@style": "realistic",
  "#resolution": 512,
  "#rating": 4.5,
  "#steps": 20,
  "*tags": ["landscape", "high-quality", "AI"],
  "*loras": ["lora1", "lora2"],
  "?is_favorite": true,
  "?is_public": false,
  "?is_nsfw": false
}
```

---

## API 端点详情

### 1. GET /api/v1/images/{image_hash}

获取图像数据，直接返回图像文件内容。

**响应:** 直接返回图像文件（PNG/JPEG/WebP 等格式）

**Headers:**
```
Content-Type: image/png
Content-Length: 1234567
```

### 2. POST /api/v1/images/{image_hash}/metadata

为图像设置元数据属性。新属性会覆盖同类型旧属性。

**请求参数:**

```json
{
  "@style": "photorealistic",
  "#rating": 4.8,
  "*tags": ["portrait", "high-quality"],
  "?is_favorite": true
}
```

**响应:**

```json
{
  "success": true,
  "updated_metadata": {
    "@style": "photorealistic",
    "#rating": 4.8,
    "*tags": ["portrait", "high-quality"],
    "?is_favorite": true
  }
}
```

### 3. GET /api/v1/images

查询图像，按属性过滤，返回图像哈希列表和元数据。

**查询参数:**
- `@type=generated` - 字符串类型过滤
- `#rating>=4.0` - 数字类型范围过滤
- `*tags=landscape` - 集合类型包含过滤
- `?is_favorite=true` - 布尔类型过滤
- `limit=20` - 限制返回数量
- `offset=0` - 分页偏移

**响应:**

```json
{
  "images": [
    {
      "hash": "abc123...",
      "metadata": {
        "@type": "generated",
        "@model": "stable-diffusion-v1-5",
        "#rating": 4.5,
        "*tags": ["landscape", "high-quality"],
        "?is_favorite": true
      }
    }
  ],
  "total": 156,
  "limit": 20,
  "offset": 0
}
```

### 4. DELETE /api/v1/images

删除图像，支持按哈希列表或元数据属性条件批量删除。

**按哈希删除:**

```json
{
  "hashes": ["abc123...", "def456..."]
}
```

**按条件删除:**

```json
{
  "conditions": {
    "#rating": {"<": 2.0},
    "?is_public": false
  }
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

## 高级查询语法

### 数字类型查询
- `#rating=4.5` - 等于
- `#rating>=4.0` - 大于等于
- `#rating<3.0` - 小于
- `#steps=20,25,30` - 多值匹配

### 集合类型查询
- `*tags=landscape` - 包含标签
- `*tags=landscape,portrait` - 包含任一标签
- `*tags=landscape&portrait` - 同时包含多个标签

### 字符串类型查询
- `@model=stable-diffusion-v1-5` - 精确匹配
- `@style=realistic,photorealistic` - 多值匹配
