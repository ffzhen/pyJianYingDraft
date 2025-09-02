# 工作流组件库

本目录包含已调试完成的核心工作流组件，可用于构建正式的视频制作工作流。

## 📦 组件列表

### 1. `flow_python_implementation.py`
**音频转录智能字幕工作流**

- ✅ 火山引擎ASR语音识别
- ✅ 豆包AI关键词提取
- ✅ 智能字幕高亮
- ✅ 剪映项目生成

**功能特性**：
- 自动音频转录为精确字幕
- AI识别重要关键词并高亮显示
- 支持字幕时间调整（延迟、速度）
- 生成完整剪映草稿项目

### 2. `volcengine_asr.py`
**火山引擎ASR + 豆包API集成模块**

- ✅ 火山引擎语音识别服务
- ✅ 豆包AI关键词提取服务
- ✅ 智能本地备用算法
- ✅ 错误处理和容错机制

**API配置**：
```python
# 火山引擎ASR（语音识别）
volcengine_appid = "6046310832"
volcengine_access_token = "fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY"

# 豆包API（关键词提取）
doubao_token = "您的豆包token"
doubao_model = "doubao-1-5-pro-32k-250115"
```

## 🚀 使用方法

### 快速开始
```python
from workflow.component.flow_python_implementation import VideoEditingWorkflow

# 创建工作流
workflow = VideoEditingWorkflow(draft_folder_path, project_name)

# 配置参数
inputs = {
    'audio_url': 'your_audio_file.wav',
    'volcengine_appid': '6046310832',
    'volcengine_access_token': 'your_asr_token',
    'doubao_token': 'your_doubao_token',
    'doubao_model': 'doubao-1-5-pro-32k-250115'
}

# 执行工作流
save_path = workflow.process_workflow(inputs)
```

### 完整示例
参考 `flow_python_implementation.py` 中的 `main()` 函数。

## 🎯 工作流架构

```
音频输入 → 火山引擎ASR → 文字转录
                           ↓
豆包AI ← 关键词提取 ← 转录文本
  ↓
关键词列表 → 智能高亮 → 富文本字幕
                        ↓
                   剪映项目生成
```

## 📋 已验证功能

- ✅ 音频转录准确性
- ✅ 关键词提取质量（优化前后对比）
- ✅ 字幕高亮精确性（只高亮关键词本身）
- ✅ API容错机制
- ✅ 剪映项目兼容性

## 🔧 技术特性

### 关键词提取优化
- **优化前**: `['突然被一', '段话触动', '允许的情', '况下']` ❌
- **优化后**: `['经济条件', '享受生活', '年轻', '触动']` ✅

### 高亮精确性
- 只高亮关键词本身，不影响其他文字
- 智能过滤：只显示文本中实际存在的关键词
- 支持重复关键词的正确处理

### 错误处理
- 豆包API失败时自动使用本地智能算法
- 网络异常、认证错误的优雅处理
- 详细的日志输出便于调试

## 📚 相关文档

- `API_CONFIG_GUIDE.md` - API配置指南
- `RICH_TEXT_HIGHLIGHT_GUIDE.md` - 富文本高亮功能说明

## 🎬 下一步

基于这些组件，您可以创建：
- 批量视频处理工作流
- 自定义字幕样式工作流  
- 多语言字幕工作流
- 视频剪辑自动化工作流

这些组件已经过充分测试，可以作为构建更复杂工作流的可靠基础。


