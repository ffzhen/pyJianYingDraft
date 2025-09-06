"""
快速运行原来功能的脚本

提供简单的方式来运行您原来的视频编辑功能
"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def run_original_workflow():
    """运行原来的工作流功能"""
    
    print("🎬 运行原来的视频编辑功能")
    print("=" * 50)
    
    try:
        # 导入原来的工作流类
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        print("✅ 成功导入原来的工作流类")
        
        # 设置基本参数（请根据实际情况修改）
        draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
        project_name = "original_workflow_test"
        
        print(f"📁 草稿文件夹: {draft_folder_path}")
        print(f"📝 项目名称: {project_name}")
        
        # 创建工作流实例
        workflow = VideoEditingWorkflow(draft_folder_path, project_name)
        print("✅ 工作流实例创建成功")
        
        # 创建草稿
        print("\n🏗️ 创建草稿...")
        workflow.create_draft()
        print("✅ 草稿创建完成")
        
        # 演示添加音频（如果有的话）
        print("\n🎵 可以使用的原来的方法:")
        print("  workflow.add_audio(audio_url, duration, volume)")
        print("  workflow.add_background_music(music_path, target_duration, volume)")
        print("  workflow.add_video(video_url, duration, start_time)")
        print("  workflow.add_digital_human_video(digital_human_url, target_duration)")
        print("  workflow.add_subtitle_from_asr(asr_result)")
        print("  workflow.save_draft()")
        
        # 保存草稿
        print("\n💾 保存草稿...")
        workflow.save_draft()
        save_path = workflow.script.save_path
        print(f"✅ 草稿已保存到: {save_path}")
        
        return workflow, save_path
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请检查原来的文件是否存在")
        return None, None
        
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        print("请检查剪映草稿文件夹路径是否正确")
        return None, None

def run_with_sample_data():
    """使用示例数据运行完整流程"""
    
    print("\n🎬 使用示例数据运行完整流程")
    print("=" * 50)
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        # 基本设置
        draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
        project_name = "sample_workflow"
        
        workflow = VideoEditingWorkflow(draft_folder_path, project_name)
        
        # 创建草稿
        workflow.create_draft()
        
        # 示例：添加音频（请替换为实际的音频URL或路径）
        print("\n📋 示例操作流程:")
        print("1. 如果有音频文件:")
        print("   workflow.add_audio('your_audio.mp3', duration=30.0, volume=1.0)")
        
        print("2. 如果有背景音乐:")
        print("   workflow.add_background_music('background.mp3', volume=0.3)")
        
        print("3. 如果有视频:")
        print("   workflow.add_video('your_video.mp4', duration=30.0)")
        
        print("4. 如果有ASR结果:")
        print("   asr_result = [")
        print("       {'text': '字幕内容', 'start_time': 0.0, 'end_time': 3.0}")
        print("   ]")
        print("   workflow.add_subtitle_from_asr(asr_result)")
        
        # 保存
        workflow.save_draft()
        print(f"\n✅ 示例项目已创建: {workflow.script.save_path}")
        
        return workflow
        
    except Exception as e:
        print(f"❌ 示例运行出错: {e}")
        return None

def show_usage_guide():
    """显示使用指南"""
    
    print("\n📚 使用指南")
    print("=" * 50)
    
    print("🔧 方式1: 直接使用原来的系统")
    print("```python")
    print("from workflow.component.flow_python_implementation import VideoEditingWorkflow")
    print("")
    print("# 创建工作流")
    print("workflow = VideoEditingWorkflow(draft_folder_path, project_name)")
    print("")
    print("# 使用原来的方法")
    print("workflow.create_draft()")
    print("workflow.add_audio('audio.mp3')")
    print("workflow.add_background_music('music.mp3')")
    print("workflow.save_draft()")
    print("```")
    
    print("\n🔧 方式2: 使用新的优雅系统（修复API兼容性后）")
    print("```python")
    print("from workflow.elegant_workflow import create_elegant_workflow")
    print("")
    print("workflow = create_elegant_workflow(draft_folder_path, project_name)")
    print("inputs = {'audio_url': '...', 'title': '...'}")
    print("save_path = workflow.process_simple_workflow(inputs)")
    print("```")
    
    print("\n⚙️ 需要修改的参数:")
    print("  draft_folder_path: 您的剪映草稿文件夹路径")
    print("  project_name: 项目名称")
    print("  audio_url/path: 音频文件路径")
    print("  video_url/path: 视频文件路径")
    
    print("\n🔍 常见问题:")
    print("  1. 如果导入失败，检查文件路径")
    print("  2. 如果创建草稿失败，检查剪映文件夹权限")
    print("  3. 如果添加素材失败，检查文件是否存在")

def main():
    """主函数"""
    
    print("🎬 运行原来功能的脚本")
    print("选择运行方式:")
    print("1. 基础运行（创建空项目）")
    print("2. 示例运行（显示完整流程）")
    print("3. 显示使用指南")
    
    try:
        choice = input("\n请选择 (1/2/3): ").strip()
        
        if choice == "1":
            workflow, save_path = run_original_workflow()
            if workflow:
                print(f"\n🎉 成功！您可以在剪映中打开: {save_path}")
                
        elif choice == "2":
            workflow = run_with_sample_data()
            if workflow:
                print(f"\n🎉 示例完成！")
                
        elif choice == "3":
            show_usage_guide()
            
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")

if __name__ == "__main__":
    main()