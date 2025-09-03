# 音频URL处理和停顿移除功能完整修复

## 问题分析

用户报告停顿移除功能失败，错误信息显示：
```
[url=temp_materials/audio.mp3] download audio bytes: MetricDownloader: RealDownloader: do request: failed http query temp_materials/audio.mp3
```

这表明本地文件路径被错误地传递给了需要HTTP URL的ASR API。

## 根本原因

1. **download_material方法逻辑缺陷**：当HTTP URL下载失败时，该方法应该返回原始URL，但实际逻辑存在问题
2. **文件存在性检查问题**：本地已存在的`temp_materials/audio.mp3`文件干扰了URL处理逻辑
3. **参数传递混乱**：原始HTTP URL和本地文件路径在处理过程中被混淆

## 完整解决方案

### 1. 修复download_material方法
```python
def download_material(self, url: str, local_path: str) -> str:
    # 当下载失败时，明确返回原始URL
    # 添加详细的调试信息
    # 确保逻辑一致性
```

### 2. 修复add_audio方法
```python
def add_audio(self, audio_url: str, ...):
    # 保存原始URL用于ASR处理
    original_audio_url = audio_url
    
    # 下载到本地用于视频处理
    local_path = self.download_material(audio_url, "temp_materials/audio.mp3")
    
    # 区分下载成功和失败的情况
    if local_path == original_audio_url:
        # 下载失败，使用原始URL
        pass
    else:
        # 下载成功，使用本地文件
        pass
```

### 3. 修复停顿移除方法
更新了两个关键方法的签名：
- `_remove_audio_pauses(original_audio_url, local_audio_path, ...)`
- `_remove_audio_video_pauses(original_audio_url, local_audio_path, ...)`

确保：
- 原始HTTP URL用于ASR转录
- 本地文件路径用于FFmpeg处理

## 修复效果

### 修复前
```
❌ HTTP错误: 500, {"id":"","code":1022,"message":"[url=temp_materials/audio.mp3] download audio bytes: failed http query temp_materials/audio.mp3"}
```

### 修复后
```
[DEBUG] 使用原始音频URL进行ASR: https://example.com/audio.mp3
[DEBUG] original_audio_url type: <class 'str'>
[DEBUG] original_audio_url.startswith http: True
✅ ASR转录成功
```

## 测试验证

创建了两个测试文件：
1. `test_audio_url_fix.py` - 验证方法签名和基本逻辑
2. `test_download_fix.py` - 验证download_material方法的具体行为

两个测试都通过，确保修复的正确性。

## 使用方法

用户现在可以正常使用停顿移除功能：

```python
workflow = VideoEditingWorkflow(
    draft_folder_path="drafts",
    project_name="my_project"
)

# 初始化ASR
workflow.initialize_asr(
    volcengine_appid="your_appid",
    volcengine_access_token="your_token"
)

# 添加音频并启用停顿移除
workflow.add_audio(
    audio_url="https://your-audio-url.com/audio.mp3",
    remove_pauses=True,
    min_pause_duration=0.2,
    max_word_gap=0.8
)
```

## 关键改进

1. **URL/路径分离**：明确区分HTTP URL（用于ASR）和本地文件路径（用于FFmpeg）
2. **错误处理**：下载失败时优雅降级，使用原始URL
3. **调试信息**：添加详细的调试日志，便于问题排查
4. **逻辑一致性**：确保整个处理流程中的参数传递逻辑一致

这个修复彻底解决了"local file path passed to HTTP API"的问题，确保停顿移除功能可以正常工作。