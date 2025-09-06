# 视频制作工作流系统

专业的视频制作自动化工作流集合，基于剪映API和AI服务构建。

## 📁 目录结构

```
workflow/
├── component/              # 核心组件库
│   ├── flow_python_implementation.py  # 音频转录智能字幕工作流
│   ├── volcengine_asr.py              # 火山引擎ASR + 豆包API模块
│   └── README.md                      # 组件说明文档
│
├── examples/               # 工作流示例（待创建）
├── templates/              # 工作流模板（待创建）
└── README.md              # 本文件
```

## 🎯 核心功能

### 已完成的组件
- ✅ **音频转录智能字幕**: 自动生成带AI关键词高亮的字幕
- ✅ **火山引擎ASR集成**: 高精度语音识别服务
- ✅ **豆包AI关键词提取**: 智能识别重要词汇进行高亮

### 计划中的工作流
- 🔄 批量视频处理工作流
- 🔄 多语言字幕生成工作流
- 🔄 视频剪辑自动化工作流
- 🔄 社交媒体视频优化工作流

## 🚀 快速开始

### 1. 环境准备
确保已安装 `pyJianYingDraft` 包和相关依赖。

### 2. API配置
配置必要的API密钥：
```python
# 火山引擎ASR（语音识别）
volcengine_appid = "your_appid"
volcengine_access_token = "your_asr_token"

# 豆包API（关键词提取，可选）
doubao_token = "your_doubao_token"
doubao_model = "doubao-1-5-pro-32k-250115"
```

### 3. 运行示例工作流
```python
from workflow.component.flow_python_implementation import VideoEditingWorkflow

# 创建并执行工作流
workflow = VideoEditingWorkflow(draft_folder_path)
result = workflow.process_workflow(inputs)
```

## 🎬 工作流类型

### 基础工作流
- **音频转录字幕**: 将音频文件转换为带时间戳的字幕
- **关键词高亮**: AI识别并高亮重要词汇
- **项目生成**: 自动创建剪映草稿项目

### 高级工作流（规划中）
- **批量处理**: 一次处理多个视频文件
- **样式定制**: 自定义字幕样式和布局
- **多轨道编辑**: 复杂的视频剪辑工作流
- **自动发布**: 完成后自动导出和发布

## 🔧 技术架构

```
输入素材 → 工作流引擎 → AI服务集成 → 剪映项目生成
    ↓           ↓            ↓           ↓
  音频/视频   流程控制    语音识别/NLP   草稿文件输出
```

### 核心技术栈
- **剪映API**: `pyJianYingDraft` 包
- **语音识别**: 火山引擎ASR
- **AI服务**: 豆包API
- **工作流引擎**: Python + 组件化架构

## 📊 性能特性

- ⚡ **高效处理**: 优化的API调用和错误处理
- 🛡️ **容错机制**: 多重备用方案确保稳定性
- 🎯 **精确控制**: 精细的参数调节和自定义选项
- 📈 **可扩展性**: 模块化设计便于功能扩展

## 📚 文档和支持

- **组件文档**: `component/README.md`
- **API配置**: `../API_CONFIG_GUIDE.md`
- **功能说明**: `../RICH_TEXT_HIGHLIGHT_GUIDE.md`

## 🎉 开始创建您的工作流

这个目录已经为您准备好了坚实的基础组件。您可以：

1. **直接使用现有组件**: 调用 `component/` 中的模块
2. **创建自定义工作流**: 基于现有组件构建新的工作流
3. **扩展功能**: 添加新的AI服务或处理步骤

让我们开始构建专业的视频制作自动化系统吧！🚀





