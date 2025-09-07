# 实体查询协议 (Entity Query Protocol)

SD-Host 采用基于 JSON API 标准的实体查询协议，为模型管理和图像管理提供标准化且强大的查询和过滤能力。

## 设计理念

- **标准化**: 遵循 JSON API 查询标准，简洁直观
- **统一标准**: 模型和图像使用相同的查询语法
- **清晰分离**: 核心属性 (attributes) 与关系 (relationships) 分离
- **JSON 原生**: 完全基于 JSON 格式，易于解析和使用

---

## 实体结构设计

## 实体结构设计

### JSON API 规范

每个实体遵循 JSON API 标准格式：

1. **类型 (type)**: 实体类型标识符
2. **ID (id)**: 唯一标识符 
3. **属性 (attributes)**: 实体的核心数据
4. **关系 (relationships)**: 与其他实体的关联

```json
{
  "data": {
    "type": "model",
    "id": "abc123...",
    "attributes": {
      "name": "stable-diffusion-v1-5",
      "type": "checkpoint",
      "size": 4200000000,
      "created_at": "2024-01-01T00:00:00Z"
    },
    "relationships": {
      "tags": {
        "data": [
          {"type": "tag", "id": "photorealistic"},
          {"type": "tag", "id": "general"}
        ]
      }
    }
  }
}
```

## JSON API 查询语法

### 查询参数

JSON API 使用标准的查询参数进行数据过滤和操作：

**基本参数：**

- `filter[field]` - 字段过滤
- `sort` - 排序字段
- `page[size]` - 页面大小
- `page[number]` - 页面编号
- `fields[type]` - 字段选择
- `include` - 包含关联资源

### 过滤操作

**等值过滤：**

- `filter[type]=checkpoint` - 精确匹配
- `filter[name]=stable-diffusion-v1-5` - 字符串匹配

**比较操作：**

- `filter[size][gte]=1000000000` - 大于等于
- `filter[size][lte]=5000000000` - 小于等于
- `filter[size][gt]=1000000000` - 大于
- `filter[size][lt]=5000000000` - 小于

**字符串操作：**

- `filter[name][contains]=landscape` - 包含子字符串
- `filter[name][starts_with]=stable` - 以指定字符串开头
- `filter[name][ends_with]=v1-5` - 以指定字符串结尾

**数组操作：**

- `filter[type][in]=checkpoint,lora` - 包含于列表
- `filter[type][not_in]=vae,embedding` - 不包含于列表

**标签过滤：**

- `filter[tags][any]=photorealistic` - 包含指定标签
- `filter[tags][all]=anime,portrait` - 包含所有指定标签
- `filter[tags][none]=nsfw` - 不包含指定标签

### 逻辑操作符

**组合条件：**

- `and` - 逻辑与
- `or` - 逻辑或
- `not` - 逻辑非

**示例：**

```http
# 逻辑与 (默认)
filter[type]=checkpoint&filter[size][gte]=1000000000

# 逻辑或 (使用 OR 前缀)
filter[or][type]=lora&filter[or][type]=checkpoint

# 逻辑非 (使用 not 前缀)
filter[not][tags][any]=nsfw

# 复合条件
filter[type]=checkpoint&filter[or][tags][any]=high_quality&filter[or][tags][any]=popular
```

### 排序操作

**单字段排序：**

- `sort=name` - 按名称升序
- `sort=-name` - 按名称降序
- `sort=created_at` - 按创建时间升序
- `sort=-created_at` - 按创建时间降序

**多字段排序：**

```http
# 先按类型升序，再按大小降序
sort=type,-size

# 先按标签数降序，再按创建时间降序
sort=-tag_count,-created_at
```

### 分页参数

**基于页码的分页：**

- `page[number]` - 页码 (从 1 开始)
- `page[size]` - 每页大小 (默认 50，最大 200)

**基于偏移的分页：**

- `page[offset]` - 偏移量 (从 0 开始) 
- `page[limit]` - 限制数量

**示例：**

```http
# 第一页，每页 20 条
page[number]=1&page[size]=20

# 第二页，每页 20 条  
page[number]=2&page[size]=20

# 使用偏移量
page[offset]=40&page[limit]=20
```

### 字段选择

**稀疏字段集：**

- `fields[model]` - 选择模型资源的字段
- `fields[tag]` - 选择标签资源的字段

**示例：**

```http
# 只返回模型的名称和类型
fields[model]=name,type

# 返回模型和标签的指定字段
fields[model]=name,type,size&fields[tag]=name
```

### 包含关联资源

**include 参数：**

- `include=tags` - 包含标签信息
- `include=cover_image` - 包含封面图像
- `include=task` - 包含关联任务

**示例：**

```http
# 包含标签信息
include=tags

# 包含多个关联资源
include=tags,cover_image
```

---

## 模型实体标准

### 模型 JSON API 格式

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
        "resolution": 512,
        "trigger_words": ["masterpiece"],
        "training_epochs": 100
      },
      "description": "# Stable Diffusion v1.5\n\n这是一个通用的文生图模型...",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    "relationships": {
      "tags": {
        "data": [
          {"type": "tag", "id": "photorealistic"},
          {"type": "tag", "id": "general"},
          {"type": "tag", "id": "portrait"}
        ]
      },
      "cover_image": {
        "data": {"type": "image", "id": "def456..."}
      }
    }
  }
}
```

### 模型标签分类

模型标签采用分类标记方式：

```json
{
  "relationships": {
    "tags": {
      "data": [
        // 风格标签
        {"type": "tag", "id": "photorealistic"},
        {"type": "tag", "id": "anime"},
        {"type": "tag", "id": "cartoon"},
        
        // 内容标签  
        {"type": "tag", "id": "portrait"},
        {"type": "tag", "id": "landscape"},
        {"type": "tag", "id": "character"},
        
        // 质量标签
        {"type": "tag", "id": "high-quality"},
        {"type": "tag", "id": "detailed"},
        
        // 特殊标签
        {"type": "tag", "id": "commercial"},
        {"type": "tag", "id": "nsfw"}
      ]
    }
  }
}
```

## 图像实体标准

### 图像 JSON API 格式

```json
{
  "data": {
    "type": "image",
    "id": "def456...",
    "attributes": {
      "width": 512,
      "height": 512,
      "size": 1024000,
      "seed": 1234567890,
      "created_at": "2024-01-01T00:00:00Z"
    },
    "relationships": {
      "task": {
        "data": {"type": "task", "id": "uuid-123..."}
      },
      "tags": {
        "data": [
          {"type": "tag", "id": "landscape"},
          {"type": "tag", "id": "nature"},
          {"type": "tag", "id": "high-quality"}
        ]
      }
    }
  }
}
```

### 图像标签分类

图像标签用于内容分类和快速筛选：

```json
{
  "relationships": {
    "tags": {
      "data": [
        // 内容标签
        {"type": "tag", "id": "landscape"},
        {"type": "tag", "id": "portrait"},
        {"type": "tag", "id": "nature"},
        
        // 风格标签
        {"type": "tag", "id": "photorealistic"},
        {"type": "tag", "id": "anime"},
        {"type": "tag", "id": "artistic"},
        
        // 质量标签  
        {"type": "tag", "id": "high-quality"},
        {"type": "tag", "id": "detailed"},
        {"type": "tag", "id": "masterpiece"},
        
        // 特殊标签
        {"type": "tag", "id": "favorite"},
        {"type": "tag", "id": "wallpaper"},
        {"type": "tag", "id": "nsfw"}
      ]
    }
  }
}
```

## 任务实体标准

### 任务 JSON API 格式

任务包含生成参数，图像通过 task_id 关联到任务获取生成信息：

```json
{
  "data": {
    "type": "task",
    "id": "uuid-123...",
    "attributes": {
      "status": "completed",
      "prompt": "a beautiful landscape, masterpiece, high quality",
      "negative_prompt": "blurry, low quality, worst quality",
      "width": 768,
      "height": 768,
      "seed": 1234567890,
      "steps": 30,
      "cfg_scale": 8.0,
      "sampler": "DPM++ 2M Karras",
      "batch_size": 4,
      "error_message": null,
      "created_at": "2024-01-01T00:00:00Z",
      "promoted_at": "2024-01-01T00:05:00Z",
      "completed_at": "2024-01-01T00:05:45Z",
      "updated_at": "2024-01-01T00:05:45Z"
    },
    "relationships": {
      "checkpoint": {
        "data": {"type": "model", "id": "abc123..."}
      },
      "vae": {
        "data": {"type": "model", "id": "vae456..."}
      },
      "additional_models": {
        "data": [
          {"type": "task_model", "id": "tm_001"}
        ]
      },
      "tags": {
        "data": [
          {"type": "tag", "id": "landscape"},
          {"type": "tag", "id": "batch_generation"}
        ]
      }
    }
  },
  "included": [
    {
      "type": "task_model",
      "id": "tm_001",
      "attributes": {
        "weight": 0.8
      },
      "relationships": {
        "model": {
          "data": {"type": "model", "id": "lora123..."}
        }
      }
    }
  ]
}
```

---

## JSON API 查询示例

### 模型查询示例

**1. 基本属性过滤：**

```http
# 基础过滤
GET /api/models?filter[model_type]=checkpoint&filter[base_model]=SD1.5

# 数值范围过滤
GET /api/models?filter[size][gte]=1000000000

# 字符串模糊匹配
GET /api/models?filter[name][contains]=landscape
```

**2. 标签查询：**

```http
# 包含指定标签
GET /api/models?filter[tags][any]=photorealistic

# 包含任一标签
GET /api/models?filter[tags][any]=anime,portrait

# 同时包含多个标签
GET /api/models?filter[tags][all]=anime,portrait

# 包含指定标签但排除其他标签
GET /api/models?filter[tags][any]=photorealistic&filter[tags][none]=nsfw
```

**3. 复合查询：**

```http
# 高质量动漫风格LoRA，排除成人内容
GET /api/models?filter[model_type]=lora&filter[tags][any]=anime&filter[tags][all]=high_quality&filter[tags][none]=nsfw

# 大型写实风格Checkpoint
GET /api/models?filter[model_type]=checkpoint&filter[tags][any]=photorealistic&filter[size][gte]=2000000000&filter[tags][any]=commercial
```

**4. 分页和排序：**

```http
# 按创建时间降序，分页显示
GET /api/models?filter[model_type]=checkpoint&sort=-created_at&page[number]=1&page[size]=20

# 多字段排序
GET /api/models?sort=model_type,-size,-created_at&page[size]=50
```

### 图像查询示例

**1. 基本属性过滤：**

```http
# 基础过滤
GET /api/images?filter[task_id][not_null]=true

# 分辨率过滤
GET /api/images?filter[width][gte]=1024&filter[height][gte]=1024&filter[tags][any]=high_quality

# 种子过滤
GET /api/images?filter[seed]=1234567890
```

**2. 标签查询：**

```http
# 包含风景标签
GET /api/images?filter[tags][any]=landscape

# 高质量人像，排除成人内容
GET /api/images?filter[tags][any]=portrait,high-quality&filter[tags][none]=nsfw

# 收藏的动漫风格图像
GET /api/images?filter[tags][all]=anime,favorite
```

**3. 关联查询：**

```http
# 包含任务信息
GET /api/images?include=task

# 包含标签和任务信息
GET /api/images?include=tags,task&fields[image]=width,height,seed&fields[task]=prompt,steps
```

**4. 字段选择和分页：**

```http
# 只返回基本信息
GET /api/images?fields[image]=width,height,size&page[size]=20

# 选择特定字段组合
GET /api/images?filter[tags][any]=favorite&fields[image]=size,seed&sort=-created_at
```

### 任务查询示例

**1. 状态过滤：**

```http
# 已完成的任务
GET /api/tasks?filter[status]=completed

# 失败的任务
GET /api/tasks?filter[status]=failed&include=checkpoint
```

**2. 生成参数过滤：**

```http
# 按步数和CFG过滤
GET /api/tasks?filter[steps][gte]=20&filter[cfg_scale][gte]=7.0

# 按采样器过滤
GET /api/tasks?filter[sampler][contains]=DPM

# 特定分辨率任务
GET /api/tasks?filter[width]=1024&filter[height]=1024
```

**3. 关联查询：**

```http
# 包含模型和标签信息
GET /api/tasks?include=checkpoint,vae,tags&filter[status]=completed

# 包含附加模型信息
GET /api/tasks?include=checkpoint,additional_models.model&fields[task]=prompt,steps,cfg_scale
```

---

## JSON API 响应格式

### 成功响应格式

**单个资源：**

```json
{
  "data": {
    "type": "model",
    "id": "abc123...",
    "attributes": { /* ... */ },
    "relationships": { /* ... */ }
  },
  "included": [ /* 相关资源 */ ]
}
```

**资源集合：**

```json
{
  "data": [
    {
      "type": "model",
      "id": "abc123...",
      "attributes": { /* ... */ },
      "relationships": { /* ... */ }
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
    "self": "/api/models?page[number]=1&page[size]=20",
    "next": "/api/models?page[number]=2&page[size]=20",
    "last": "/api/models?page[number]=8&page[size]=20"
  },
  "included": [ /* 相关资源 */ ]
}
```

### 性能优化建议

1. **字段选择**: 使用 `fields[type]` 参数只获取需要的字段
2. **分页控制**: 合理设置 `page[size]`，避免一次获取过多数据
3. **关联资源**: 按需使用 `include` 参数，避免不必要的数据传输
4. **过滤优化**: 使用索引字段进行过滤，提升查询效率
5. **缓存策略**: 对频繁查询的结果进行客户端缓存

---

## 错误处理

### 查询参数错误 (400 Bad Request)

```json
{
  "errors": [
    {
      "status": "400",
      "code": "invalid_filter",
      "title": "Invalid Filter Parameter",
      "detail": "The filter[size][xyz] operation is not supported",
      "source": {
        "parameter": "filter[size][xyz]"
      }
    }
  ]
}
```

### 不支持的操作错误

```json
{
  "errors": [
    {
      "status": "400",
      "code": "unsupported_operation",
      "title": "Unsupported Operation",
      "detail": "The 'regex' operation is not supported for string fields",
      "source": {
        "parameter": "filter[name][regex]"
      }
    }
  ]
}
```

### 标签查询错误

```json
{
  "errors": [
    {
      "status": "400",
      "code": "invalid_tag_filter",
      "title": "Invalid Tag Filter",
      "detail": "Tag filter operation 'invalid_op' is not supported. Use 'any', 'all', or 'none'",
      "source": {
        "parameter": "filter[tags][invalid_op]"
      }
    }
  ]
}
```
