# 动态封面功能使用指南

## 功能概述

动态封面功能允许根据账号ID自动选择不同的封面图片，实现个性化的视频封面效果。

## 功能特性

- ✅ 支持根据账号ID动态选择封面图片
- ✅ 支持多种图片格式（jpg, png, jpeg）
- ✅ 支持多种目录结构
- ✅ 具有合理的优先级和兜底机制
- ✅ 与飞书批量生成完美集成

## 封面选择优先级

1. **直接传入的 cover_image_path**（最高优先级）
2. **账号动态封面路径**（中等优先级）
3. **模板配置的 cover_background**（最低优先级）
4. **默认封面 resource/查封面.jpg**（兜底）

## 支持的动态封面路径格式

### 1. 账号专用封面目录
```
resource/covers/{account_id}.jpg
resource/covers/{account_id}.png
resource/covers/{account_id}.jpeg
```

### 2. 账号专用封面文件（带前缀）
```
resource/covers/cover_{account_id}.jpg
resource/covers/cover_{account_id}.png
resource/covers/cover_{account_id}.jpeg
```

### 3. 模板目录下的账号封面
```
resource/templates/{account_id}/cover.jpg
resource/templates/{account_id}/cover.png
resource/templates/{account_id}/cover.jpeg
```

## 使用示例

### 示例1：为账号 "user001" 设置专用封面

1. 将封面图片命名为 `user001.jpg` 并放置在 `resource/covers/` 目录下
2. 在飞书任务数据中设置 `account_id: "user001"`
3. 系统会自动使用 `resource/covers/user001.jpg` 作为封面

### 示例2：为账号 "user002" 设置带前缀的封面

1. 将封面图片命名为 `cover_user002.png` 并放置在 `resource/covers/` 目录下
2. 在飞书任务数据中设置 `account_id: "user002"`
3. 系统会自动使用 `resource/covers/cover_user002.png` 作为封面

### 示例3：为账号 "user003" 设置模板目录封面

1. 创建目录 `resource/templates/user003/`
2. 将封面图片命名为 `cover.jpg` 并放置在 `resource/templates/user003/` 目录下
3. 在飞书任务数据中设置 `account_id: "user003"`
4. 系统会自动使用 `resource/templates/user003/cover.jpg` 作为封面

## 技术实现

### 核心方法

```python
def _get_dynamic_cover_path(self, account_id: str) -> Optional[str]:
    """根据账号ID获取动态封面图片路径"""
    if not account_id:
        return None
    
    # 定义动态封面图片的查找路径
    cover_paths = [
        f"resource/covers/{account_id}.jpg",
        f"resource/covers/{account_id}.png",
        f"resource/covers/{account_id}.jpeg",
        f"resource/covers/cover_{account_id}.jpg",
        f"resource/covers/cover_{account_id}.png",
        f"resource/covers/cover_{account_id}.jpeg",
        f"resource/templates/{account_id}/cover.jpg",
        f"resource/templates/{account_id}/cover.png",
        f"resource/templates/{account_id}/cover.jpeg",
    ]
    
    # 检查每个可能的路径
    for cover_path in cover_paths:
        full_path = os.path.join(project_root, cover_path)
        if os.path.exists(full_path):
            return full_path
    
    return None
```

### 集成流程

1. **飞书任务数据** → 包含 `account_id` 字段
2. **BatchCozeWorkflow** → 提取 `account_id` 并传递给 `CozeVideoWorkflow`
3. **CozeVideoWorkflow** → 将 `account_id` 传递给 `VideoEditingWorkflow`
4. **VideoEditingWorkflow** → 在 `process_workflow` 中调用 `_get_dynamic_cover_path`
5. **动态封面选择** → 根据账号ID选择对应的封面图片

## 注意事项

1. **文件命名**：确保封面文件名与账号ID完全匹配
2. **文件格式**：支持 jpg、png、jpeg 格式
3. **目录结构**：按照支持的路径格式组织文件
4. **兜底机制**：如果没有找到动态封面，会使用模板默认封面或系统默认封面
5. **性能优化**：系统会按优先级顺序查找，找到第一个匹配的文件即停止

## 故障排除

### 问题1：动态封面没有生效
- 检查账号ID是否正确传递
- 检查封面文件是否存在且路径正确
- 检查文件格式是否支持

### 问题2：封面显示为默认封面
- 检查是否在支持的路径格式中
- 检查文件名是否与账号ID匹配
- 检查文件权限是否正确

### 问题3：飞书批量生成时封面不正确
- 检查飞书任务数据中是否包含 `account_id` 字段
- 检查 `field_mapping` 配置是否正确
- 检查账号ID是否正确提取

## 更新日志

- **v1.0.0** - 初始版本，支持基本的动态封面功能
- **v1.1.0** - 添加多种路径格式支持
- **v1.2.0** - 集成飞书批量生成功能
- **v1.3.0** - 优化优先级机制和兜底逻辑
