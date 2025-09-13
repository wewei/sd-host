# 模型标签管理 API 使用示例

## 概述

模型标签管理提供了批量添加和移除标签的接口，支持笛卡尔积操作，可以高效地为多个模型批量管理标签关系。

## API 端点

- `POST /api/models/tag` - 为模型批量添加标签
- `POST /api/models/untag` - 为模型批量移除标签

## 请求格式

两个端点接受相同的请求格式：

```json
[
  {
    "entities": ["model_hash_1", "model_hash_2"],
    "tags": ["anime", "high-quality"]
  },
  {
    "entities": ["model_hash_3"],
    "tags": ["realistic", "portrait"]
  }
]
```

### 参数说明

- **请求体**: 操作列表数组
- **entities**: 模型哈希列表（字符串数组）
- **tags**: 标签名称列表（字符串数组）

### 笛卡尔积处理

每个操作对象中的 `entities` 和 `tags` 会形成笛卡尔积，例如：

```json
{
  "entities": ["hash1", "hash2"],
  "tags": ["anime", "realistic"]
}
```

将产生 4 个操作：
- hash1 + anime
- hash1 + realistic  
- hash2 + anime
- hash2 + realistic

## 响应格式

```json
{
  "success": true,
  "message": "Tagged 3/4 model-tag pairs",
  "total_operations": 4,
  "successful_operations": 3,
  "failed_operations": 1,
  "results": [
    {
      "entity": "hash1",
      "tag": "anime", 
      "success": true
    },
    {
      "entity": "hash1",
      "tag": "realistic",
      "success": true
    },
    {
      "entity": "hash2", 
      "tag": "anime",
      "success": true
    },
    {
      "entity": "hash2",
      "tag": "realistic", 
      "success": false,
      "message": "Model not found"
    }
  ]
}
```

### 响应字段说明

- **success**: 整体操作是否成功（所有子操作都成功才为 true）
- **message**: 操作结果摘要
- **total_operations**: 总操作数（笛卡尔积展开后的数量）
- **successful_operations**: 成功操作数
- **failed_operations**: 失败操作数  
- **results**: 每个子操作的详细结果

## 使用示例

### 1. 为多个模型添加标签

```bash
curl -X POST "http://localhost:8000/api/models/tag" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "entities": ["model_hash_1", "model_hash_2"],
      "tags": ["anime", "high-quality"]
    }
  ]'
```

### 2. 复杂批量操作

```bash
curl -X POST "http://localhost:8000/api/models/tag" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "entities": ["checkpoint_hash_1", "checkpoint_hash_2"],
      "tags": ["anime", "character"]
    },
    {
      "entities": ["lora_hash_1"],
      "tags": ["style", "enhancement"]
    },
    {
      "entities": ["controlnet_hash_1", "controlnet_hash_2", "controlnet_hash_3"],
      "tags": ["pose", "composition"]
    }
  ]'
```

### 3. 移除标签

```bash
curl -X POST "http://localhost:8000/api/models/untag" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "entities": ["model_hash_1"],
      "tags": ["outdated", "experimental"]
    }
  ]'
```

## 错误处理

### 常见错误情况

1. **模型不存在**: 指定的模型哈希在数据库中不存在
2. **标签关系不存在**: 尝试移除不存在的标签关系
3. **数据库错误**: 数据库连接或约束违反错误

### 错误响应示例

```json
{
  "success": false,
  "message": "Tagged 2/3 model-tag pairs", 
  "total_operations": 3,
  "successful_operations": 2,
  "failed_operations": 1,
  "results": [
    {
      "entity": "valid_hash",
      "tag": "anime",
      "success": true
    },
    {
      "entity": "invalid_hash", 
      "tag": "anime",
      "success": false,
      "message": "Model not found"
    },
    {
      "entity": "valid_hash",
      "tag": "realistic", 
      "success": true
    }
  ]
}
```

## 最佳实践

### 1. 批量操作优化

- 将相关的模型和标签组织在同一个操作对象中
- 避免过大的请求（建议单次不超过 1000 个操作）
- 合理利用笛卡尔积减少请求次数

### 2. 错误处理

- 检查响应中的 `success` 字段判断整体结果
- 遍历 `results` 数组处理部分失败的情况
- 根据 `message` 字段了解具体错误原因

### 3. 性能考虑

- 标签操作会自动创建不存在的标签
- 重复添加相同标签关系会被忽略（成功返回）
- 移除不存在的标签关系会返回失败

## 与其他 API 的集成

### 结合模型列表查询

```bash
# 1. 获取特定类型的模型
curl "http://localhost:8000/api/models?filter[model_type]=checkpoint"

# 2. 提取模型哈希用于标签操作
# 3. 批量添加标签
curl -X POST "http://localhost:8000/api/models/tag" \
  -H "Content-Type: application/json" \
  -d '[{"entities": ["hash1", "hash2"], "tags": ["verified"]}]'
```

### 结合标签管理

```bash
# 1. 获取可用标签
curl "http://localhost:8000/api/tags"

# 2. 使用返回的标签名称进行批量操作
```

这样的设计确保了标签管理操作的高效性和灵活性，支持复杂的批量操作场景。
