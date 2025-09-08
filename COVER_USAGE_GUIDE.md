# 封面功能使用指南

## 概述

已成功为 `flow_python_implementation.py` 添加了封面功能，通过 `CoverProcessor` 模块实现。封面功能支持：

- 在视频前2帧添加封面图片
- 添加自定义封面字幕（上方和下方）
- 自动应用时间轴偏移
- 字幕时间自动调整

## 使用方法

### 1. 在主流程中启用封面

```python
from workflow.component.flow_python_implementation import VideoEditingWorkflow

# 初始化工作流
workflow = VideoEditingWorkflow(draft_folder_path="/path/to/draft")

# 输入参数中包含封面配置
inputs = {
    'audio_url': 'https://example.com/audio.mp3',
    'volcengine_appid': 'your_appid',
    'volcengine_access_token': 'your_token',
    'enable_cover': True,  # 启用封面
    'cover_image_path': 'resource/封面.jpg',  # 封面图片路径
    'cover_top_text': '主标题',  # 封面上方文字
    'cover_bottom_text': '副标题',  # 封面下方文字
    'cover_frames': 2,  # 封面帧数
    'cover_fps': 30,  # 帧率
    # ... 其他参数
}

# 执行工作流
result = workflow.process_workflow(inputs)
```

### 2. 独立使用CoverProcessor

```python
from workflow.component.cover_processor import CoverProcessor
import pyJianYingDraft as draft

# 创建草稿
draft_folder = draft.DraftFolder("/path/to/draft")
script = draft_folder.create_draft("my_project", 1080, 1920)

# 初始化封面处理器
cover_processor = CoverProcessor(script=script)

# 启用封面
cover_processor.enable_cover(
    cover_image_path="resource/封面.jpg",
    frames=2,
    fps=30
)

# 处理封面并获取时间信息
result = cover_processor.process_cover_and_get_timing(
    top_text="主标题",
    bottom_text="副标题"
)

if result['success']:
    print(f"封面时长: {result['cover_duration']:.6f}秒")
    print(f"时间偏移: {result['time_offset']:.6f}秒")
    
    # 后续内容需要根据时间偏移调整
    time_offset = result['time_offset']
```

## 参数说明

### 封面相关参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_cover` | bool | False | 是否启用封面功能 |
| `cover_image_path` | str | None | 封面图片路径 |
| `cover_top_text` | str | "农村宅基地" | 封面上方文字 |
| `cover_bottom_text` | str | "农村还有宅基地的好好看这条视频" | 封面下方文字 |
| `cover_frames` | int | 2 | 封面持续帧数 |
| `cover_fps` | int | 30 | 帧率 |

### 时间偏移

- 封面时长 = `cover_frames / cover_fps`
- 默认情况下：2帧@30fps = 0.067秒
- 所有后续内容（视频、音频、字幕）都会自动向后偏移封面时长

## 时间轴偏移机制

### 1. 自动偏移逻辑

```python
# 原始字幕时间
original_subtitles = [
    {'start': 0.0, 'end': 2.0, 'text': '第一段字幕'},
    {'start': 2.0, 'end': 4.0, 'text': '第二段字幕'}
]

# 应用封面偏移后（假设封面时长0.067秒）
adjusted_subtitles = [
    {'start': 0.067, 'end': 2.067, 'text': '第一段字幕'},
    {'start': 2.067, 'end': 4.067, 'text': '第二段字幕'}
]
```

### 2. 片段处理

- 封面片段：0秒 - 0.067秒
- 主视频内容：0.067秒开始
- 音频内容：0.067秒开始
- 字幕内容：0.067秒开始

## 文件结构

```
workflow/
├── component/
│   ├── flow_python_implementation.py    # 主流程（已集成封面功能）
│   ├── cover_processor.py              # 封面处理器模块
│   └── ...
├── elegant_workflow.py                 # 优雅工作流
└── ...
```

## 测试

### 运行封面处理器测试

```bash
python workflow/component/cover_processor.py
```

### 运行集成测试

```bash
python test_cover_integration.py
```

## 注意事项

1. **封面图片路径**：支持相对路径和绝对路径，相对路径相对于项目根目录
2. **时间偏移**：封面功能会自动处理所有时间偏移，无需手动调整
3. **轨道管理**：封面会使用专门的轨道，不会与主内容冲突
4. **性能影响**：封面功能对性能影响极小（仅2帧）

## 故障排除

### 常见问题

1. **封面图片不存在**
   - 检查图片路径是否正确
   - 确保图片文件存在

2. **时间偏移不正确**
   - 检查 `cover_frames` 和 `cover_fps` 参数
   - 确认主流程中的时间偏移逻辑已启用

3. **封面字幕显示异常**
   - 检查字幕文本是否为空
   - 确认字体样式设置正确

### 调试方法

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查封面时间信息
timing_info = cover_processor.get_cover_timing_info()
print(f"封面时间信息: {timing_info}")
```

## 更新日志

- **2025-09-07**: 初始版本发布
  - 实现基本的封面添加功能
  - 集成时间轴偏移机制
  - 支持参数化配置