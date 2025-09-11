# 标题字体输入框功能实现指南

## 功能概述

将模板管理中的标题字体字段从下拉选择框改为输入框，允许用户输入任意字体名称，提供更大的字体选择灵活性。

## 实现内容

### 1. 字段处理逻辑修改

#### 原来的实现（下拉选择框）：
```python
elif key.endswith('_font'):
    # 字体选择下拉框
    var = tk.StringVar(value=str(data.get(key, font_options[0])))
    cb = ttk.Combobox(parent, textvariable=var, values=font_options, width=37, state='readonly')
    cb.grid(row=row, column=1, padx=5, pady=5)
    entries[key] = var
```

#### 新的实现（区分标题和字幕字体）：
```python
elif key.endswith('_font') and key != 'title_font':
    # 字幕字体使用下拉选择框（标题字体在下面处理）
    var = tk.StringVar(value=str(data.get(key, font_options[0])))
    cb = ttk.Combobox(parent, textvariable=var, values=font_options, width=37, state='readonly')
    cb.grid(row=row, column=1, padx=5, pady=5)
    entries[key] = var
elif key.endswith('_size') or key.endswith('_scale') or key == 'title_font':
    # 数值输入框或标题字体输入框
    if key == 'title_font':
        default_value = '阳华体'
    elif key.endswith('_size'):
        default_value = '18'
    else:  # _scale
        default_value = '1.0'
    
    e = ttk.Entry(parent, width=40)
    e.insert(0, str(data.get(key, default_value)))
    e.grid(row=row, column=1, padx=5, pady=5)
    entries[key] = e
```

### 2. 字段类型区分

#### 标题字体（title_font）
- **控件类型**：`ttk.Entry` 输入框
- **默认值**：'阳华体'
- **宽度**：40字符
- **特点**：支持任意字体名称输入

#### 字幕字体（subtitle_font）
- **控件类型**：`ttk.Combobox` 下拉选择框
- **选项**：预定义的字体列表
- **状态**：只读（readonly）
- **特点**：限制在预定义字体范围内

### 3. 字体选项列表

字幕字体仍使用预定义列表：
```python
font_options = ['阳华体', '俪金黑', '思源黑体', '微软雅黑', '宋体', '黑体', '楷体', '仿宋']
```

## 技术特点

### 1. 灵活性提升
- **标题字体**：支持任意字体名称，不受预定义列表限制
- **字幕字体**：保持下拉选择，确保字体可用性

### 2. 用户体验
- **标题字体**：用户可以直接输入任何字体名称
- **字幕字体**：用户从预定义列表中选择，避免输入错误

### 3. 数据验证
- 标题字体通过动态字体获取机制处理
- 字幕字体通过预定义列表确保有效性

## 使用方法

### 1. 设置标题字体
1. 打开"模版管理"标签页
2. 点击"新增模版"或"编辑所选"
3. 在"标题字体"字段直接输入字体名称（如"思源黑体"、"微软雅黑"等）
4. 保存模板

### 2. 设置字幕字体
1. 在"字幕字体"字段点击下拉箭头
2. 从预定义列表中选择字体
3. 保存模板

### 3. 字体名称示例

#### 支持的标题字体名称：
- 中文字体：思源黑体、微软雅黑、宋体、黑体、楷体、仿宋
- 英文字体：Arial、Times New Roman、Helvetica
- 特殊字体：自定义字体名称

#### 字幕字体选项：
- 阳华体
- 俪金黑
- 思源黑体
- 微软雅黑
- 宋体
- 黑体
- 楷体
- 仿宋

## 配置示例

### 标题字体配置示例
```json
{
  "title_font": "思源黑体",
  "subtitle_font": "俪金黑"
}
```

### 自定义字体配置示例
```json
{
  "title_font": "自定义字体名称",
  "subtitle_font": "阳华体"
}
```

## 影响范围

### 修改的文件
- `python-gui/video_generator_gui.py`
  - 修改`_template_form`方法中的字段处理逻辑
  - 区分标题字体和字幕字体的控件类型

### 功能影响
- ✅ 标题字体支持任意名称输入
- ✅ 字幕字体保持下拉选择
- ✅ 保持向后兼容性
- ✅ 字体动态获取机制正常工作
- ✅ 模板测试功能正常

## 技术优势

### 1. 灵活性
- 用户可以使用任何字体名称
- 不受预定义列表限制
- 支持未来新增字体

### 2. 兼容性
- 保持字幕字体的下拉选择
- 现有模板配置无需修改
- 字体动态获取机制自动处理

### 3. 用户体验
- 标题字体输入更直观
- 字幕字体选择更安全
- 界面操作更符合使用习惯

## 更新日志

- 将标题字体字段改为输入框
- 保持字幕字体为下拉选择框
- 优化字段处理逻辑
- 保持向后兼容性
- 支持任意字体名称输入

---

通过这次更新，用户现在可以更灵活地设置标题字体，同时保持字幕字体的选择安全性。


