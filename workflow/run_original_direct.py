"""
直接运行原来功能

不需要用户输入，直接演示如何使用原来的系统
"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def main():
    """直接演示原来的功能"""
    
    print("🎬 直接运行原来的视频编辑功能")
    print("=" * 50)
    
    try:
        # 导入原来的工作流类
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        print("✅ 成功导入原来的工作流类")
        
        # 设置基本参数（请根据实际情况修改这些路径）
        draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
        project_name = "test_original_workflow"
        
        print(f"📁 草稿文件夹: {draft_folder_path}")
        print(f"📝 项目名称: {project_name}")
        
        # 创建工作流实例
        workflow = VideoEditingWorkflow(draft_folder_path, project_name)
        print("✅ 工作流实例创建成功")
        
        # 创建草稿
        print("\n🏗️ 创建草稿...")
        workflow.create_draft()
        print("✅ 草稿创建完成")
        
        # 保存草稿
        print("\n💾 保存草稿...")
        workflow.script.save()
        save_path = workflow.script.save_path
        print(f"✅ 草稿已保存到: {save_path}")
        
        print("\n🎉 原来的功能运行成功！")
        print(f"📂 您可以在剪映中打开这个项目: {save_path}")
        
        print("\n📋 您可以继续使用这些原来的方法:")
        print("```python")
        print("# 添加音频")
        print("workflow.add_audio('音频路径或URL', duration=30.0, volume=1.0)")
        print("")
        print("# 添加背景音乐") 
        print("workflow.add_background_music('音乐路径', volume=0.3)")
        print("")
        print("# 添加视频")
        print("workflow.add_video('视频路径或URL', duration=30.0)")
        print("")
        print("# 添加数字人视频")
        print("workflow.add_digital_human_video('数字人视频URL', target_duration=30.0)")
        print("")
        print("# 添加字幕（从ASR结果）")
        print("asr_result = [")
        print("    {'text': '字幕内容', 'start_time': 0.0, 'end_time': 3.0},")
        print("    # 更多字幕...")
        print("]")
        print("workflow.add_subtitle_from_asr(asr_result)")
        print("")
        print("# 保存草稿")
        print("workflow.script.save()")
        print("```")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("\n🔍 可能的原因:")
        print("  1. 原来的文件路径不正确")
        print("  2. 缺少依赖模块")
        
        print("\n💡 解决方法:")
        print("  检查这个文件是否存在:")
        print("  workflow/component/flow_python_implementation.py")
        
        return False
        
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        print("\n🔍 可能的原因:")
        print("  1. 剪映草稿文件夹路径不正确")
        print("  2. 没有权限访问剪映文件夹")
        print("  3. 剪映没有正确安装")
        
        print("\n💡 解决方法:")
        print("  1. 检查剪映安装路径")
        print("  2. 确保剪映草稿文件夹存在")
        print("  3. 以管理员权限运行")
        
        return False

def show_alternative_usage():
    """显示替代使用方法"""
    
    print("\n" + "=" * 50)
    print("🔄 其他使用方法")
    print("=" * 50)
    
    print("如果上面的方法不工作，您也可以:")
    
    print("\n1️⃣ 直接在Python中使用:")
    print("```python")
    print("import sys")
    print("sys.path.append('d:/code/pyJianYingDraft')")
    print("")
    print("from workflow.component.flow_python_implementation import VideoEditingWorkflow")
    print("")
    print("# 修改为您的实际路径")
    print("draft_path = r'C:\\Users\\您的用户名\\AppData\\Local\\JianyingPro\\User Data\\Projects\\com.lveditor.draft'")
    print("workflow = VideoEditingWorkflow(draft_path, '我的项目')")
    print("workflow.create_draft()")
    print("workflow.save_draft()")
    print("```")
    
    print("\n2️⃣ 在原来的脚本中使用:")
    print("  找到您原来调用视频编辑功能的脚本")
    print("  那些代码应该仍然可以正常工作")
    
    print("\n3️⃣ 新优雅系统（需要修复API兼容性）:")
    print("  等待API兼容性修复完成后")
    print("  可以使用更简洁的新系统")

if __name__ == "__main__":
    success = main()
    show_alternative_usage()
    
    if success:
        print("\n✅ 成功！您的原来功能可以正常使用。")
    else:
        print("\n❌ 需要解决一些问题才能运行原来的功能。")
        
    print("\n📚 更多帮助:")
    print("  - 查看 workflow/component/flow_python_implementation.py")  
    print("  - 查看 workflow/MIGRATION_GUIDE.md")
    print("  - 查看 workflow/ELEGANT_WORKFLOW_README.md")