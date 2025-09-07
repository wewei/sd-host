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
    version TEXT,                             -- 版本号
    source TEXT,                              -- 来源平台 (civitai, huggingface, local)
    resolution INTEGER,                       -- 支持分辨率
    download_count INTEGER DEFAULT 0,         -- 下载次数
    rating REAL DEFAULT 0.0,                  -- 评分 (1.0-5.0)
    
    -- 布尔属性
    is_nsfw BOOLEAN DEFAULT FALSE,            -- 是否成人内容
    is_commercial BOOLEAN DEFAULT TRUE,       -- 是否允许商用
    requires_trigger BOOLEAN DEFAULT FALSE,   -- 是否需要触发词
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 检查约束
    CONSTRAINT chk_type CHECK (type IN ('checkpoint', 'lora', 'controlnet', 'vae', 'embedding')),
    CONSTRAINT chk_rating CHECK (rating >= 0.0 AND rating <= 5.0),
    CONSTRAINT chk_size CHECK (size > 0)
);

-- 索引
CREATE INDEX idx_models_type ON models(type);
CREATE INDEX idx_models_base_model ON models(base_model);
CREATE INDEX idx_models_rating ON models(rating DESC);
CREATE INDEX idx_models_size ON models(size);
CREATE INDEX idx_models_created_at ON models(created_at DESC);
CREATE INDEX idx_models_name_fts ON models(name); -- 用于全文搜索
```

### 2. images 表

存储图像的核心属性信息。

```sql
CREATE TABLE images (
    hash TEXT PRIMARY KEY,                    -- SHA256 哈希值 (唯一标识)
    type TEXT NOT NULL DEFAULT 'generated',  -- 图像类型 (generated, uploaded, processed)
    model TEXT,                               -- 使用的模型 (外键到 models.hash)
    width INTEGER NOT NULL,                   -- 宽度 (像素)
    height INTEGER NOT NULL,                  -- 高度 (像素)
    size INTEGER NOT NULL,                    -- 文件大小 (字节)
    format TEXT NOT NULL DEFAULT 'png',      -- 文件格式 (png, jpg, webp)
    rating REAL DEFAULT 0.0,                 -- 用户评分 (1.0-5.0)
    
    -- 生成参数 (仅 generated 类型)
    prompt TEXT,                              -- 正向提示词
    negative_prompt TEXT,                     -- 负向提示词
    sampler TEXT,                             -- 采样器
    steps INTEGER,                            -- 采样步数
    cfg_scale REAL,                           -- CFG 系数
    seed INTEGER,                             -- 随机种子
    
    -- 布尔属性
    is_favorite BOOLEAN DEFAULT FALSE,        -- 是否收藏
    is_public BOOLEAN DEFAULT FALSE,          -- 是否公开
    is_nsfw BOOLEAN DEFAULT FALSE,            -- 是否成人内容
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 检查约束
    CONSTRAINT chk_type CHECK (type IN ('generated', 'uploaded', 'processed')),
    CONSTRAINT chk_rating CHECK (rating >= 0.0 AND rating <= 5.0),
    CONSTRAINT chk_dimensions CHECK (width > 0 AND height > 0),
    CONSTRAINT chk_size CHECK (size > 0),
    CONSTRAINT chk_format CHECK (format IN ('png', 'jpg', 'jpeg', 'webp')),
    CONSTRAINT chk_steps CHECK (steps IS NULL OR steps > 0),
    CONSTRAINT chk_cfg_scale CHECK (cfg_scale IS NULL OR cfg_scale > 0.0),
    
    -- 外键约束
    FOREIGN KEY (model) REFERENCES models(hash) ON DELETE SET NULL
);

-- 索引
CREATE INDEX idx_images_type ON images(type);
CREATE INDEX idx_images_model ON images(model);
CREATE INDEX idx_images_dimensions ON images(width, height);
CREATE INDEX idx_images_rating ON images(rating DESC);
CREATE INDEX idx_images_created_at ON images(created_at DESC);
CREATE INDEX idx_images_is_favorite ON images(is_favorite);
CREATE INDEX idx_images_seed ON images(seed); -- 用于种子查询
```

### 3. tasks 表

存储任务的核心属性信息。

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,                      -- 任务唯一标识 (UUID)
    type TEXT NOT NULL DEFAULT 'generate',   -- 任务类型 (generate, download, process)
    status TEXT NOT NULL DEFAULT 'pending',  -- 任务状态 (pending, running, completed, failed, cancelled)
    priority INTEGER DEFAULT 0,              -- 优先级 (数值越大优先级越高)
    
    -- 关联实体
    model_hash TEXT,                          -- 关联模型 (外键到 models.hash)
    result_image_hash TEXT,                   -- 结果图像 (外键到 images.hash)
    
    -- 任务参数 (JSON 格式存储)
    parameters TEXT,                          -- 任务参数 (JSON)
    
    -- 执行信息
    progress REAL DEFAULT 0.0,                -- 执行进度 (0.0-1.0)
    error_message TEXT,                       -- 错误信息
    
    -- 时间信息
    estimated_duration INTEGER,              -- 预估执行时间 (秒)
    actual_duration INTEGER,                 -- 实际执行时间 (秒)
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,                      -- 开始执行时间
    completed_at DATETIME,                    -- 完成时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 检查约束
    CONSTRAINT chk_type CHECK (type IN ('generate', 'download', 'process')),
    CONSTRAINT chk_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT chk_progress CHECK (progress >= 0.0 AND progress <= 1.0),
    CONSTRAINT chk_priority CHECK (priority >= 0),
    
    -- 外键约束
    FOREIGN KEY (model_hash) REFERENCES models(hash) ON DELETE SET NULL,
    FOREIGN KEY (result_image_hash) REFERENCES images(hash) ON DELETE SET NULL
);

-- 索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX idx_tasks_model_hash ON tasks(model_hash);
CREATE INDEX idx_tasks_type ON tasks(type);
CREATE UNIQUE INDEX idx_tasks_queue ON tasks(status, priority DESC, created_at ASC) 
    WHERE status IN ('pending', 'running'); -- 任务队列优化索引
```

---

## 标签系统

### 4. tags 表

存储所有标签的定义信息。

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,    -- 标签唯一标识
    name TEXT NOT NULL UNIQUE,               -- 标签名称 (最大 20 个 Unicode 字符)
    category TEXT,                           -- 标签分类 (style, content, quality, special)
    description TEXT,                        -- 标签描述
    usage_count INTEGER DEFAULT 0,          -- 使用次数统计
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 检查约束
    CONSTRAINT chk_name_length CHECK (length(name) <= 20 AND length(name) > 0),
    CONSTRAINT chk_category CHECK (category IS NULL OR category IN ('style', 'content', 'quality', 'special')),
    CONSTRAINT chk_usage_count CHECK (usage_count >= 0)
);

-- 索引
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_category ON tags(category);
CREATE INDEX idx_tags_usage_count ON tags(usage_count DESC);
```

### 5. entity_tags 关联表

管理实体与标签的多对多关系。

```sql
CREATE TABLE entity_tags (
    entity_type TEXT NOT NULL,               -- 实体类型 (model, image, task)
    entity_id TEXT NOT NULL,                 -- 实体ID (对应各表的主键)
    tag_id INTEGER NOT NULL,                 -- 标签ID (外键到 tags.id)
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 主键
    PRIMARY KEY (entity_type, entity_id, tag_id),
    
    -- 检查约束
    CONSTRAINT chk_entity_type CHECK (entity_type IN ('model', 'image', 'task')),
    
    -- 外键约束
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_entity_tags_entity ON entity_tags(entity_type, entity_id);
CREATE INDEX idx_entity_tags_tag ON entity_tags(tag_id);
CREATE INDEX idx_entity_tags_type_tag ON entity_tags(entity_type, tag_id); -- 按类型和标签查询
```

---

## 辅助表

### 6. metadata 表

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
    GROUP_CONCAT(t.name, ',') as tag_names,
    COUNT(et.tag_id) as tag_count
FROM models m
LEFT JOIN entity_tags et ON et.entity_type = 'model' AND et.entity_id = m.hash
LEFT JOIN tags t ON t.id = et.tag_id
GROUP BY m.hash;

-- 图像标签聚合视图
CREATE VIEW images_with_tags AS
SELECT 
    i.*,
    GROUP_CONCAT(t.name, ',') as tag_names,
    COUNT(et.tag_id) as tag_count
FROM images i
LEFT JOIN entity_tags et ON et.entity_type = 'image' AND et.entity_id = i.hash
LEFT JOIN tags t ON t.id = et.tag_id
GROUP BY i.hash;

-- 任务标签聚合视图
CREATE VIEW tasks_with_tags AS
SELECT 
    tk.*,
    GROUP_CONCAT(t.name, ',') as tag_names,
    COUNT(et.tag_id) as tag_count
FROM tasks tk
LEFT JOIN entity_tags et ON et.entity_type = 'task' AND et.entity_id = tk.id
LEFT JOIN tags t ON t.id = et.tag_id
GROUP BY tk.id;
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

-- images 表更新触发器
CREATE TRIGGER images_updated_at
    AFTER UPDATE ON images
    FOR EACH ROW
BEGIN
    UPDATE images SET updated_at = CURRENT_TIMESTAMP WHERE hash = NEW.hash;
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
    UPDATE tags SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

### 标签使用计数

```sql
-- 标签使用计数增加
CREATE TRIGGER tag_usage_increment
    AFTER INSERT ON entity_tags
    FOR EACH ROW
BEGIN
    UPDATE tags SET usage_count = usage_count + 1 WHERE id = NEW.tag_id;
END;

-- 标签使用计数减少
CREATE TRIGGER tag_usage_decrement
    AFTER DELETE ON entity_tags
    FOR EACH ROW
BEGIN
    UPDATE tags SET usage_count = usage_count - 1 WHERE id = OLD.tag_id;
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
