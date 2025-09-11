# 标题行间距功能实现指南

## 功能概述

为模板系统添加了标题行间距（line_spacing）配置项，允许用户自定义标题文本的行间距，提供更精细的文本样式控制。

## 实现内容

### 1. 模板配置扩展

#### 在`VideoEditingWorkflow`中添加title_line_spacing配置：
```python
# 标题样式默认值
self.title_config = {
    'color': self.template_config.get('title_color', '#FFFFFF'),
    'highlight_color': self.template_config.get('title_highlight_color', '#FFD700'),
    'bg_enabled': self.template_config.get('title_bg_enabled', True),
    'font': self.template_config.get('title_font', '俪金黑'),
    'font_size': float(self.template_config.get('title_font_size', '15')),
    'scale': float(self.template_config.get('title_scale', '1.0')),
    'line_spacing': float(self.template_config.get('title_line_spacing', '1.0'))  # 新增
}
```

### 2. GUI界面更新

#### 模板表单字段扩展：
```python
fields = [
    ('name','模版名称'),
    ('title_color','标题颜色'),
    ('title_highlight_color','标题高亮色'),
    ('title_bg_enabled','标题背景'),
    ('title_font','标题字体'),
    ('title_font_size','标题字号'),
    ('title_scale','标题缩放'),
    ('title_line_spacing','标题行间距'),  # 新增
    ('subtitle_color','字幕颜色'),
    # ...
]
```

#### 模板列表显示扩展：
```python
self.template_list = ttk.Treeview(tab, columns=(
    'key','name','title_color','title_font','title_size','title_line_spacing','subtitle_color','subtitle_font','subtitle_size'
), show='headings', height=10)
```

### 3. 数据验证

#### 添加title_line_spacing验证：
```python
validated['title_line_spacing'] = self._validate_scale(template_data.get('title_line_spacing', '1.0'))
```

### 4. 默认模板更新

#### 在默认模板中添加title_line_spacing：
```python
'default': {
    'name': '默认模版',
    'title_color': '#FFFFFF',
    'title_highlight_color': '#FFD700',
    'title_bg_enabled': True,
    'title_font': '阳华体',
    'title_font_size': '24',
    'title_scale': '1.0',
    'title_line_spacing': '1.0',  # 新增
    # ...
}
```

### 5. 标题渲染应用

#### 在add_three_line_title方法中应用行间距：
```python
title_line_spacing = int(self.title_config['line_spacing'] * 4)  # 转换为整数，默认4

style = draft.TextStyle(
    size=title_size,
    bold=True,
    align=0,  # 左对齐
    color=title_color,
    max_line_width=0.7,
    line_spacing=title_line_spacing  # 使用模板配置的行间距
)
```

## 技术细节

### 1. 数值转换
- 模板配置中的line_spacing是浮点数（如1.0, 1.5, 2.0）
- 在TextStyle中使用时需要转换为整数
- 转换公式：`int(self.title_config['line_spacing'] * 4)`
- 默认值1.0对应line_spacing=4

### 2. 验证规则
- 使用`_validate_scale`方法验证，范围0.1-5.0
- 默认值1.0
- 无效值时自动修正为1.0

### 3. 显示格式
- 在模板列表中显示为单独列
- 列宽100像素
- 显示原始配置值

## 使用方法

### 1. 创建模板时设置行间距
1. 打开"模版管理"标签页
2. 点击"新增模版"
3. 在"标题行间距"字段输入数值（如1.5）
4. 保存模板

### 2. 编辑现有模板
1. 选择要编辑的模板
2. 点击"编辑所选"
3. 修改"标题行间距"字段
4. 保存更改

### 3. 模板测试
1. 选择模板后点击"测试模版"
2. 系统会使用配置的行间距生成测试视频
3. 在剪映中查看效果

## 配置示例

### 紧凑行间距（0.8）
```json
{
  "title_line_spacing": "0.8"
}
```
- 对应line_spacing=3
- 标题行间距较紧凑

### 标准行间距（1.0）
```json
{
  "title_line_spacing": "1.0"
}
```
- 对应line_spacing=4
- 默认标准行间距

### 宽松行间距（1.5）
```json
{
  "title_line_spacing": "1.5"
}
```
- 对应line_spacing=6
- 标题行间距较宽松

## 影响范围

### 修改的文件
1. `workflow/component/flow_python_implementation.py`
   - 添加title_line_spacing到title_config
   - 在add_three_line_title中应用行间距

2. `python-gui/video_generator_gui.py`
   - 添加title_line_spacing字段到模板表单
   - 更新模板列表显示
   - 添加数据验证
   - 更新默认模板

### 功能影响
- ✅ 支持标题行间距自定义
- ✅ 保持向后兼容性
- ✅ 提供数据验证和默认值
- ✅ 集成到模板测试功能
- ✅ 支持所有工作流（简单合成、飞书批量、定时任务）

## 更新日志

- 添加title_line_spacing配置项
- 更新GUI界面支持行间距设置
- 在标题渲染中应用行间距配置
- 添加数据验证和默认值处理
- 更新模板列表显示
- 集成到模板测试功能

---

通过这次更新，用户现在可以精确控制标题的行间距，实现更丰富的文本样式效果。


