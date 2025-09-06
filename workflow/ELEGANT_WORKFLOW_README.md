# 优雅视频工作流 v2.0

这是一个全新重构的视频编辑工作流系统，采用模块化设计，职责分离，易于扩展和测试。

## ✨ 核心特性

- **🏗️ 模块化架构**: 清晰的职责分离，核心功能分布在不同模块中
- **📏 精确时长控制**: 所有时长统一保留2位小数，确保不超过视频总时长
- **🔧 非破坏性编辑**: 安全的素材处理和轨道管理
- **📝 完整错误处理**: 详细的异常处理和日志记录
- **📊 统计信息跟踪**: 实时统计处理结果和性能指标
- **🎯 双工作流模式**: 支持简化工作流和完整工作流

## 🏛️ 架构设计

```
workflow/
├── core/                    # 核心模块
│   ├── base.py             # 基础类和接口
│   ├── logger.py           # 日志系统
│   ├── config.py           # 配置管理
│   └── exceptions.py       # 异常定义
├── managers/               # 管理器模块
│   ├── duration_manager.py # 时长管理和验证
│   ├── track_manager.py    # 轨道管理
│   └── material_manager.py # 素材管理
├── processors/             # 处理器模块
│   ├── audio_processor.py  # 音频处理
│   ├── video_processor.py  # 视频处理
│   ├── subtitle_processor.py # 字幕处理
│   └── pause_processor.py  # 停顿处理
└── elegant_workflow.py     # 主工作流编排
```

## 🚀 快速开始

### 基础使用

```python
from workflow.elegant_workflow import create_elegant_workflow

# 创建工作流
workflow = create_elegant_workflow(
    draft_folder_path="剪映草稿文件夹路径",
    project_name="我的项目"
)

# 简化工作流 - 适合基础场景
inputs = {
    "audio_url": "音频文件URL",
    "background_music_path": "背景音乐路径",
    "background_music_volume": 0.3,
    "title": "项目标题"
}

save_path = workflow.process_simple_workflow(inputs)
```

### 完整工作流

```python
# 完整工作流 - 支持所有功能
complete_inputs = {
    "audio_url": "音频文件URL",
    "video_url": "主视频URL", 
    "digital_human_url": "数字人视频URL",
    "background_music_path": "背景音乐路径",
    "background_music_volume": 0.25,
    "title": "项目标题",
    "title_duration": 3.0,
    "asr_result": [
        {"text": "字幕文本", "start_time": 0.0, "end_time": 3.0},
        # 更多ASR结果...
    ],
    "apply_pauses": True,
    "pause_intensity": 0.6
}

save_path = workflow.process_complete_workflow(complete_inputs)
```

## 🔧 单独使用处理器

```python
# 单独使用音频处理器
workflow.add_audio("audio_url", duration=10.0, volume=1.0)
workflow.add_background_music("music.mp3", volume=0.3)

# 单独使用视频处理器  
workflow.add_video("video_url", duration=15.0)
workflow.add_digital_human_video("digital_human_url")

# 单独使用字幕处理器
workflow.add_subtitle_from_asr(asr_result)
workflow.add_title_subtitle("标题文本", start_time=0.0, duration=3.0)

# 单独使用停顿处理器
workflow.apply_natural_pauses(asr_result, pause_intensity=0.5)
```

## 📊 核心模块说明

### DurationManager (时长管理器)
- **功能**: 时长验证、边界检查、格式化
- **特性**: 确保所有时长保留2位小数，不超过视频总时长

### TrackManager (轨道管理器) 
- **功能**: 轨道创建、管理、清理
- **轨道类型**: 主视频、数字人视频、音频、背景音乐、字幕

### MaterialManager (素材管理器)
- **功能**: 素材下载、唯一文件名生成、临时文件管理
- **特性**: 自动处理网络资源和本地文件

### AudioProcessor (音频处理器)
- **功能**: 音频添加、背景音乐循环播放
- **特性**: 智能时长匹配、音量控制

### VideoProcessor (视频处理器)  
- **功能**: 主视频、数字人视频、背景视频处理
- **特性**: 自动循环播放、时长同步

### SubtitleProcessor (字幕处理器)
- **功能**: ASR字幕生成、标题字幕、自定义字幕
- **特性**: 时间优化、统计信息

### PauseProcessor (停顿处理器)
- **功能**: 自然停顿检测、同步停顿应用
- **特性**: 基于ASR结果的智能停顿

## ⚡ 性能优化

- **并行处理**: 多个处理器可并行工作
- **内存管理**: 智能的临时文件清理
- **错误恢复**: 优雅的错误处理和回退机制
- **日志系统**: 详细的执行日志和性能指标

## 🔄 与原系统对比

| 特性 | 原系统 | 新系统 |
|------|--------|--------|
| 架构 | 单一文件2500+行 | 模块化设计 |
| 时长精度 | 不统一(.1f, .2f混用) | 统一2位小数 |
| 错误处理 | 基础异常捕获 | 完整错误处理体系 |
| 可扩展性 | 难以扩展 | 高度可扩展 |
| 测试性 | 难以测试 | 易于单元测试 |
| 维护性 | 复杂 | 简单清晰 |

## 📝 使用示例

运行演示程序:

```bash
python workflow/elegant_workflow.py
```

演示程序会展示:
- 完整工作流处理 (包含所有功能)
- 简化工作流处理 (基础功能)
- 详细的执行日志
- 性能统计信息

## 🎯 设计原则

1. **单一职责**: 每个模块只负责一项功能
2. **依赖注入**: 通过构造函数注入依赖
3. **接口隔离**: 清晰的接口定义
4. **错误优先**: 完整的错误处理
5. **可观测性**: 详细的日志和统计

## 🔮 未来扩展

- [ ] 支持更多视频格式
- [ ] 批量处理功能
- [ ] 模板系统
- [ ] 插件架构
- [ ] Web API接口
- [ ] 实时预览功能

---

**版本**: v2.0  
**架构**: Modular Elegant Design  
**特性**: 非破坏性编辑，2位小数精度，完整验证体系