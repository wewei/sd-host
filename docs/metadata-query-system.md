# 元数据查询系统 (Metadata Query System)

SD-Host 采用统一的基于元数据的查询系统，为模型管理和图像管理提供一致且强大的过滤和搜索能力。

## 设计理念

- **统一标准**: 模型和图像使用相同的元数据查询语法
- **类型推断**: 根据操作符和值自动推断数据类型，无需类型前缀
- **URL友好**: 所有语法都是URL安全的，无需特殊编码
- **直观简洁**: 布尔值使用一元操作符，更加直观

---

## 查询语法

### 操作符规则

**字符串类型 (自动推断):**

- `field=value` - 精确匹配
- `field!=value` - 不等于  
- `field~value` - 模糊匹配 (包含子字符串)

**数字类型 (自动推断):**

- `field=123` - 等于
- `field!=123` - 不等于
- `field>123` - 大于
- `field>=123` - 大于等于
- `field<123` - 小于
- `field<=123` - 小于等于

**布尔类型 (一元操作符):**

- `field` - 字段为真 (等同于 field=true)
- `!field` - 字段为假 (等同于 field=false)

### 类型推断规则

系统根据以下规则自动推断字段类型：

1. **数字类型**: 值可以解析为数字时 (`size=1024`, `rating>=4.5`)
2. **布尔类型**: 使用一元操作符时 (`is_nsfw`, `!is_commercial`)
3. **字符串类型**: 其他所有情况 (`type=checkpoint`, `name~landscape`)

---

## 模型元数据标准

### 通用元数据字段

```json
{
  "s$type": "checkpoint",           // 模型类型
  "s$name": "stable-diffusion-v1-5", // 模型名称
  "s$base_model": "SD1.5",         // 基础模型架构
  "s$source": "civitai",           // 来源平台
  "s$version": "1.5",              // 版本号
  "s$description": "模型描述",      // 描述信息
  "n$size": 4200000000,            // 文件大小 (字节)
  "n$resolution": 512,             // 支持分辨率
  "n$download_count": 150000,      // 下载次数
  "rating": 4.8,                       // 评分 (1-5)
  
  // 标签布尔集合
  "tag_photorealistic": true,          // 写实风格
  "tag_anime": false,                  // 动漫风格
  "tag_portrait": true,                // 人像
  "tag_landscape": false,              // 风景
  "tag_nsfw": false,                   // 成人内容
  "tag_high_quality": true,            // 高质量
  
  // 采样器支持
  "scheduler_ddim": true,              // 支持 DDIM
  "scheduler_euler": true,             // 支持 Euler
  "scheduler_dpm": false,              // 支持 DPM
  
  // 其他布尔属性
  "is_nsfw": false,                    // 是否包含成人内容
  "is_commercial": true,               // 是否允许商用
  "requires_trigger": false            // 是否需要触发词
}
```

### 按模型类型的专属字段

**Checkpoint 模型:**

```json
{
  "architecture": "SD1.5",            // 架构类型
  "vae_included": true,                // 是否包含VAE
  "supports_512x512": true,            // 支持 512x512
  "supports_768x768": false,           // 支持 768x768
  "supports_1024x1024": false          // 支持 1024x1024
}
```

**LoRA 模型:**

```json
{
  "training_method": "dreambooth",     // 训练方法
  "recommended_weight": 0.8,           // 推荐权重
  "trigger_masterpiece": true,         // 触发词: masterpiece
  "trigger_detailed": true,            // 触发词: detailed
  "compatible_sd15": true,             // 兼容 SD1.5
  "compatible_sdxl": false             // 兼容 SDXL
}
```

**ControlNet 模型:**

```json
{
  "control_type": "pose",              // 控制类型
  "preprocessor": "openpose",          // 预处理器
  "input_image": true,                 // 支持图像输入
  "input_sketch": false                // 支持草图输入
}
```

---

## 图像元数据标准

### 生成信息元数据

```json
{
  "@type": "generated",           // 图像类型
  "@model": "stable-diffusion-v1-5", // 使用的模型
  "@prompt": "a beautiful landscape", // 正向提示词
  "@negative_prompt": "blurry, low quality", // 负向提示词
  "@sampler": "DPM++ 2M Karras",  // 采样器
  "#width": 512,                  // 宽度
  "#height": 512,                 // 高度
  "#steps": 20,                   // 采样步数
  "#cfg_scale": 7.0,              // CFG 系数
  "#seed": 1234567890,            // 随机种子
  "#rating": 4.5,                 // 用户评分
  
  // 标签布尔集合
  "tag_landscape": true,               // 风景
  "tag_nature": true,                  // 自然
  "tag_high_quality": true,            // 高质量
  "tag_portrait": false,               // 人像
  "tag_anime": false,                  // 动漫
  
  // LoRA 使用情况
  "lora_landscape": true,              // 使用了风景LoRA
  "lora_detail": false,                // 使用了细节LoRA
  
  // 其他属性
  "is_favorite": true,                 // 是否收藏
  "is_public": false,                  // 是否公开
  "is_nsfw": false                     // 是否成人内容
}
```

---

## 查询语法示例

### 模型查询示例

**1. 查找特定类型的模型:**

```http
GET /api/v1/models?type=checkpoint&base_model=SD1.5
```

**2. 按大小范围过滤:**

```http
GET /api/v1/models?size>=1000000000&size<=5000000000
```

**3. 按标签组合查询 (使用一元布尔操作符):**

```http
GET /api/v1/models?type=lora&tag_anime&!tag_nsfw
```

**4. 高评分且允许商用的模型:**

```http
GET /api/v1/models?rating>=4.5&is_commercial
```

**5. 模糊搜索模型名称:**

```http
GET /api/v1/models?name~landscape&type=lora&tag_landscape
```

### 图像查询示例

**1. 查找特定模型生成的图像:**

```http
GET /api/v1/images?model=stable-diffusion-v1-5&type=generated
```

**2. 按分辨率过滤:**

```http
GET /api/v1/images?width>=1024&height>=1024
```

**3. 收藏的高质量图像:**

```http
GET /api/v1/images?is_favorite&rating>=4.0&tag_high_quality
```

**4. 包含特定标签但排除成人内容:**

```http
GET /api/v1/images?type=generated&tag_portrait&!is_nsfw
```

---

## 复合查询和高级功能

### 多条件组合

```http
# 查找高质量的动漫风格LoRA模型，排除成人内容
GET /api/v1/models?type=lora&tag_anime&!is_nsfw&rating>=4.0

# 查找使用特定模型生成的高分辨率收藏图像
GET /api/v1/images?model~stable-diffusion&width>=1024&is_favorite

# 查找支持多种分辨率的写实风格Checkpoint
GET /api/v1/models?type=checkpoint&tag_photorealistic&supports_512x512&supports_1024x1024

# 查找使用了风景LoRA的高评分图像，排除成人内容
GET /api/v1/images?lora_landscape&rating>=4.5&tag_landscape&!is_nsfw
```

### 分页和排序

```http
# 按评分降序排列，分页显示
GET /api/v1/models?@type=checkpoint&sort=#rating&order=desc&skip=0&take=20

# 按创建时间排序
GET /api/v1/images?sort=created_at&order=desc&skip=50&take=25
```

### 性能优化建议

1. **索引字段优先**: 优先使用已建立索引的字段进行过滤
2. **类型过滤前置**: 先按 `@type` 过滤，再应用其他条件
3. **范围查询优化**: 数字范围查询比精确匹配更高效
4. **标签查询优化**: 使用 `*tags=value` 比模糊搜索更快
5. **分页控制**: 使用适当的 `take` 值，避免返回过多结果

---

## 错误处理

### 查询参数验证错误 (400 Bad Request)

```json
{
  "error": "Invalid query parameter",
  "details": {
    "#size": "Invalid number format",
    "*tags": "Invalid array format",
    "@type": "Invalid model type. Allowed: checkpoint, lora, controlnet, vae, embedding"
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
