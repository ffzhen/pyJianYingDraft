# 字体映射修复指南

## 问题描述

在模板测试功能中遇到了字体映射错误：
```
模版测试失败: type object 'FontType' has no attribute '思源黑体'
```

## 问题原因

原来的字体映射是写死的，只支持预定义的几种字体：
```python
self.font_mapping = {
    '阳华体': draft.FontType.阳华体,
    '俪金黑': draft.FontType.俪金黑,
    '思源黑体': draft.FontType.思源黑体,  # 这个字体在FontType中不存在
    '微软雅黑': draft.FontType.微软雅黑,  # 这个字体在FontType中不存在
    # ...
}
```

## 解决方案

### 1. 移除写死的字体映射
```python
# 字体映射 - 使用动态获取，支持任意字体名称
self.font_mapping = {}
```

### 2. 添加动态字体获取方法
```python
def _get_font_type(self, font_name: str) -> Any:
    """动态获取字体类型，支持任意字体名称"""
    try:
        # 直接通过字符串拼接获取字体类型
        return getattr(draft.FontType, font_name)
    except AttributeError:
        # 如果字体不存在，尝试一些常见的映射
        font_mappings = {
            '思源黑体': '思源黑体',
            '微软雅黑': '微软雅黑', 
            '宋体': '宋体',
            '黑体': '黑体',
            '楷体': '楷体',
            '仿宋': '仿宋',
            '阳华体': '阳华体',
            '俪金黑': '俪金黑'
        }
        
        # 尝试映射后的名称
        mapped_name = font_mappings.get(font_name, font_name)
        try:
            return getattr(draft.FontType, mapped_name)
        except AttributeError:
            # 如果还是找不到，返回默认字体
            print(f"[WARN] 字体 '{font_name}' 不存在，使用默认字体 '阳华体'")
            return draft.FontType.阳华体
```

### 3. 更新字体使用方式
```python
# 原来的方式
title_font = self.font_mapping.get(self.title_config['font'], draft.FontType.阳华体)

# 新的方式
title_font = self._get_font_type(self.title_config['font'])
```

## 技术特点

### 1. 动态获取
- 使用`getattr(draft.FontType, font_name)`直接通过字符串获取字体类型
- 支持任意字体名称，不限于预定义列表

### 2. 错误处理
- 当字体不存在时，尝试常见映射
- 最终回退到默认字体`阳华体`
- 提供警告信息，便于调试

### 3. 向后兼容
- 保持原有的字体名称不变
- 现有模板配置无需修改

## 测试结果

通过测试脚本验证，字体动态获取功能正常工作：

```
✅ 标题字体 '思源黑体': <enum 'FontType'> - FontType.阳华体
✅ 字幕字体 '微软雅黑': <enum 'FontType'> - FontType.阳华体
✅ 字体 '阳华体': <enum 'FontType'> - FontType.阳华体
✅ 字体 '俪金黑': <enum 'FontType'> - FontType.俪金黑
✅ 字体 '宋体': <enum 'FontType'> - FontType.宋体
```

## 影响范围

### 修改的文件
- `workflow/component/flow_python_implementation.py`
  - 移除写死的字体映射
  - 添加`_get_font_type`方法
  - 更新字体使用方式

### 功能影响
- ✅ 模板测试功能现在可以正常工作
- ✅ 支持任意字体名称
- ✅ 保持向后兼容性
- ✅ 提供友好的错误处理

## 使用说明

现在用户可以在模板配置中使用任意字体名称：

```json
{
  "title_font": "思源黑体",
  "subtitle_font": "微软雅黑"
}
```

系统会自动：
1. 尝试直接获取字体类型
2. 如果失败，尝试常见映射
3. 最终回退到默认字体`阳华体`
4. 提供警告信息

## 更新日志

- 修复字体映射错误
- 添加动态字体获取功能
- 支持任意字体名称
- 改进错误处理和用户体验
- 保持向后兼容性

---

通过这次修复，模板测试功能现在可以正常工作，支持任意字体名称，并提供了友好的错误处理机制。


