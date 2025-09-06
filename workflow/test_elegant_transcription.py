"""
使用新优雅架构的音频转录智能字幕工作流测试

基于新的模块化架构实现完整的音频转录、字幕生成、关键词高亮和背景音乐功能
"""

import os
import sys
import time

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

# 尝试导入新架构，如果失败则回退到原架构
try:
    # 新架构导入（修复API兼容性后）
    from workflow.elegant_workflow import create_elegant_workflow
    USE_NEW_ARCHITECTURE = True
    print("✅ 使用新优雅架构")
except ImportError as e:
    # 回退到原架构
    from workflow.component.flow_python_implementation import VideoEditingWorkflow
    USE_NEW_ARCHITECTURE = False
    print(f"⚠️ 新架构暂时不可用({e})，回退到原架构")

def create_workflow_with_new_architecture(draft_folder_path: str, project_name: str):
    """使用新架构创建工作流"""
    workflow = create_elegant_workflow(draft_folder_path, project_name)
    return workflow

def create_workflow_with_old_architecture(draft_folder_path: str, project_name: str):
    """使用原架构创建工作流"""
    workflow = VideoEditingWorkflow(draft_folder_path, project_name)
    return workflow

def process_with_new_architecture(workflow, inputs):
    """使用新架构处理完整工作流"""
    # 转换输入格式为新架构格式
    new_inputs = {
        "audio_url": inputs.get("audio_url"),
        "video_url": inputs.get("digital_video_url"),  # 映射数字人视频
        "title": inputs.get("title"),
        "background_music_path": inputs.get("background_music_path"),
        "background_music_volume": inputs.get("background_music_volume", 0.25),
        
        # 新架构专用参数
        "apply_asr": True,  # 启用ASR转录
        "apply_keyword_highlighting": True,  # 启用关键词高亮
        "content_hint": inputs.get("content"),  # 内容提示用于关键词提取
        
        # API配置
        "volcengine_appid": inputs.get("volcengine_appid"),
        "volcengine_access_token": inputs.get("volcengine_access_token"),
        "doubao_token": inputs.get("doubao_token"),
        "doubao_model": inputs.get("doubao_model"),
    }
    
    # 使用新架构的完整工作流处理
    return workflow.process_complete_workflow(new_inputs)

def process_with_old_architecture(workflow, inputs):
    """使用原架构处理工作流"""
    # 使用原架构的process_workflow方法
    return workflow.process_workflow(inputs)

def main():
    """主函数 - 音频转录智能字幕工作流（新架构版本）"""
    
    print("🎬 音频转录智能字幕工作流 + AI关键词高亮 + 背景音乐")
    print("=" * 60)
    print("📋 功能说明:")
    print("  • 自动转录音频并生成智能字幕")
    print("  • 使用AI识别关键词进行高亮显示") 
    print("  • 添加华尔兹背景音乐")
    print("  • 采用新优雅架构（如可用）")
    
    # 配置剪映草稿文件夹路径
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    project_name = "elegant_audio_transcription_demo"
    
    # 配置华尔兹背景音乐路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..')
    background_music_path = os.path.join(project_root, '华尔兹.mp3')
    
    print(f"\n📁 草稿文件夹: {draft_folder_path}")
    print(f"📝 项目名称: {project_name}")
    print(f"🎼 背景音乐: {background_music_path}")
    
    # 配置输入参数
    inputs = {
        # 音频和视频素材
        "audio_url": "https://oss.oemi.jdword.com/prod/temp/srt/V20250904223919001.wav",
        "digital_video_url": "https://oss.oemi.jdword.com/prod/order/video/202509/V20250904224537001.mp4",
        
        # 内容和标题
        "content": "买房的时候你永远要记住一句话，在最贵的地方买最便宜的房子，千万不要在最便宜的地方买最贵的房子。你现在不理解这句话的含义，在你卖房子的时候，你就知道了，过来人都能听懂我这句话",
        "title": "买房子该怎么买，一定要牢记",
        
        # 火山引擎ASR配置
        'volcengine_appid': '6046310832',
        'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',
        
        # 豆包API配置
        'doubao_token': 'adac0afb-5fd4-4c66-badb-370a7ff42df5',
        'doubao_model': 'doubao-1-5-pro-32k-250115',
        
        # 背景音乐配置
        'background_music_path': background_music_path,
        'background_music_volume': 0.25,
    }
    
    start_time = time.time()
    
    try:
        print(f"\n🏗️ 创建工作流实例...")
        
        if USE_NEW_ARCHITECTURE:
            # 使用新优雅架构
            workflow = create_workflow_with_new_architecture(draft_folder_path, project_name)
            print("✅ 新优雅架构工作流创建成功")
            
            print(f"\n🚀 开始处理完整工作流（新架构）...")
            save_path = process_with_new_architecture(workflow, inputs)
            
        else:
            # 使用原架构
            workflow = create_workflow_with_old_architecture(draft_folder_path, project_name)
            print("✅ 原架构工作流创建成功")
            
            print(f"\n🚀 开始处理工作流（原架构）...")
            save_path = process_with_old_architecture(workflow, inputs)
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        print(f"\n🎉 音频转录工作流完成!")
        print(f"⏱️ 执行时间: {execution_time:.2f}秒")
        print(f"📂 剪映项目已保存到: {save_path}")
        
        # 显示功能总结
        print(f"\n📊 处理功能总结:")
        print(f"  ✅ 音频转录: ASR语音识别")
        print(f"  ✅ 智能字幕: 自动生成时间轴")
        print(f"  ✅ 关键词高亮: AI识别重点词汇") 
        print(f"  ✅ 数字人视频: 自动循环匹配")
        print(f"  ✅ 背景音乐: 华尔兹循环播放")
        print(f"  ✅ 架构: {'新优雅模块化' if USE_NEW_ARCHITECTURE else '原稳定版本'}")
        
        print(f"\n🎬 请打开剪映查看生成的智能字幕视频项目")
        
        return save_path
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"\n❌ 工作流失败: {e}")
        print(f"⏱️ 失败前耗时: {execution_time:.2f}秒")
        
        # 显示详细错误信息
        import traceback
        print(f"\n🔍 详细错误信息:")
        traceback.print_exc()
        
        # 提供解决建议
        print(f"\n💡 可能的解决方案:")
        print(f"  1. 检查剪映草稿文件夹路径是否正确")
        print(f"  2. 确认火山引擎ASR配置是否有效")
        print(f"  3. 验证豆包API token是否可用")
        print(f"  4. 检查网络连接和素材URL是否可访问")
        print(f"  5. 确保华尔兹.mp3文件存在")
        
        return None

def demo_architecture_comparison():
    """演示新旧架构对比"""
    
    print(f"\n🏗️ 架构对比说明")
    print("=" * 60)
    
    print("📊 新优雅架构特性:")
    print("  • 模块化设计，职责清晰分离")
    print("  • 统一2位小数精度控制")
    print("  • 完整的边界验证和错误处理")
    print("  • 支持简化和完整两种工作流模式")
    print("  • 详细的执行日志和统计信息")
    print("  • 非破坏性编辑保证")
    
    print(f"\n📊 架构使用状态:")
    if USE_NEW_ARCHITECTURE:
        print("  ✅ 当前使用新优雅架构")
        print("  🎯 享受模块化设计的优势")
    else:
        print("  ⚠️ 当前使用原架构（稳定版本）")
        print("  🔧 等待新架构API兼容性修复")
    
    print(f"\n🔄 功能完全兼容:")
    print("  • 无论使用哪种架构，功能完全一致")
    print("  • 自动选择最佳可用架构")
    print("  • 保证业务功能不受影响")

def show_usage_guide():
    """显示使用指南"""
    
    print(f"\n📚 使用指南")
    print("=" * 60)
    
    print("🔧 直接运行:")
    print("  python workflow/test_elegant_transcription.py")
    
    print(f"\n🔧 自定义参数运行:")
    print("```python")
    print("# 修改main()函数中的inputs配置")
    print("inputs = {")
    print('    "audio_url": "您的音频URL",')
    print('    "digital_video_url": "您的数字人视频URL",')
    print('    "title": "您的标题",')
    print('    "content": "您的内容提示",')
    print('    # ... 其他配置')
    print("}")
    print("```")
    
    print(f"\n🔧 集成到其他项目:")
    print("```python")
    print("from workflow.test_elegant_transcription import main")
    print("save_path = main()  # 返回保存路径")
    print("```")

if __name__ == "__main__":
    # 显示架构对比
    demo_architecture_comparison()
    
    # 运行主函数
    result = main()
    
    if result:
        print(f"\n✅ 测试完成！项目文件: {result}")
        
        # 显示使用指南
        show_usage_guide()
        
    else:
        print(f"\n❌ 测试失败，请检查配置和环境")
        
    print(f"\n👋 感谢使用优雅工作流系统！")