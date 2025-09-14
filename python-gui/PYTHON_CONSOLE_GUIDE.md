# Python控制台使用指南

## 功能概述

Python控制台是内置在视频生成器GUI中的交互式Python执行环境，允许您直接在GUI中编写、运行和调试Python代码，无需打开外部终端。

## 主要特性

### 🎯 核心功能
- **代码编辑器**：支持多行Python代码输入，使用等宽字体
- **实时输出**：显示代码执行结果、错误信息和调试输出
- **后台执行**：代码在后台线程中执行，不会阻塞GUI界面
- **输出重定向**：自动捕获`print()`输出和错误信息
- **工作目录**：自动设置为项目根目录，便于访问项目文件

### 🛠️ 控制功能
- **运行代码**：执行当前编辑器中的Python代码
- **清空代码**：清空代码编辑器内容
- **清空输出**：清空输出显示区域
- **停止执行**：停止正在运行的代码（如果支持）

### 📦 预置环境
控制台提供了以下预置变量和模块：
- `PROJECT_ROOT`：项目根目录路径
- `datetime`：日期时间模块
- `json`：JSON处理模块
- `os`：操作系统接口模块
- `sys`：系统特定参数和函数模块

## 使用方法

### 1. 打开Python控制台
1. 启动视频生成器GUI
2. 点击"Python控制台"标签页
3. 控制台会自动加载示例代码

### 2. 编写代码
在代码编辑器中输入Python代码，支持：
- 多行代码
- 注释
- 函数定义
- 类定义
- 导入模块

### 3. 运行代码
1. 点击"运行代码"按钮
2. 代码将在后台执行
3. 执行结果会显示在输出区域

### 4. 查看输出
输出区域会显示：
- 标准输出（print语句）
- 错误信息
- 执行时间戳
- 执行状态

## 使用示例

### 示例1：基本输出
```python
# 打印当前时间
from datetime import datetime
print(f"当前时间: {datetime.now()}")
```

### 示例2：文件操作
```python
# 读取配置文件
import json
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print("配置加载成功:")
    for key, value in config.items():
        print(f"  {key}: {value}")
except Exception as e:
    print(f"配置加载失败: {e}")
```

### 示例3：测试模板配置
```python
# 测试模板配置
import json
templates_file = "templates.json"
try:
    with open(templates_file, 'r', encoding='utf-8') as f:
        templates = json.load(f)
    print("可用模板:")
    for name, config in templates.items():
        print(f"  - {name}: {config.get('name', '未知')}")
        print(f"    封面背景: {config.get('cover_background', 'N/A')}")
        print(f"    标题字体: {config.get('cover_title_font', 'N/A')}")
except Exception as e:
    print(f"加载模板失败: {e}")
```

### 示例4：测试工作流模块
```python
# 测试工作流模块导入
try:
    from workflow.examples.coze_complete_video_workflow import CozeVideoWorkflow
    print("✅ CozeVideoWorkflow 导入成功")
    
    from workflow.component.flow_python_implementation import VideoEditingWorkflow
    print("✅ VideoEditingWorkflow 导入成功")
    
    from workflow.feishu_async_batch_workflow import FeishuAsyncBatchWorkflow
    print("✅ FeishuAsyncBatchWorkflow 导入成功")
    
    print("🎉 所有工作流模块导入成功！")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
```

### 示例5：调试配置
```python
# 调试当前配置
import json
import os

print("=== 配置调试 ===")
print(f"项目根目录: {PROJECT_ROOT}")
print(f"当前工作目录: {os.getcwd()}")

# 检查配置文件
config_files = ['config.json', 'templates.json', 'workflows.json']
for file in config_files:
    file_path = os.path.join(PROJECT_ROOT, 'python-gui', file)
    if os.path.exists(file_path):
        print(f"✅ {file} 存在")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"   - 文件大小: {len(str(data))} 字符")
        except Exception as e:
            print(f"   - 读取错误: {e}")
    else:
        print(f"❌ {file} 不存在")
```

## 注意事项

### ⚠️ 安全提醒
- 控制台具有完整的Python执行权限
- 请谨慎执行未知来源的代码
- 避免执行可能损坏系统的操作

### 🔧 技术限制
- 代码在后台线程中执行，某些GUI操作可能受限
- 长时间运行的代码会阻塞控制台
- 无法直接与GUI组件交互

### 💡 最佳实践
- 使用try-except处理异常
- 及时清理输出避免信息过载
- 利用预置变量简化代码
- 测试代码片段后再执行完整脚本

## 故障排除

### 常见问题

**Q: 代码执行后没有输出？**
A: 检查代码中是否有print语句，确保输出被正确捕获。

**Q: 导入模块失败？**
A: 确保模块路径正确，项目根目录已添加到sys.path。

**Q: 文件操作失败？**
A: 检查文件路径，使用相对路径时以项目根目录为基准。

**Q: 代码执行卡住？**
A: 点击"停止执行"按钮，检查代码是否有无限循环。

## 高级用法

### 自定义模块导入
```python
# 添加自定义路径
import sys
sys.path.append('/path/to/your/modules')
import your_module
```

### 调试技巧
```python
# 使用pdb调试
import pdb
pdb.set_trace()  # 设置断点
```

### 性能测试
```python
# 测试代码执行时间
import time
start_time = time.time()
# 你的代码
end_time = time.time()
print(f"执行时间: {end_time - start_time:.2f}秒")
```

通过Python控制台，您可以方便地测试、调试和验证各种功能，提高开发效率！
