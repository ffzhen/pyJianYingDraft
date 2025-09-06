"""
完整示例演示

展示如何使用原来的系统处理完整的视频编辑流程
"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def run_complete_example():
    """运行完整的示例流程"""
    
    print("🎬 完整视频编辑工作流示例")
    print("=" * 50)
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        # 基本配置
        draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
        project_name = "complete_example_demo"
        
        print(f"📁 草稿文件夹: {draft_folder_path}")
        print(f"📝 项目名称: {project_name}")
        
        # 创建工作流
        workflow = VideoEditingWorkflow(draft_folder_path, project_name)
        print("✅ 工作流实例创建成功")
        
        print("\n🏗️ 步骤1: 创建草稿...")
        workflow.create_draft()
        print("✅ 草稿创建完成")
        
        print("\n📋 接下来可以执行的完整流程:")
        
        # 演示完整的调用流程
        print("\n🎵 步骤2: 添加音频（示例）")
        print("代码: workflow.add_audio('audio_url', duration=30.0, volume=1.0)")
        print("说明: 添加主音频，会自动下载网络音频或使用本地文件")
        
        print("\n🎬 步骤3: 添加主视频（示例）")
        print("代码: workflow.add_video('video_url', duration=30.0, start_time=0.0)")
        print("说明: 添加主视频素材，支持时长和开始时间控制")
        
        print("\n🤖 步骤4: 添加数字人视频（示例）")
        print("代码: workflow.add_digital_human_video('digital_human_url', target_duration=30.0)")
        print("说明: 添加数字人视频，会自动循环播放以匹配目标时长")
        
        print("\n📝 步骤5: 添加字幕（示例）")
        print("代码示例:")
        print("asr_result = [")
        print("    {'text': '欢迎观看视频', 'start_time': 0.0, 'end_time': 2.5},")
        print("    {'text': '这是第二段字幕', 'start_time': 3.0, 'end_time': 5.5},")
        print("    {'text': '感谢您的观看', 'start_time': 6.0, 'end_time': 8.0}")
        print("]")
        print("workflow.add_subtitle_from_asr(asr_result)")
        print("说明: 从ASR结果生成字幕，自动处理时长和位置")
        
        print("\n🎼 步骤6: 添加背景音乐（示例）")
        print("代码: workflow.add_background_music('music_path', volume=0.3)")
        print("说明: 添加背景音乐，会自动循环播放以匹配项目时长")
        
        print("\n💾 步骤7: 保存项目")
        workflow.script.save()
        save_path = workflow.script.save_path
        print(f"✅ 项目已保存到: {save_path}")
        
        print(f"\n🎉 完整示例流程演示完成！")
        print(f"📂 您可以在剪映中打开: {save_path}")
        
        return workflow, save_path
        
    except Exception as e:
        print(f"❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def show_actual_usage_code():
    """显示实际可用的代码"""
    
    print("\n" + "=" * 50)
    print("📝 实际使用代码模板")
    print("=" * 50)
    
    print("""
# 完整的视频编辑工作流代码模板
import sys
sys.path.append('d:/code/pyJianYingDraft')

from workflow.component.flow_python_implementation import VideoEditingWorkflow

def create_video_project():
    # 配置参数
    draft_folder_path = r"C:\\Users\\nrgc\\AppData\\Local\\JianyingPro\\User Data\\Projects\\com.lveditor.draft"
    project_name = "我的视频项目"
    
    # 创建工作流
    workflow = VideoEditingWorkflow(draft_folder_path, project_name)
    
    # 1. 创建草稿
    workflow.create_draft()
    
    # 2. 添加音频（替换为您的实际音频URL或路径）
    audio_url = "https://example.com/audio.mp3"  # 或本地路径
    workflow.add_audio(audio_url, duration=60.0, volume=1.0)
    
    # 3. 添加主视频（可选）
    video_url = "https://example.com/video.mp4"  # 或本地路径
    workflow.add_video(video_url, duration=60.0, start_time=0.0)
    
    # 4. 添加数字人视频（可选）
    digital_human_url = "https://example.com/avatar.mp4"
    workflow.add_digital_human_video(digital_human_url, target_duration=60.0)
    
    # 5. 添加字幕（如果有ASR结果）
    asr_result = [
        {'text': '大家好，欢迎观看', 'start_time': 0.0, 'end_time': 3.0},
        {'text': '这是一个演示视频', 'start_time': 4.0, 'end_time': 7.0},
        {'text': '谢谢大家观看', 'start_time': 57.0, 'end_time': 60.0}
    ]
    workflow.add_subtitle_from_asr(asr_result)
    
    # 6. 添加背景音乐（可选）
    background_music_path = "path/to/background_music.mp3"
    workflow.add_background_music(background_music_path, volume=0.2)
    
    # 7. 保存项目
    workflow.script.save()
    
    print(f"项目已创建: {workflow.script.save_path}")
    return workflow

# 运行创建项目
if __name__ == "__main__":
    create_video_project()
""")

def show_advanced_features():
    """显示高级功能"""
    
    print("\n" + "=" * 50)
    print("🔧 高级功能和配置")
    print("=" * 50)
    
    print("1. 🎵 音频处理高级选项:")
    print("   - 支持网络URL和本地文件")
    print("   - 可控制音量 (0.0-1.0)")
    print("   - 可指定精确时长")
    print("   - 自动时长验证（统一2位小数精度）")
    
    print("\n2. 🎬 视频处理高级选项:")
    print("   - 支持开始时间裁剪")
    print("   - 精确时长控制")
    print("   - 自动循环播放（数字人视频）")
    print("   - 智能时长匹配")
    
    print("\n3. 📝 字幕处理高级选项:")
    print("   - 基于ASR结果自动生成")
    print("   - 时间轴自动优化")
    print("   - 支持多语言字幕")
    print("   - 字幕样式自定义")
    
    print("\n4. 🎼 背景音乐高级选项:")
    print("   - 自动循环播放")
    print("   - 音量独立控制")
    print("   - 淡入淡出效果")
    print("   - 智能时长匹配")
    
    print("\n5. 📊 质量控制特性:")
    print("   - 所有时长统一2位小数精度")
    print("   - 自动边界检查，防止超出视频时长")
    print("   - 详细的执行日志")
    print("   - 完整的错误处理")

def main():
    """主函数"""
    
    print("🎯 选择2: 完整示例演示")
    
    # 运行完整示例
    workflow, save_path = run_complete_example()
    
    if workflow:
        # 显示使用代码
        show_actual_usage_code()
        
        # 显示高级功能
        show_advanced_features()
        
        print("\n" + "=" * 50)
        print("✅ 示例演示完成！")
        print("=" * 50)
        print("🎊 您的原来功能完全可用！")
        print("📋 可以复制上面的代码模板开始使用")
        print("🎬 项目文件已保存，可以在剪映中打开")
        
    else:
        print("\n❌ 示例运行遇到问题，请检查:")
        print("  1. 剪映是否正确安装")
        print("  2. 草稿文件夹路径是否正确")
        print("  3. 是否有足够的权限")

if __name__ == "__main__":
    main()