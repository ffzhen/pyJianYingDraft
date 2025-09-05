# 飞书多维表格批量视频工作流使用指南

## 功能说明

这个工作流可以从飞书多维表格获取数据，支持关联账号查询，并批量执行视频合成任务。

## 主要特性

- ✅ 支持飞书多维表格数据获取
- ✅ 支持关联账号查询（账号→音色→数字人）
- ✅ 支持随机选择数字人形象
- ✅ 支持配置文件和命令行参数
- ✅ 支持数据过滤和批量处理
- ✅ 支持并发处理提升效率

## 文件结构

- `workflow/feishu_client.py` - 飞书多维表格API客户端
- `workflow/feishu_batch_workflow.py` - 飞书批量工作流处理器
- `workflow/feishu_config_template.json` - 配置文件模板

## 配置说明

### 1. 飞书应用配置

1. 在飞书开放平台创建应用
2. 获取 `app_id` 和 `app_secret`
3. 创建多维表格并获取 `app_token` 和 `table_id`

### 2. 多维表格配置

#### 内容创作表（主表）
- 仿写标题 - 视频标题
- 仿写文案 - 视频文案内容
- 关联账号 - 关联到账号表的字段
- 状态 - 任务状态（用于过滤，如"视频草稿生成"）
- 项目名称 - 项目名称（可选）

#### 账号表
- 账号 - 账号唯一标识
- 名称 - 账号名称

#### 音色表
- 关联账号 - 关联到账号表的字段
- 声音ID - 配音声音ID
- 备注：一个账号只有一个音色

#### 数字人表
- 关联账号 - 关联到账号表的字段
- 数字人编号 - 数字人ID
- 备注：一个账号可以有多个数字人，会随机选择

### 3. 配置文件

复制 `workflow/feishu_config_template.json` 为你的配置文件，并填写相关信息：

```json
{
  "api_config": {
    "app_id": "your_app_id_here",
    "app_secret": "your_app_secret_here",
    "app_token": "your_app_token_here"
  },
  "tables": {
    "content_table": {
      "table_id": "your_content_table_id_here",
      "field_mapping": {
        "title": "仿写标题",
        "content": "仿写文案",
        "digital_no": "数字人编号",
        "voice_id": "声音ID", 
        "project_name": "项目名称",
        "account": "关联账号"
      },
      "filter_condition": {
        "conjunction": "and",
        "conditions": [
          {
            "field_name": "状态",
            "operator": "is",
            "value": ["视频草稿生成"]
          }
        ]
      }
    },
    "account_table": {
      "table_id": "your_account_table_id_here",
      "account_field": "账号",
      "name_field": "名称"
    },
    "voice_table": {
      "table_id": "your_voice_table_id_here",
      "account_field": "关联账号",
      "voice_id_field": "声音ID"
    },
    "digital_human_table": {
      "table_id": "your_digital_human_table_id_here",
      "account_field": "关联账号",
      "digital_no_field": "数字人编号"
    }
  },
  "workflow_config": {
    "max_workers": 2,
    "background_music_path": "华尔兹.mp3",
    "background_music_volume": 0.3,
    "doubao_token": "adac0afb-5fd4-4c66-badb-370a7ff42df5",
    "doubao_model": "ep-m-20250902010446-mlwmf"
  }
}
```

**配置说明**：
- `api_config`: 飞书API配置（所有表格共用）
- `tables`: 各个表格的配置
  - `content_table`: 内容创作表（主表）
  - `account_table`: 账号表
  - `voice_table`: 音色表
  - `digital_human_table`: 数字人表
- `workflow_config`: 工作流配置

## 使用方式

### 1. 使用配置文件（推荐）

```bash
python workflow/feishu_batch_workflow.py \
  --config "your_config.json" \
  --max-workers 2 \
  --include "task_001" "task_002"
```

### 2. 使用命令行参数

```bash
python workflow/feishu_batch_workflow.py \
  --app-id "your_app_id" \
  --app-secret "your_app_secret" \
  --app-token "your_app_token" \
  --table-id "your_table_id" \
  --max-workers 2 \
  --music-path "背景音乐.mp3"
```

### 3. 禁用关联表查询

```bash
python workflow/feishu_batch_workflow.py \
  --config "your_config.json" \
  --no-relations
```

### 4. 代码集成方式

```python
from workflow.feishu_batch_workflow import FeishuBatchWorkflow

# 创建工作流
workflow = FeishuBatchWorkflow(draft_folder_path, max_workers=2)

# 设置飞书配置
workflow.set_feishu_config(
    app_id="your_app_id",
    app_secret="your_app_secret", 
    app_token="your_app_token",
    table_id="your_table_id"
)

# 设置字段映射
workflow.set_field_mapping({
    "title": "仿写标题",
    "content": "仿写文案",
    "account": "关联账号"
})

# 设置关联表配置
workflow.set_relation_tables(
    account_config={
        "app_token": "account_app_token",
        "table_id": "account_table_id",
        "account_field": "账号",
        "name_field": "名称"
    },
    voice_config={
        "app_token": "voice_app_token",
        "table_id": "voice_table_id",
        "account_field": "关联账号",
        "voice_id_field": "声音ID"
    },
    digital_human_config={
        "app_token": "digital_human_app_token",
        "table_id": "digital_human_table_id",
        "account_field": "关联账号",
        "digital_no_field": "数字人编号"
    }
)

# 设置API和背景音乐
workflow.set_doubao_api(token, model)
workflow.set_background_music(music_path, volume)

# 执行批量处理
results = workflow.process_feishu_batch()
```

## 参数说明

- `--config`: 配置文件路径
- `--app-id`: 飞书应用ID
- `--app-secret`: 飞书应用密钥
- `--app-token`: 多维表格应用令牌
- `--table-id`: 表格ID
- `--max-workers`: 最大并发数（默认2）
- `--music-path`: 背景音乐文件路径
- `--music-volume`: 背景音乐音量（默认0.3）
- `--doubao-token`: 豆包API令牌
- `--doubao-model`: 豆包模型
- `--include`: 只执行指定的任务ID
- `--exclude`: 跳过指定的任务ID
- `--no-save`: 不保存任务到文件
- `--no-relations`: 不使用关联表查询

## 关联查询逻辑

1. 从内容创作表获取任务基本信息
2. 通过关联账号字段查询账号信息
3. 通过账号ID查询对应的音色ID（一个账号一个音色）
4. 通过账号ID查询对应的数字人列表（一个账号多个数字人）
5. 随机选择一个数字人编号
6. 自动生成项目名称：`关联账号 + 仿写标题 + 时间戳`
7. 组合完整的任务信息

## 项目名称生成规则

项目名称会自动按照以下规则生成：
- **完整格式**：`{账号ID}_{标题}_{时间戳}`
- **简化格式**：如果没有账号ID，则使用 `{标题}_{时间戳}`
- **最小格式**：如果既没有账号ID也没有标题，则使用 `video_{时间戳}`

**示例**：
- `account001_未来中国可能出现的九大变化_20250904_143025`
- `account002_beauty_and_poverty_20250904_143026`

## 数据过滤

默认过滤条件为状态="视频草稿生成"，可以通过修改配置文件中的 `filter_condition` 来自定义：

```json
{
  "filter_condition": {
    "conjunction": "and",
    "conditions": [
      {
        "field_name": "状态",
        "operator": "is",
        "value":  ["视频草稿生成"]
      },
      {
        "field_name": "优先级",
        "operator": "isNotEmpty"
      }
    ]
  }
}
```

## 输出文件

- `feishu_tasks_YYYYMMDD_HHMMSS.json` - 从飞书获取的任务列表
- `batch_results.json` - 批量处理结果

## 注意事项

1. **API限制**: 飞书API有调用频率限制，建议控制并发数在2-3
2. **网络要求**: 确保网络连接正常，能够访问飞书API
3. **数据量**: 关联表数据会预加载到内存，确保数据量适中
4. **随机选择**: 数字人选择是随机的，每次运行可能不同
5. **错误处理**: 如果关联查询失败，会使用表格中的默认值
6. **调试信息**: 可以查看日志了解关联查询的详细过程

## 故障排除

### 1. 关联查询失败
- 检查关联表配置是否正确
- 确认关联字段名称匹配
- 查看日志中的缓存加载信息

### 2. 随机选择问题
- 确保数字人表中有对应账号的数据
- 检查数字人编号字段是否正确配置

### 3. API调用失败
- 验证app_id和app_secret是否正确
- 检查网络连接和API权限
- 确认app_token和table_id是否有效