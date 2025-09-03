# 视频模板架构设计文档

## 概述

为了解决多套视频模板的代码复用和维护问题，我们设计了一个基于**策略模式**和**工厂模式**的模板架构。该架构将样式配置与业务逻辑分离，支持轻松添加新的视频模板。

## 架构设计

### 1. 核心组件

```
workflow/component/
├── style_config.py              # 样式配置系统
├── video_template_base.py        # 模板基类和工厂
├── video_templates.py            # 具体模板实现
└── template_based_workflow.py    # 基于模板的工作流
```

### 2. 设计模式应用

#### 🏭 工厂模式 (Factory Pattern)
- **VideoTemplateFactory**: 负责创建不同类型的模板实例
- 支持动态注册新的模板类
- 统一的模板创建接口

#### 🎭 策略模式 (Strategy Pattern)  
- **VideoTemplateBase**: 抽象基类定义统一接口
- **具体模板类**: 实现不同的样式策略
- 运行时动态切换模板策略

#### ⚙️ 配置模式 (Configuration Pattern)
- **样式配置系统**: 将样式参数配置化
- 支持JSON序列化和反序列化
- 易于修改和扩展样式

### 3. 样式配置系统

#### 配置结构
```python
VideoStyleConfig                    # 视频整体配置
├── CaptionStyleConfig             # 字幕样式
│   ├── TextStyleConfig           # 基础文本样式
│   ├── HighlightStyleConfig      # 高亮样式  
│   ├── TextShadowConfig          # 阴影样式
│   └── TextBackgroundConfig      # 背景样式
├── TitleStyleConfig              # 标题样式
│   ├── TextStyleConfig           # 基础文本样式
│   ├── HighlightStyleConfig      # 高亮样式
│   ├── TextShadowConfig          # 阴影样式
│   └── TextBackgroundConfig      # 背景样式
└── VideoSettings                 # 视频设置
    ├── width/height/fps          # 视频参数
    └── background_music_volume   # 音量设置
```

#### 样式参数
- **字体**: font_type (俪金黑、文轩体、宋体、黑体)
- **颜色**: RGB元组 (0.0-1.0)
- **大小**: float数值
- **位置**: transform_y (-1.0 ~ 1.0)
- **背景**: 颜色、透明度、圆角等

### 4. 模板实现

#### 预置模板
1. **original** - 原有风格 (白色+黄色高亮)
2. **tech** - 科技风格 (青色+绿色高亮)
3. **warm** - 温馨风格 (暖色+粉红高亮)  
4. **business** - 商务风格 (黑白+蓝色高亮)

#### 模板类结构
```python
class OriginalStyleTemplate(VideoTemplateBase):
    def add_captions(self, caption_data, keywords):
        # 实现原有风格的字幕逻辑
    
    def add_title(self, title):
        # 实现原有风格的标题逻辑
```

### 5. 使用方式

#### 基本使用
```python
from workflow.component.template_based_workflow import create_workflow_with_template

# 创建工作流
workflow = create_workflow_with_template(
    draft_folder_path="C:/剪映草稿路径",
    template_name="tech",  # 使用科技风格
    project_name="我的视频"
)

# 处理视频
result = workflow.process_workflow({
    'audio_url': 'https://...',
    'title': '视频标题',
    'volcengine_appid': 'xxx',
    'volcengine_access_token': 'xxx'
})
```

#### 切换模板
```python
# 动态切换模板
workflow.change_template("warm")  # 切换到温馨风格
```

#### 列出模板
```python
from workflow.component.template_based_workflow import list_available_templates

templates = list_available_templates()
for template in templates:
    print(f"{template['name']}: {template['description']}")
```

## 扩展新模板

### 1. 创建样式配置

```python
# 在 style_config.py 中添加新配置
self.configs["modern"] = VideoStyleConfig(
    description="现代简约风格",
    tags=["现代", "简约", "时尚"],
    caption_style=CaptionStyleConfig(
        base_style=TextStyleConfig(
            font_type="文轩体",
            size=10.0,
            color=(0.5, 0.5, 0.5),  # 灰色
            # ... 其他样式参数
        ),
        # ... 其他配置
    ),
    # ... 其他配置
)
```

### 2. 创建模板类

```python
# 在 video_templates.py 中添加新模板类
class ModernStyleTemplate(VideoTemplateBase):
    def add_captions(self, caption_data, keywords):
        # 实现现代风格的字幕逻辑
        pass
    
    def add_title(self, title):
        # 实现现代风格的标题逻辑
        pass

# 注册模板
VideoTemplateFactory.register_template("modern", ModernStyleTemplate)
```

### 3. 自定义配置文件

```python
# 保存配置到文件
style_config_manager.save_config("modern", "modern_style.json")

# 从文件加载配置  
style_config_manager.load_config("modern", "modern_style.json")
```

## 优势特点

### ✅ 高复用性
- 共同的业务逻辑在基类中实现
- 只需重写样式相关的抽象方法
- 减少重复代码

### ✅ 易维护  
- 样式配置与业务逻辑分离
- 修改样式只需改配置文件
- 新增模板不影响现有代码

### ✅ 易扩展
- 标准化的模板创建流程
- 支持动态注册新模板
- 配置化的样式参数

### ✅ 类型安全
- 使用dataclass定义配置结构
- 明确的参数类型和默认值
- IDE智能提示支持

### ✅ 配置持久化
- 支持JSON格式的配置文件
- 可导出和导入样式配置
- 便于分享和备份

## 迁移指南

### 从旧版本迁移

1. **替换导入**
```python
# 旧版本
from workflow.component.flow_python_implementation import VideoEditingWorkflow

# 新版本  
from workflow.component.template_based_workflow import create_workflow_with_template
```

2. **修改创建方式**
```python
# 旧版本
workflow = VideoEditingWorkflow(draft_folder_path, project_name)

# 新版本
workflow = create_workflow_with_template(draft_folder_path, "original", project_name)
```

3. **参数调整**
```python
# 新版本支持模板选择
workflow.change_template("tech")  # 切换到科技风格
```

## 最佳实践

### 1. 样式设计
- 保持风格一致性
- 考虑不同场景的适用性
- 测试不同分辨率的显示效果

### 2. 性能优化
- 复用字体资源
- 避免重复创建配置对象
- 使用对象池管理模板实例

### 3. 配置管理
- 使用有意义的模板名称
- 添加详细的描述和标签
- 定期备份配置文件

### 4. 扩展开发
- 遵循开闭原则
- 保持向后兼容性
- 添加充分的注释和文档

---

这个架构设计为您提供了一个灵活、可扩展的视频模板系统，能够轻松管理和维护多套视频样式模板。