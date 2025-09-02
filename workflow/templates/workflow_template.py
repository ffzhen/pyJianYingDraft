#!/usr/bin/env python3
"""
工作流模板

用于创建新的视频制作工作流的基础模板
复制此文件并根据需要修改
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from workflow.component.flow_python_implementation import VideoEditingWorkflow

class CustomWorkflow:
    """自定义工作流类"""
    
    def __init__(self, draft_folder_path: str, project_name: str = "custom_workflow"):
        """初始化工作流
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            project_name: 项目名称
        """
        self.draft_folder_path = draft_folder_path
        self.project_name = project_name
        self.workflow = VideoEditingWorkflow(draft_folder_path, project_name)
    
    def prepare_inputs(self, **kwargs) -> dict:
        """准备工作流输入参数
        
        Args:
            **kwargs: 自定义参数
            
        Returns:
            配置好的输入参数字典
        """
        # 基础配置
        inputs = {
            # 必需参数
            'audio_url': kwargs.get('audio_url', ''),
            'title': kwargs.get('title', self.project_name),
            
            # 火山引擎ASR配置
            'volcengine_appid': kwargs.get('volcengine_appid', '6046310832'),
            'volcengine_access_token': kwargs.get('volcengine_access_token', ''),
            
            # 豆包API配置（可选）
            'doubao_token': kwargs.get('doubao_token', ''),
            'doubao_model': kwargs.get('doubao_model', 'doubao-1-5-pro-32k-250115'),
            
            # 可选参数
            'subtitle_delay': kwargs.get('subtitle_delay', 0.0),
            'subtitle_speed': kwargs.get('subtitle_speed', 1.0),
        }
        
        # 添加其他自定义参数
        for key, value in kwargs.items():
            if key not in inputs:
                inputs[key] = value
        
        return inputs
    
    def pre_process(self, inputs: dict) -> dict:
        """预处理步骤（可重写）
        
        Args:
            inputs: 输入参数
            
        Returns:
            处理后的参数
        """
        print("🔧 执行预处理步骤...")
        
        # 在这里添加您的预处理逻辑
        # 例如：验证参数、下载文件、预处理数据等
        
        return inputs
    
    def post_process(self, result: str, inputs: dict) -> str:
        """后处理步骤（可重写）
        
        Args:
            result: 工作流执行结果（保存路径）
            inputs: 输入参数
            
        Returns:
            最终结果
        """
        print("🎨 执行后处理步骤...")
        
        # 在这里添加您的后处理逻辑
        # 例如：文件移动、格式转换、通知发送等
        
        return result
    
    def execute(self, **kwargs) -> str:
        """执行完整工作流
        
        Args:
            **kwargs: 工作流参数
            
        Returns:
            执行结果路径
        """
        try:
            print(f"🚀 开始执行工作流: {self.project_name}")
            
            # 1. 准备输入参数
            inputs = self.prepare_inputs(**kwargs)
            
            # 2. 预处理
            inputs = self.pre_process(inputs)
            
            # 3. 执行核心工作流
            result = self.workflow.process_workflow(inputs)
            
            # 4. 后处理
            final_result = self.post_process(result, inputs)
            
            print(f"✅ 工作流执行完成: {final_result}")
            return final_result
            
        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")
            raise

def create_custom_workflow():
    """创建自定义工作流的示例函数"""
    # 配置路径
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 创建工作流实例
    workflow = CustomWorkflow(draft_folder_path, "my_custom_workflow")
    
    # 配置参数
    config = {
        'audio_url': 'https://example.com/audio.wav',
        'title': '我的自定义工作流',
        'volcengine_access_token': 'your_asr_token',
        'doubao_token': 'your_doubao_token',
        'subtitle_delay': 0.5,  # 延迟0.5秒
    }
    
    # 执行工作流
    result = workflow.execute(**config)
    
    return result

def main():
    """主函数 - 展示如何使用模板"""
    print("📋 工作流模板使用说明")
    print("=" * 50)
    print("1. 复制此模板文件")
    print("2. 重命名为您的工作流名称")
    print("3. 修改 CustomWorkflow 类")
    print("4. 实现您的自定义逻辑")
    print("5. 运行工作流")
    print()
    print("🎯 模板特性:")
    print("- 预处理和后处理钩子")
    print("- 参数验证和配置")
    print("- 错误处理机制")
    print("- 可扩展的架构")
    print()
    print("💡 提示: 修改 pre_process() 和 post_process() 方法来自定义您的工作流")

if __name__ == "__main__":
    main()


