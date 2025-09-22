# 文案批量二创功能配置说明

## 使用现有配置

文案二创功能使用现有的配置，无需新增字段：

### 1. 飞书配置 (feishu)
使用现有的配置字段：

```json
{
  "feishu": {
    "app_id": "你的飞书应用ID",
    "app_secret": "你的飞书应用密钥",
    "app_token": "你的飞书应用Token",
    "content_table_id": "包含视频文案的表格ID",  // 用于二创的表格
    "content_view_id": "包含视频文案的视图ID（可选）"  // 用于二创的视图
  }
}
```

### 2. Coze配置 (coze)
使用现有的配置字段：

```json
{
  "coze": {
    "bearer_token": "你的Coze API Token",
    "workflow_id": "通用工作流ID",
    "notes_workflow_id": "笔记采集工作流ID",
    "content_workflow_id": "文案二创工作流ID"  // 关键：用于二创
  }
}
```

## 配置文件位置
配置文件位于：`E:\code\pyJianYingDraft\python-gui\config\config.json`

## 使用说明

### 文案二创功能的工作流程：
1. 从飞书表格获取"状态"字段为"二创文案生成"的记录
2. 提取"视频文案"字段内容
3. 调用Coze二创工作流（使用content_workflow_id）
4. 并发处理（默认4个并发）

## 📋 飞书表格要求：
你的飞书表格中需要有：
- **"状态"** 字段（单选类型），值为 "二创文案生成" 的记录会被处理
- **"视频文案"** 字段（文本类型），包含要二创的文案内容

### 必需的配置字段：
- `feishu.app_id`: 飞书应用ID
- `feishu.app_secret`: 飞书应用密钥
- `feishu.app_token`: 飞书应用Token
- `feishu.content_table_id`: 包含待二创文案的表格ID ✅
- `coze.bearer_token`: Coze API Token
- `coze.content_workflow_id`: 文案二创工作流ID ✅

### 可选的配置字段：
- `feishu.content_view_id`: 待二创文案的视图ID
- 其他配置字段（已存在）

## 🎯 关键配置项说明：
- **表格**: 使用 `feishu.content_table_id` 作为二创数据源
- **视图**: 使用 `feishu.content_view_id`（如果配置了的话）
- **工作流**: 使用 `coze.content_workflow_id` 进行二创处理
- **过滤条件**: 表格中需要有"状态"字段，值为 "二创文案生成" 的记录才会被处理

## 配置检查
启动程序后，系统会检查以下配置是否完整：
- 飞书应用ID和密钥
- 飞书应用Token
- 待二创表格ID
- Coze API Token
- 文案二创工作流ID

如果配置不完整，会提示具体的缺失项。