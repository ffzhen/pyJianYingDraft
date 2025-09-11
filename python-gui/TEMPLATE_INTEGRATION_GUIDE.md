# 模板集成功能使用指南

## 功能概述

本更新为python-gui添加了完整的模板系统，支持在飞书视频批量生成和定时执行中选择和应用模板配置。

## 新增功能

### 1. 模板管理
- **模板字段扩展**: 支持标题和字幕的颜色、字体、字号、缩放等属性
- **模板验证**: 自动验证和修正模板数据
- **模板选择**: 在飞书批量生成和定时任务中选择模板

### 2. 飞书视频批量生成模板选择
- 在"飞书视频批量生成"标签页添加了模板选择下拉框
- 支持选择不同的模板进行批量处理
- 模板配置会自动应用到所有生成的视频

### 3. 定时任务模板选择
- 在"定时任务"标签页添加了模板选择功能
- 仅对飞书异步批量工作流显示模板选择
- 定时任务会保存选择的模板配置

### 4. 工作流集成
- 模板配置会传递到整个工作流链
- 从GUI → FeishuAsyncBatchWorkflow → AsyncCozeProcessor → CozeVideoWorkflow → VideoEditingWorkflow
- 确保模板样式正确应用到最终视频

## 模板字段说明

### 标题样式
- `title_color`: 标题颜色（十六进制，如 #FFFFFF）
- `title_highlight_color`: 标题高亮色（十六进制，如 #FFD700）
- `title_bg_enabled`: 是否启用标题背景（布尔值）
- `title_font`: 标题字体（下拉选择）
- `title_font_size`: 标题字号（8-100）
- `title_scale`: 标题缩放（0.1-5.0）

### 字幕样式
- `subtitle_color`: 字幕颜色（十六进制，如 #FFFFFF）
- `subtitle_highlight_color`: 字幕高亮色（十六进制，如 #00FFFF）
- `subtitle_bg_enabled`: 是否启用字幕背景（布尔值）
- `subtitle_font`: 字幕字体（下拉选择）
- `subtitle_font_size`: 字幕字号（8-100）
- `subtitle_scale`: 字幕缩放（0.1-5.0）

## 使用方法

### 1. 创建和管理模板
1. 切换到"模版管理"标签页
2. 点击"新增模版"创建新模板
3. 填写模板名称和样式配置
4. 点击"保存"完成创建
5. 使用"编辑所选"、"删除所选"管理现有模板

### 2. 在飞书批量生成中使用模板
1. 切换到"飞书视频批量生成"标签页
2. 在"模板配置"区域选择要使用的模板
3. 点击"刷新模板"更新模板列表
4. 正常执行批量生成，模板样式会自动应用

### 3. 在定时任务中使用模板
1. 切换到"定时任务"标签页
2. 选择工作流类型为"飞书异步批量"
3. 在"模板选择"下拉框中选择模板
4. 创建定时任务，模板配置会被保存
5. 定时执行时会使用保存的模板配置

## 技术实现

### 数据流
```
GUI模板选择 → 配置构建 → FeishuAsyncBatchWorkflow → AsyncCozeProcessor → CozeVideoWorkflow → VideoEditingWorkflow → 样式应用
```

### 关键修改
1. **VideoGeneratorGUI**: 添加模板选择UI和配置传递
2. **FeishuAsyncBatchWorkflow**: 支持模板配置参数
3. **AsyncCozeProcessor**: 传递模板配置到视频合成
4. **CozeVideoWorkflow**: 接收和应用模板配置
5. **VideoEditingWorkflow**: 使用模板配置设置文本样式

### 模板验证
- 颜色值验证：确保十六进制格式正确
- 字体验证：限制在支持的字体列表中
- 字号验证：限制在8-100范围内
- 缩放验证：限制在0.1-5.0范围内

## 默认模板

系统会自动创建一个默认模板：
```json
{
  "name": "默认模版",
  "title_color": "#FFFFFF",
  "title_highlight_color": "#FFD700",
  "title_bg_enabled": true,
  "title_font": "阳华体",
  "title_font_size": "24",
  "title_scale": "1.0",
  "subtitle_color": "#FFFFFF",
  "subtitle_highlight_color": "#00FFFF",
  "subtitle_bg_enabled": true,
  "subtitle_font": "俪金黑",
  "subtitle_font_size": "18",
  "subtitle_scale": "1.0"
}
```

## 注意事项

1. **模板选择**: 如果没有选择模板，系统会使用当前激活的模板或默认模板
2. **数据验证**: 所有模板数据都会经过验证，无效值会被自动修正
3. **向后兼容**: 现有功能不受影响，模板功能是可选的
4. **性能影响**: 模板配置对性能影响很小，主要是样式设置

## 故障排除

### 常见问题
1. **模板不生效**: 检查模板配置是否正确，查看日志确认模板是否被正确传递
2. **样式异常**: 检查颜色值格式是否正确，字体是否在支持列表中
3. **定时任务模板丢失**: 确保在创建定时任务时选择了模板

### 日志查看
所有模板相关的操作都会记录在"运行日志"标签页中，包括：
- 模板选择信息
- 模板配置传递过程
- 样式应用结果

## 扩展开发

### 添加新的模板字段
1. 在`_template_form`方法中添加新字段
2. 在`validate_template_data`方法中添加验证逻辑
3. 在`VideoEditingWorkflow`中添加样式应用逻辑

### 自定义字体支持
1. 在`font_mapping`字典中添加新字体映射
2. 确保字体在pyJianYingDraft的FontType枚举中定义


