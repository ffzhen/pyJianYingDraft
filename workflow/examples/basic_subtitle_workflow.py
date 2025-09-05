#!/usr/bin/env python3
"""
基础字幕工作流示例

演示如何使用component中的组件创建一个简单的音频转录字幕工作流
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from workflow.component.flow_python_implementation import VideoEditingWorkflow

def create_subtitle_workflow():
    """创建基础字幕工作流"""
    print("🎬 基础字幕工作流示例")
    print("=" * 50)
    
    # 配置剪映草稿文件夹路径（请根据实际情况修改）
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 创建工作流实例
    workflow = VideoEditingWorkflow(draft_folder_path, "subtitle_workflow_demo")
    
    # 配置输入参数
    inputs = {
        # 必需参数
        'audio_url': 'https://example.com/your_audio.wav',  # 请替换为真实音频URL
        'title': '基础字幕工作流演示',
        
        # 🔥 火山引擎ASR配置（语音识别）
        'volcengine_appid': '6046310832',
        'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',
        
        # 🤖 豆包API配置（关键词提取，可选）
        'doubao_token': 'your_doubao_token_here',  # 请替换为真实token
        'doubao_model': 'doubao-1-5-pro-32k-250115',
        
        # 可选参数
        'subtitle_delay': 0.0,      # 字幕延迟（秒）
        'subtitle_speed': 1.0,      # 字幕速度倍数
    }
    
    print("📋 工作流配置:")
    print(f"   项目名称: subtitle_workflow_demo")
    print(f"   音频URL: {inputs['audio_url']}")
    print(f"   字幕延迟: {inputs['subtitle_delay']}秒")
    print(f"   AI关键词提取: {'启用' if inputs.get('doubao_token') != 'your_doubao_token_here' else '禁用（使用本地算法）'}")
    
    return workflow, inputs

def run_workflow():
    """运行工作流"""
    try:
        # 创建工作流
        workflow, inputs = create_subtitle_workflow()
        
        print(f"\n🚀 开始执行工作流...")
        
        # 执行工作流
        save_path = workflow.process_workflow(inputs)
        
        print(f"\n✅ 工作流执行完成!")
        print(f"📁 剪映项目已保存到: {save_path}")
        print("🎬 请打开剪映查看生成的字幕项目")
        
        return save_path
        
    except Exception as e:
        print(f"❌ 工作流执行失败: {e}")
        print("\n🔧 请检查:")
        print("1. API配置是否正确")
        print("2. 音频URL是否可访问")
        print("3. 剪映草稿文件夹路径是否正确")
        return None

def main():
    """主函数"""
    print("🎯 这是一个基础字幕工作流示例")
    print("展示如何使用workflow组件创建简单的音频转录字幕工作流")
    print()
    
    # 询问是否运行
    response = input("是否立即运行工作流？(y/N): ").strip().lower()
    
    if response == 'y':
        run_workflow()
    else:
        print("📚 使用说明:")
        print("1. 修改 inputs 中的音频URL和API配置")
        print("2. 确保剪映草稿文件夹路径正确")
        print("3. 运行此脚本开始工作流")
        print()
        print("💡 提示: 这只是一个示例，您可以基于此创建更复杂的工作流")

if __name__ == "__main__":
    main()



