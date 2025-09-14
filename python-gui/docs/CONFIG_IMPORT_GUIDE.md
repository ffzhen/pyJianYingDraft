# 配置导入功能使用指南

## 功能概述

GUI应用现已支持从 `workflow/feishu_config_template.json` 模板文件一键导入所有配置，无需手动填写复杂的配置项。

## 主要特性

### ✅ 已实现功能
- **一键导入**: 从模板文件自动导入所有配置项
- **滚动界面**: 配置标签页支持滚动，解决内容过长问题
- **配置清空**: 支持一键清空所有配置
- **配置保存**: 导入后可保存到本地配置文件

### 📋 配置映射关系

| 模板配置路径 | GUI字段 | 说明 |
|-------------|---------|------|
| `api_config.app_id` | 飞书App ID | 飞书应用ID |
| `api_config.app_secret` | 飞书App Secret | 飞书应用密钥 |
| `api_config.app_token` | 飞书App Token | 飞书访问令牌 |
| `tables.content_table.table_id` | 内容表ID | 存储视频任务的表格ID |
| `tables.account_table.table_id` | 账号表ID | 存储账号信息的表格ID |
| `tables.voice_table.table_id` | 声音表ID | 存储声音配置的表格ID |
| `tables.digital_human_table.table_id` | 数字人表ID | 存储数字人配置的表格ID |
| `workflow_config.coze_config.token` | Coze Bearer Token | Coze API访问令牌 |
| `workflow_config.coze_config.workflow_id` | Coze Workflow ID | Coze工作流ID |
| `workflow_config.volcengine_appid` | 火山引擎App ID | 火山引擎应用ID |
| `workflow_config.volcengine_access_token` | 火山引擎Access Token | 火山引擎访问令牌 |
| `workflow_config.doubao_token` | 豆包Token | 豆包API访问令牌 |
| `workflow_config.draft_folder_path` | 剪映草稿文件夹路径 | 剪映项目文件夹路径 |
| `workflow_config.max_coze_concurrent` | Coze最大并发数 | Coze API并发调用数 |
| `workflow_config.max_synthesis_workers` | 视频合成最大并发数 | 视频合成并发数 |
| `workflow_config.poll_interval` | 轮询间隔(秒) | 任务状态检查间隔 |

## 使用步骤

### 1. 启动GUI
```bash
cd python-gui
python video_generator_gui.py
```

### 2. 导入配置
1. 切换到"配置管理"标签页
2. 滚动到页面底部（现在支持滚动）
3. 点击"导入模板配置"按钮
4. 系统会自动从 `workflow/feishu_config_template.json` 读取配置
5. 所有配置项将自动填充到对应字段

### 3. 保存配置
1. 检查导入的配置是否正确
2. 点击"保存配置"按钮
3. 配置将保存到本地 `config.json` 文件

### 4. 清空配置（可选）
- 点击"清空配置"按钮可以清空所有配置字段
- 系统会要求确认操作

## 界面优化

### 滚动支持
- 配置标签页现在支持垂直滚动
- 解决了配置项过多导致按钮区域被隐藏的问题
- 可以轻松访问所有配置项和操作按钮

### 按钮布局
- **保存配置**: 保存当前配置到本地
- **导入模板配置**: 从模板文件导入配置
- **清空配置**: 清空所有配置字段

## 技术实现

### 核心方法
- `import_template_config()`: 导入模板配置
- `clear_config()`: 清空配置
- `clear_config_fields()`: 清空配置字段
- `load_config_to_gui()`: 加载配置到GUI

### 文件结构
```
python-gui/
├── video_generator_gui.py      # 主GUI文件
├── config.json                 # 本地配置文件
├── test_gui_config.py          # 配置测试脚本
└── CONFIG_IMPORT_GUIDE.md      # 本说明文档

workflow/
└── feishu_config_template.json # 模板配置文件
```

## 测试验证

运行测试脚本验证功能：
```bash
python test_gui_config.py
```

测试内容包括：
- 模板配置文件存在性检查
- 配置文件格式验证
- 配置映射关系验证
- 导入功能测试

## 注意事项

1. **模板文件**: 确保 `workflow/feishu_config_template.json` 文件存在且格式正确
2. **权限**: 确保有读取模板文件的权限
3. **备份**: 建议在导入前备份现有配置
4. **验证**: 导入后请检查配置是否正确

## 故障排除

### 常见问题
1. **模板文件不存在**: 检查文件路径是否正确
2. **配置格式错误**: 验证JSON格式是否正确
3. **权限问题**: 确保有文件读取权限
4. **界面问题**: 使用滚动条查看所有内容

### 错误处理
- 所有操作都有完整的错误提示
- 失败时会显示具体错误信息
- 支持日志记录便于调试

## 更新日志

- ✅ 添加配置导入功能
- ✅ 优化界面布局，支持滚动
- ✅ 添加配置清空功能
- ✅ 完善错误处理和用户提示
- ✅ 添加测试脚本和文档
