# SQLite 数据库表结构设计

SD-Host 使用 SQLite 数据库存储三类核心实体：Model、Task、Image，以及统一的标签系统。

## 设计原则

- **实体独立**: 每类实体使用独立的表存储核心属性
- **统一标签**: 所有实体共享统一的标签系统
- **关系清晰**: 使用关联表管理实体与标签的多对多关系
- **性能优化**: 合理设计索引，支持高效的 OData 查询

---

## 核心实体表

### 1. models 表

存储模型的核心属性信息。

```sql
CREATE TABLE models (
    hash TEXT PRIMARY KEY,                    -- SHA256 哈希值 (唯一标识)
    name TEXT NOT NULL,                       -- 模型名称
    type TEXT NOT NULL,                       -- 模型类型 (checkpoint, lora, controlnet, vae, embedding)
    base_model TEXT,                          -- 基础模型架构 (SD1.5, SDXL, etc.)
    size INTEGER NOT NULL,                    -- 文件大小 (字节)
    sourceUrl TEXT,                           -- 下载源URL
    metadata TEXT,                            -- 模型参数信息 (JSON 格式)
    description TEXT,                         -- 模型描述 (Markdown 格式)
    cover_image_hash TEXT,                    -- 封面图像 (外键到 images.hash, 可选)
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 检查约束
    CONSTRAINT chk_type CHECK (type IN ('checkpoint', 'lora', 'controlnet', 'vae', 'embedding')),
    CONSTRAINT chk_size CHECK (size > 0),
    
    -- 外键约束
    FOREIGN KEY (cover_image_hash) REFERENCES images(hash) ON DELETE SET NULL
);

-- 索引
CREATE INDEX idx_models_type ON models(type);
CREATE INDEX idx_models_base_model ON models(base_model);
CREATE INDEX idx_models_created_at ON models(created_at DESC);
CREATE INDEX idx_models_cover_image ON models(cover_image_hash);
CREATE INDEX idx_models_name_fts ON models(name); -- 用于全文搜索
```

### 2. images 表

存储图像的核心属性信息。

```sql
CREATE TABLE images (
    hash TEXT PRIMARY KEY,                    -- SHA256 哈希值 (唯一标识)
    task_id TEXT,                             -- 关联任务 (外键到 tasks.id, 可选)
    width INTEGER NOT NULL,                   -- 宽度 (像素)
    height INTEGER NOT NULL,                  -- 高度 (像素)
    size INTEGER NOT NULL,                    -- 文件大小 (字节)
    seed INTEGER,                             -- 随机种子 (同一任务中每张图可能不同)
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 检查约束
    CONSTRAINT chk_dimensions CHECK (width > 0 AND height > 0),
    CONSTRAINT chk_size CHECK (size > 0),
    
    -- 外键约束
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- 索引
CREATE INDEX idx_images_task_id ON images(task_id);
CREATE INDEX idx_images_dimensions ON images(width, height);
CREATE INDEX idx_images_created_at ON images(created_at DESC);
CREATE INDEX idx_images_seed ON images(seed); -- 用于种子查询
```

### 3. tasks 表

存储任务的核心属性信息。

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,                      -- 任务唯一标识 (UUID)
    status TEXT NOT NULL DEFAULT 'pending',  -- 任务状态 (pending, completed, failed, cancelled)
    
    -- 主要模型关联 (Checkpoint)
    checkpoint_hash TEXT NOT NULL,            -- 主模型 (外键到 models.hash)
    
    -- 生成参数
    prompt TEXT NOT NULL,                     -- 正向提示词
    negative_prompt TEXT DEFAULT '',          -- 反向提示词
    width INTEGER NOT NULL DEFAULT 512,      -- 图像宽度
    height INTEGER NOT NULL DEFAULT 512,     -- 图像高度
    seed INTEGER DEFAULT -1,                  -- 随机种子 (-1 表示随机)
    steps INTEGER NOT NULL DEFAULT 20,       -- 降噪轮数
    cfg_scale REAL NOT NULL DEFAULT 7.0,     -- CFG 比例
    sampler TEXT NOT NULL DEFAULT 'DPM++ 2M Karras', -- 采样器
    batch_size INTEGER NOT NULL DEFAULT 1,   -- 批次大小
    vae_hash TEXT,                           -- VAE 模型 (外键到 models.hash, 可选)
    
    -- 错误信息
    error_message TEXT,                       -- 错误信息
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    promoted_at DATETIME DEFAULT '1970-01-01 00:00:00', -- 提升时间 (默认 epoch 0)
    completed_at DATETIME,                    -- 完成时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 检查约束
    CONSTRAINT chk_status CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
    CONSTRAINT chk_dimensions CHECK (width > 0 AND height > 0),
    CONSTRAINT chk_steps CHECK (steps > 0 AND steps <= 200),
    CONSTRAINT chk_cfg_scale CHECK (cfg_scale > 0 AND cfg_scale <= 30),
    CONSTRAINT chk_batch_size CHECK (batch_size > 0 AND batch_size <= 10),
    
    -- 外键约束
    FOREIGN KEY (checkpoint_hash) REFERENCES models(hash) ON DELETE CASCADE,
    FOREIGN KEY (vae_hash) REFERENCES models(hash) ON DELETE SET NULL
);

-- 索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_checkpoint ON tasks(checkpoint_hash);
CREATE INDEX idx_tasks_vae ON tasks(vae_hash);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX idx_tasks_promoted_at ON tasks(promoted_at DESC);
CREATE INDEX idx_tasks_completed_at ON tasks(completed_at DESC);
-- 任务队列优化索引 (按执行优先级排序)
CREATE INDEX idx_tasks_queue ON tasks(status, promoted_at DESC, created_at ASC) 
    WHERE status = 'pending';
```

### 4. task_models 表

存储任务与非 checkpoint 模型的关联关系 (如 LoRA、ControlNet 等)。

```sql
CREATE TABLE task_models (
    task_id TEXT NOT NULL,                   -- 任务ID (外键到 tasks.id)
    model_hash TEXT NOT NULL,               -- 模型哈希 (外键到 models.hash)
    weight REAL DEFAULT 1.0,                -- 模型权重 (LoRA 强度等)
    
    -- 复合主键
    PRIMARY KEY (task_id, model_hash),
    
    -- 外键约束
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (model_hash) REFERENCES models(hash) ON DELETE CASCADE,
    
    -- 检查约束
    CONSTRAINT chk_weight CHECK (weight >= 0.0 AND weight <= 2.0)
);

-- 索引
CREATE INDEX idx_task_models_task ON task_models(task_id);
CREATE INDEX idx_task_models_model ON task_models(model_hash);
```

---

## 标签系统

### 6. tags 表

存储所有标签的定义信息。

```sql
CREATE TABLE tags (
    name TEXT PRIMARY KEY,                   -- 标签名称 (最大 20 个 Unicode 字符)
    description TEXT,                        -- 标签描述 (可选)
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 检查约束
    CONSTRAINT chk_name_length CHECK (length(name) <= 20 AND length(name) > 0)
);

-- 索引
CREATE INDEX idx_tags_created_at ON tags(created_at DESC);
```

### 7. model_tags 关联表

管理模型与标签的多对多关系。

```sql
CREATE TABLE model_tags (
    model_hash TEXT NOT NULL,               -- 模型哈希 (外键到 models.hash)
    tag_name TEXT NOT NULL,                 -- 标签名称 (外键到 tags.name)
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 主键
    PRIMARY KEY (model_hash, tag_name),
    
    -- 外键约束
    FOREIGN KEY (model_hash) REFERENCES models(hash) ON DELETE CASCADE,
    FOREIGN KEY (tag_name) REFERENCES tags(name) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_model_tags_model ON model_tags(model_hash);
CREATE INDEX idx_model_tags_tag ON model_tags(tag_name);
```

### 8. image_tags 关联表

管理图像与标签的多对多关系。

```sql
CREATE TABLE image_tags (
    image_hash TEXT NOT NULL,               -- 图像哈希 (外键到 images.hash)
    tag_name TEXT NOT NULL,                 -- 标签名称 (外键到 tags.name)
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 主键
    PRIMARY KEY (image_hash, tag_name),
    
    -- 外键约束
    FOREIGN KEY (image_hash) REFERENCES images(hash) ON DELETE CASCADE,
    FOREIGN KEY (tag_name) REFERENCES tags(name) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_image_tags_image ON image_tags(image_hash);
CREATE INDEX idx_image_tags_tag ON image_tags(tag_name);
```

### 9. task_tags 关联表

管理任务与标签的多对多关系。

```sql
CREATE TABLE task_tags (
    task_id TEXT NOT NULL,                  -- 任务ID (外键到 tasks.id)
    tag_name TEXT NOT NULL,                 -- 标签名称 (外键到 tags.name)
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 主键
    PRIMARY KEY (task_id, tag_name),
    
    -- 外键约束
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_name) REFERENCES tags(name) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_task_tags_task ON task_tags(task_id);
CREATE INDEX idx_task_tags_tag ON task_tags(tag_name);
```

---

## 辅助表

### 10. metadata 表

存储系统元数据和配置信息。

```sql
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,                    -- 配置键
    value TEXT,                              -- 配置值
    type TEXT DEFAULT 'string',              -- 值类型 (string, number, boolean, json)
    description TEXT,                        -- 描述信息
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 检查约束
    CONSTRAINT chk_type CHECK (type IN ('string', 'number', 'boolean', 'json'))
);

-- 初始数据
INSERT INTO metadata (key, value, type, description) VALUES 
    ('db_version', '1.0.0', 'string', '数据库版本'),
    ('api_version', '1.0.0', 'string', 'API 版本'),
    ('created_at', datetime('now'), 'string', '数据库创建时间');
```

---

## 视图定义

### 实体标签聚合视图

为了优化 OData 查询性能，创建预聚合的视图。

```sql
-- 模型标签聚合视图
CREATE VIEW models_with_tags AS
SELECT 
    m.*,
    GROUP_CONCAT(mt.tag_name, ',') as tag_names,
    COUNT(mt.tag_name) as tag_count
FROM models m
LEFT JOIN model_tags mt ON mt.model_hash = m.hash
GROUP BY m.hash;

-- 图像标签聚合视图
CREATE VIEW images_with_tags AS
SELECT 
    i.*,
    GROUP_CONCAT(it.tag_name, ',') as tag_names,
    COUNT(it.tag_name) as tag_count
FROM images i
LEFT JOIN image_tags it ON it.image_hash = i.hash
GROUP BY i.hash;

-- 任务标签聚合视图
CREATE VIEW tasks_with_tags AS
SELECT 
    t.*,
    GROUP_CONCAT(tt.tag_name, ',') as tag_names,
    COUNT(tt.tag_name) as tag_count
FROM tasks t
LEFT JOIN task_tags tt ON tt.task_id = t.id
GROUP BY t.id;
```

---

## 触发器

### 自动更新时间戳

```sql
-- models 表更新触发器
CREATE TRIGGER models_updated_at
    AFTER UPDATE ON models
    FOR EACH ROW
BEGIN
    UPDATE models SET updated_at = CURRENT_TIMESTAMP WHERE hash = NEW.hash;
END;

-- tasks 表更新触发器
CREATE TRIGGER tasks_updated_at
    AFTER UPDATE ON tasks
    FOR EACH ROW
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- tags 表更新触发器
CREATE TRIGGER tags_updated_at
    AFTER UPDATE ON tags
    FOR EACH ROW
BEGIN
    UPDATE tags SET updated_at = CURRENT_TIMESTAMP WHERE name = NEW.name;
END;
```

---

## 性能优化建议

### 索引策略

1. **主键索引**: 所有表的主键自动建立唯一索引
2. **外键索引**: 所有外键字段建立索引，提升关联查询性能
3. **查询索引**: 根据常用查询条件建立复合索引
4. **全文搜索**: 对 name、prompt 等文本字段考虑 FTS 扩展

### 查询优化

1. **使用视图**: 预聚合的标签视图减少运行时 JOIN 操作
2. **分页查询**: 合理使用 LIMIT 和 OFFSET
3. **索引提示**: 复杂查询时考虑使用 SQLite 查询计划器
4. **缓存策略**: 对频繁查询的标签统计信息进行缓存

### 维护建议

1. **定期 VACUUM**: 回收删除数据的空间
2. **统计信息**: 定期 ANALYZE 更新查询优化器统计
3. **备份策略**: 定期备份数据库文件
4. **监控查询**: 使用 EXPLAIN QUERY PLAN 分析慢查询
