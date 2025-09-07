# 实体查询协议 (Entity Query Protocol)

SD-Host 采用统一的实体查询协议，为模型管理和图像管理提供一致且直观的查询和过滤能力。

## 设计理念

- **简洁直观**: 实体属性直接查询，无需复杂的类型系统
- **统一标准**: 模型和图像使用相同的查询语法
- **清晰分离**: 核心属性 (properties) 与标签系统 (tags) 分离
- **URL友好**: 所有语法都是URL安全的，无需特殊编码

---

## 实体结构设计

### 实体组成

每个实体由两部分组成：

1. **核心属性 (Properties)**: 实体的基本信息和固定属性
2. **标签系统 (Tags)**: 灵活的标记和分类系统

```json
{
  // 核心属性 - 固定字段
  "hash": "abc123...",
  "name": "stable-diffusion-v1-5",
  "type": "checkpoint",
  "size": 4200000000,
  "created_at": "2024-01-01T00:00:00Z",
  
  // 标签系统 - 灵活标记
  "tags": ["photorealistic", "general", "portrait"]
}
```

## 查询语法

### 属性查询操作符

**字符串属性:**

- `name=value` - 精确匹配
- `name!=value` - 不等于  
- `name~value` - 模糊匹配 (包含子字符串)

**数字属性:**

- `size=123` - 等于
- `size!=123` - 不等于
- `size>123` - 大于
- `size>=123` - 大于等于
- `size<123` - 小于
- `size<=123` - 小于等于

**布尔属性:**

- `is_nsfw=true` - 为真
- `is_nsfw=false` - 为假

### 标签查询操作符

**标签包含:**

- `tags=landscape` - 包含指定标签
- `tags=landscape,portrait` - 包含任一标签 (OR 关系)

**标签排除:**

- `!tags=nsfw` - 不包含指定标签
- `!tags=nsfw,adult` - 不包含任一指定标签

**标签组合:**

- `tags=anime&tags=portrait` - 同时包含多个标签 (AND 关系)
- `tags=landscape&!tags=nsfw` - 包含指定标签但排除其他标签

---

## 模型实体标准

### 模型核心属性 (Properties)

```json
{
  "hash": "abc123...",              // SHA256 哈希 (唯一标识)
  "name": "stable-diffusion-v1-5",  // 模型名称
  "type": "checkpoint",             // 模型类型
  "base_model": "SD1.5",           // 基础模型架构
  "size": 4200000000,              // 文件大小 (字节)
  "version": "1.5",                // 版本号
  "source": "civitai",             // 来源平台
  "resolution": 512,               // 支持分辨率
  "download_count": 150000,        // 下载次数
  "rating": 4.8,                   // 评分 (1-5)
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  
  // 布尔属性
  "is_nsfw": false,                // 是否成人内容
  "is_commercial": true,           // 是否允许商用
  "requires_trigger": false        // 是否需要触发词
}
```

### 模型标签系统 (Tags)

模型标签采用分类标记方式：

```json
{
  "tags": [
    // 风格标签
    "photorealistic", "anime", "cartoon", "artistic",
    
    // 内容标签  
    "portrait", "landscape", "character", "object",
    
    // 质量标签
    "high-quality", "detailed", "masterpiece",
    
    // 特殊标签
    "nsfw", "commercial", "free"
  ]
}
```

## 图像实体标准

### 图像核心属性 (Properties)

```json
{
  "hash": "def456...",              // SHA256 哈希 (唯一标识)
  "type": "generated",              // 图像类型
  "model": "stable-diffusion-v1-5", // 使用的模型
  "width": 512,                     // 宽度
  "height": 512,                    // 高度
  "size": 1024000,                  // 文件大小 (字节)
  "format": "png",                  // 文件格式
  "rating": 4.5,                    // 用户评分
  "created_at": "2024-01-01T00:00:00Z",
  
  // 生成参数 (generated 类型特有)
  "prompt": "a beautiful landscape",
  "negative_prompt": "blurry, low quality",
  "sampler": "DPM++ 2M Karras",
  "steps": 20,
  "cfg_scale": 7.0,
  "seed": 1234567890,
  
  // 布尔属性
  "is_favorite": true,              // 是否收藏
  "is_public": false,               // 是否公开
  "is_nsfw": false                  // 是否成人内容
}
```

### 图像标签系统 (Tags)

图像标签用于内容分类和快速筛选：

```json
{
  "tags": [
    // 内容标签
    "landscape", "portrait", "nature", "architecture",
    
    // 风格标签
    "photorealistic", "anime", "artistic", "cartoon",
    
    // 质量标签  
    "high-quality", "detailed", "masterpiece",
    
    // 特殊标签
    "nsfw", "favorite", "wallpaper"
  ]
}
```

---

## 查询语法示例

### 模型查询示例

**1. 基本属性查询:**

```http
GET /api/models?type=checkpoint&base_model=SD1.5
GET /api/models?size>=1000000000&rating>=4.5
GET /api/models?name~landscape&is_commercial=true
```

**2. 标签查询:**

```http
# 包含指定标签
GET /api/models?tags=photorealistic

# 包含任一标签 (OR 关系)
GET /api/models?tags=anime,portrait

# 同时包含多个标签 (AND 关系)  
GET /api/models?tags=anime&tags=portrait

# 包含指定标签但排除其他标签
GET /api/models?tags=photorealistic&!tags=nsfw
```

**3. 复合查询:**

```http
# 高质量动漫风格LoRA，排除成人内容
GET /api/models?type=lora&tags=anime&!tags=nsfw&rating>=4.0

# 大型写实风格Checkpoint，允许商用
GET /api/models?type=checkpoint&tags=photorealistic&size>=2000000000&is_commercial=true
```

### 图像查询示例

**1. 基本属性查询:**

```http
GET /api/images?type=generated&model=stable-diffusion-v1-5
GET /api/images?width>=1024&height>=1024&rating>=4.0
GET /api/images?is_favorite=true&is_nsfw=false
```

**2. 标签查询:**

```http
# 包含风景标签
GET /api/images?tags=landscape

# 高质量人像，排除成人内容
GET /api/images?tags=portrait,high-quality&!tags=nsfw

# 收藏的动漫风格图像
GET /api/images?tags=anime&is_favorite=true
```

**3. 生成参数查询:**

```http
# 按生成参数过滤
GET /api/images?steps>=20&cfg_scale>=7.0&sampler~DPM

# 特定种子范围的图像
GET /api/images?seed>=1000000&seed<=9999999
```

---

## 分页和排序

### 分页参数

- `skip` - 跳过记录数 (分页偏移，默认 0)
- `take` - 获取记录数 (分页大小，默认 50，最大 200)

### 排序参数

- `sort` - 排序字段 (支持任何核心属性，默认 `created_at`)
- `order` - 排序顺序 (`asc`, `desc`, 默认 `desc`)

### 示例

```http
# 按评分降序，分页显示
GET /api/models?type=checkpoint&sort=rating&order=desc&skip=0&take=20

# 按创建时间排序
GET /api/images?sort=created_at&order=desc&skip=50&take=25

# 按大小排序查找大型模型
GET /api/models?sort=size&order=desc&take=10
```

---

## 性能优化建议

1. **类型过滤优先**: 优先使用 `type` 参数过滤，可显著减少查询时间
2. **索引字段**: 核心属性通常已建立索引，查询效率更高
3. **标签组合**: 合理使用标签的 AND/OR 组合，避免过度复杂的查询
4. **分页控制**: 使用适当的 `take` 值，避免返回过多结果
5. **范围查询**: 数字范围查询 (`>=`, `<=`) 比精确匹配更灵活

---

## 错误处理

### 查询参数验证错误 (400 Bad Request)

```json
{
  "error": "Invalid query parameter",
  "details": {
    "size": "Invalid number format",
    "tags": "Invalid tag format",
    "type": "Invalid entity type"
  }
}
```

### 不支持的操作符错误

```json
{
  "error": "Unsupported operator",
  "message": "String fields do not support '>' operator. Use '=', '!=' or '~'"
}
```
