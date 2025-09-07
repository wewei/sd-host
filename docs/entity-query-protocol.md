# 实体查询协议 (Entity Query Protocol)

SD-Host 采用基于 OData 标准的实体查询协议，为模型管理和图像管理提供标准化且强大的查询和过滤能力。

## 设计理念

- **标准化**: 遵循 OData 查询标准，与业界最佳实践保持一致
- **统一标准**: 模型和图像使用相同的查询语法
- **清晰分离**: 核心属性 (properties) 与标签系统 (tags) 分离
- **URL友好**: 符合 OData URL 编码规范

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

## OData 查询语法

### $filter 查询表达式

基于 OData v4 标准的 `$filter` 查询参数进行实体过滤。

### 比较操作符

**等值比较:**

- `name eq 'stable-diffusion-v1-5'` - 精确匹配
- `name ne 'old-model'` - 不等于
- `type eq 'checkpoint'` - 类型匹配

**数值比较:**

- `size gt 1000000000` - 大于
- `size ge 1000000000` - 大于等于
- `size lt 5000000000` - 小于  
- `size le 5000000000` - 小于等于
- `width eq 1024` - 等于

**字符串操作:**

- `contains(name, 'landscape')` - 包含子字符串
- `startswith(name, 'stable')` - 以指定字符串开头
- `endswith(name, 'v1-5')` - 以指定字符串结尾

**基于标签的查询:**

- `tags/any(t: t eq 'nsfw')` - 包含特定标签
- `not tags/any(t: t eq 'nsfw')` - 不包含特定标签

### 逻辑操作符

**组合条件:**

- `and` - 逻辑与
- `or` - 逻辑或  
- `not` - 逻辑非

**示例:**

```http
# 逻辑与
$filter=type eq 'checkpoint' and size ge 1000000000

# 逻辑或
$filter=type eq 'lora' or type eq 'checkpoint'

# 逻辑非
$filter=not tags/any(t: t eq 'nsfw')

# 复合条件
$filter=type eq 'checkpoint' and (tags/any(t: t eq 'high_quality') or tags/any(t: t eq 'popular'))
```

### 标签查询扩展

虽然 OData 标准不直接支持数组查询，我们扩展了标签查询语法：

**标签包含:**

- `tags/any(t: t eq 'landscape')` - 包含指定标签
- `tags/any(t: t eq 'anime' or t eq 'portrait')` - 包含任一标签

**标签排除:**

- `not tags/any(t: t eq 'nsfw')` - 不包含指定标签

**标签组合:**

```http
# 同时包含多个标签
$filter=tags/any(t: t eq 'anime') and tags/any(t: t eq 'portrait')

# 包含指定标签但排除其他标签
$filter=tags/any(t: t eq 'photorealistic') and not tags/any(t: t eq 'nsfw')
```

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
  "sourceUrl": "https://civitai.com/models/...", // 下载来源URL
  "metadata": "{\"resolution\": 512, \"trigger_words\": [\"masterpiece\"], \"training_epochs\": 100}", // 模型参数信息 (JSON)
  "description": "# Stable Diffusion v1.5\n\n这是一个通用的文生图模型...", // 模型描述 (Markdown)
  "cover_image_hash": "def456...",  // 封面图像哈希 (可选)
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
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
  "task_id": "uuid-123...",         // 关联任务ID (可选，间接关联模型)
  "width": 512,                     // 宽度
  "height": 512,                    // 高度
  "size": 1024000,                  // 文件大小 (字节)
  "seed": 1234567890,               // 随机种子
  "created_at": "2024-01-01T00:00:00Z"
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

### 任务核心属性 (Properties)

任务包含生成参数，图像通过 task_id 关联到任务获取生成信息：

```json
{
  "id": "uuid-123...",              // 任务唯一标识 (UUID)
  "status": "completed",            // 任务状态 (pending, completed, failed, cancelled)
  "checkpoint_hash": "abc123...",   // 主模型 (Checkpoint)
  
  // 生成参数
  "prompt": "a beautiful landscape, masterpiece, high quality",
  "negative_prompt": "blurry, low quality, worst quality",
  "width": 768,
  "height": 768,
  "seed": 1234567890,
  "steps": 30,
  "cfg_scale": 8.0,
  "sampler": "DPM++ 2M Karras",
  "batch_size": 4,
  "vae_hash": "vae456...",          // VAE 模型 (可选)
  
  // 时间戳
  "created_at": "2024-01-01T00:00:00Z",
  "promoted_at": "2024-01-01T00:05:00Z",
  "completed_at": "2024-01-01T00:05:45Z",
  
  // 关联的非 checkpoint 模型
  "additional_models": [
    {
      "model_hash": "lora123...",
      "weight": 0.8
    },
    {
      "model_hash": "controlnet456...",
      "weight": 1.0
    }
  ]
}
```

---

## OData 查询示例

### 模型查询示例

**1. 基本属性过滤:**

```http
# 基础过滤
GET /api/models?$filter=type eq 'checkpoint' and base_model eq 'SD1.5'

# 数值范围过滤
GET /api/models?$filter=size ge 1000000000 and rating ge 4.5

# 字符串模糊匹配
GET /api/models?$filter=contains(name, 'landscape') and is_commercial eq true
```

**2. 标签查询:**

```http
# 包含指定标签
GET /api/models?$filter=tags/any(t: t eq 'photorealistic')

# 包含任一标签
GET /api/models?$filter=tags/any(t: t eq 'anime' or t eq 'portrait')

# 同时包含多个标签
GET /api/models?$filter=tags/any(t: t eq 'anime') and tags/any(t: t eq 'portrait')

# 包含指定标签但排除其他标签
GET /api/models?$filter=tags/any(t: t eq 'photorealistic') and not tags/any(t: t eq 'nsfw')
```

**3. 复合查询:**

```http
# 高质量动漫风格LoRA，排除成人内容
GET /api/models?$filter=type eq 'lora' and tags/any(t: t eq 'anime') and not tags/any(t: t eq 'nsfw') and tags/any(t: t eq 'high_quality')

# 大型写实风格Checkpoint
GET /api/models?$filter=type eq 'checkpoint' and tags/any(t: t eq 'photorealistic') and size ge 2000000000 and tags/any(t: t eq 'commercial')
```

**4. 分页和排序:**

```http
# 按创建时间降序，分页显示
GET /api/models?$filter=type eq 'checkpoint'&$orderby=created_at desc&$top=20&$skip=0

# 多字段排序
GET /api/models?$orderby=type asc, size desc, created_at desc&$top=50
```

### 图像查询示例

**1. 基本属性过滤:**

```http
# 基础过滤
GET /api/images?$filter=task_id ne null

# 分辨率过滤
GET /api/images?$filter=width ge 1024 and height ge 1024 and tags/any(t: t eq 'high_quality')

# 种子过滤
GET /api/images?$filter=seed eq 1234567890
```

**2. 标签查询:**

```http
# 包含风景标签
GET /api/images?$filter=tags/any(t: t eq 'landscape')

# 高质量人像，排除成人内容
GET /api/images?$filter=tags/any(t: t eq 'portrait' or t eq 'high-quality') and not tags/any(t: t eq 'nsfw')

# 收藏的动漫风格图像
GET /api/images?$filter=tags/any(t: t eq 'anime') and is_favorite eq true
```

**3. 生成参数查询:**

```http
# 按生成参数过滤
GET /api/images?$filter=steps ge 20 and cfg_scale ge 7.0 and contains(sampler, 'DPM')

# 特定种子范围的图像
GET /api/images?$filter=seed ge 1000000 and seed le 9999999

# 复合生成参数查询
GET /api/images?$filter=type eq 'generated' and steps ge 20 and contains(prompt, 'landscape') and not tags/any(t: t eq 'nsfw')
```

**4. 字段选择和分页:**

```http
# 只返回基本信息
GET /api/images?$select=hash,type,width,height,rating&$top=20

# 选择特定字段组合
GET /api/images?$filter=is_favorite eq true&$select=hash,model,prompt,rating,tags&$orderby=created_at desc
```

## OData 查询参数

### 分页参数

- `$skip` - 跳过记录数 (分页偏移，默认 0)
- `$top` - 获取记录数 (分页大小，默认 50，最大 200)

### 排序参数

- `$orderby` - 排序表达式，支持多字段排序

**示例:**

```http
# 按单一字段排序
$orderby=rating desc

# 按多字段排序  
$orderby=type asc, rating desc, created_at desc

# 组合分页和排序
$top=20&$skip=40&$orderby=size desc
```

### 字段选择

- `$select` - 选择返回的字段

**示例:**

```http
# 只返回基本信息
$select=hash,name,type,size

# 返回指定字段组合
$select=hash,name,rating,tags
```

---

## 性能优化建议

1. **$filter 优化**: 将选择性高的条件放在前面，利用短路求值
2. **索引字段**: 核心属性通常已建立索引，查询效率更高
3. **标签查询**: 合理使用标签的 any/all 操作符，避免过度复杂的表达式
4. **$top 控制**: 使用适当的 `$top` 值，避免返回过多结果
5. **$select 优化**: 只选择需要的字段，减少数据传输量

---

## 错误处理

### OData 查询错误 (400 Bad Request)

```json
{
  "error": {
    "code": "InvalidFilter",
    "message": "The $filter expression is invalid",
    "details": {
      "expression": "size ge abc",
      "issue": "Cannot convert 'abc' to type 'Edm.Int64'"
    }
  }
}
```

### 不支持的操作错误

```json
{
  "error": {
    "code": "UnsupportedFunction", 
    "message": "The function 'regex' is not supported in $filter expressions",
    "target": "$filter"
  }
}
```

### 标签查询错误

```json
{
  "error": {
    "code": "InvalidLambdaExpression",
    "message": "Invalid lambda expression in tags collection filter",
    "details": {
      "expression": "tags/any(t: t contains 'invalid')",
      "issue": "String function 'contains' requires two parameters"
    }
  }
}
```
