# Model API 使用示例

基于 FastAPI + JSON API + SQLite 实现的 Model API 已经完成！以下是使用示例：

## 启动服务器

### Windows
```bash
.\scripts\start.bat
```

### Linux/Mac
```bash
./scripts/start.sh
```

### 手动启动
```bash
# 1. 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate.bat  # Windows

# 2. 安装依赖
pip install -r requirements/requirements.txt

# 3. 初始化数据库
python scripts/init_db.py

# 4. 启动服务
cd src
python main.py
```

服务启动后访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API 使用示例

### 1. 获取模型列表

```bash
# 基础查询
curl "http://localhost:8000/api/models"

# 按类型过滤
curl "http://localhost:8000/api/models?filter[model_type]=checkpoint"

# 按名称搜索
curl "http://localhost:8000/api/models?filter[name][contains]=landscape"

# 按标签过滤
curl "http://localhost:8000/api/models?filter[tags][any]=anime&filter[tags][none]=nsfw"

# 分页查询
curl "http://localhost:8000/api/models?page[number]=1&page[size]=20"

# 排序
curl "http://localhost:8000/api/models?sort=-created_at"

# 复合查询
curl "http://localhost:8000/api/models?filter[model_type]=lora&filter[tags][any]=anime&page[size]=10&sort=name"
```

### 2. 获取单个模型

```bash
curl "http://localhost:8000/api/models/{model_hash}"
```

### 3. 下载模型文件

```bash
curl -O "http://localhost:8000/api/models/{model_hash}/content"
```

### 4. 更新模型元数据

```bash
curl -X POST "http://localhost:8000/api/models/{model_hash}" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_high_quality": true,
    "rating": 4.8,
    "is_favorite": true,
    "custom_note": "Great for landscapes"
  }'
```

### 5. 批量更新模型

```bash
curl -X POST "http://localhost:8000/api/models" \
  -H "Content-Type: application/json" \
  -d '{
    "models": {
      "hash1": {"rating": 4.5, "is_favorite": true},
      "hash2": {"tag_high_quality": true}
    }
  }'
```

### 6. 删除模型

```bash
# 删除单个模型
curl -X DELETE "http://localhost:8000/api/models/{model_hash}"

# 批量删除
curl -X DELETE "http://localhost:8000/api/models" \
  -H "Content-Type: application/json" \
  -d '{
    "hashes": ["hash1", "hash2", "hash3"]
  }'
```

### 7. 从 Civitai 添加模型

```bash
curl -X POST "http://localhost:8000/api/models/add-from-civitai" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "4201",
    "version_id": "130072"
  }'
```

### 8. 跟踪下载进度 (SSE)

```javascript
// JavaScript 示例
const eventSource = new EventSource('http://localhost:8000/api/models/add-from-civitai/{tracking_hash}');

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.progress + '%');
  console.log('Speed:', data.speed);
  console.log('ETA:', data.eta);
  
  if (data.status === 'completed') {
    console.log('Download completed!', data.model_info);
    eventSource.close();
  } else if (data.status === 'failed') {
    console.log('Download failed:', data.error);
    eventSource.close();
  }
};
```

## 响应格式

所有响应都遵循 JSON API 规范：

### 模型列表响应
```json
{
  "data": [
    {
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
          "trigger_words": ["masterpiece"]
        },
        "description": "# Model Description...",
        "status": "ready",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      },
      "relationships": {
        "tags": {
          "data": [
            {"type": "tag", "id": "photorealistic"},
            {"type": "tag", "id": "portrait"}
          ]
        },
        "cover_image": {
          "data": {"type": "image", "id": "def456..."}
        }
      }
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "pages": 5,
      "per_page": 50,
      "total": 230
    }
  },
  "links": {
    "first": "?page[number]=1&page[size]=50",
    "last": "?page[number]=5&page[size]=50",
    "next": "?page[number]=2&page[size]=50"
  }
}
```

### 错误响应
```json
{
  "errors": [
    {
      "status": "404",
      "title": "Model not found",
      "detail": "The requested model could not be found"
    }
  ]
}
```

## 过滤操作符

支持以下过滤操作符：

- `filter[field]=value` - 精确匹配
- `filter[field][contains]=value` - 包含匹配
- `filter[field][gte]=value` - 大于等于
- `filter[field][lte]=value` - 小于等于
- `filter[field][in]=value1,value2` - 在列表中
- `filter[tags][any]=tag1,tag2` - 包含任意标签
- `filter[tags][none]=tag1,tag2` - 不包含任何标签

## 排序字段

支持的排序字段：
- `name` - 按名称排序
- `created_at` - 按创建时间排序
- `updated_at` - 按更新时间排序
- `size` - 按文件大小排序
- `model_type` - 按模型类型排序

使用 `-` 前缀表示降序，例如：`sort=-created_at`

## 标签系统

系统预定义了常用标签：

**风格标签**: photorealistic, anime, cartoon, artistic, stylized
**内容标签**: portrait, landscape, character, object, architecture
**质量标签**: high-quality, detailed, professional, masterpiece
**限制标签**: nsfw, adult, violence, explicit
**其他标签**: commercial, non-commercial, favorite

可以通过 API 动态添加新标签。
