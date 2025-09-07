# Task Management API

任务管理 API 负责图像生成任务的调度、监控和管理功能。

## 设计理念

- **全自动化**: Pipeline 管理完全自动化，用户无需手动管理 checkpoint
- **智能调度**: 任务协调器根据任务需求自动切换模型和 LoRA
- **效率优化**: 智能任务调度，新任务会优先插入到使用相同 checkpoint 的任务后面
- **实时监控**: 通过 SSE 实时推送任务队列状态

---

## API 端点详情

### 1. GET /api/tasks/queue

SSE 实时推送任务队列状态。

**SSE 数据格式:**

```json
{
  "current_task": {
    "id": "task_123",
    "status": "running",
    "progress": 75.5,
    "model": "stable-diffusion-v1-5",
    "eta": "00:01:30"
  },
  "queue": [
    {
      "id": "task_124",
      "status": "waiting",
      "model": "stable-diffusion-v1-5",
      "position": 1
    }
  ],
  "queue_length": 3
}
```

### 2. POST /api/tasks

创建新任务，系统会自动进行智能调度。

**请求参数:**

```json
{
  "model": "stable-diffusion-v1-5",
  "prompt": "a beautiful landscape",
  "negative_prompt": "blurry, low quality",
  "width": 512,
  "height": 512,
  "steps": 20,
  "cfg_scale": 7.0,
  "seed": -1,
  "batch_size": 1,
  "loras": [
    {
      "name": "landscape_lora",
      "weight": 0.8
    }
  ]
}
```

**响应:**

```json
{
  "task_id": "task_123",
  "status": "queued",
  "position": 2,
  "estimated_time": "00:05:30"
}
```

### 3. DELETE /api/tasks

批量取消任务。

**请求参数:**

```json
{
  "task_ids": ["task_123", "task_124", "task_125"]
}
```

**响应:**

```json
{
  "cancelled": ["task_123", "task_124"],
  "failed": [
    {
      "task_id": "task_125",
      "reason": "Task already completed"
    }
  ]
}
```

### 4. PUT /api/tasks/priority

批量提升任务优先级。

**请求参数:**

```json
{
  "task_ids": ["task_124", "task_125"],
  "priority": "high"
}
```

**响应:**

```json
{
  "updated": ["task_124", "task_125"],
  "new_positions": [
    {
      "task_id": "task_124",
      "position": 1
    },
    {
      "task_id": "task_125", 
      "position": 2
    }
  ]
}
```
