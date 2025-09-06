"""
Python交互式环境运行版本

直接在Python REPL中复制执行这些代码
"""

# 复制以下代码到Python交互式环境中：

import sys
import os

# 添加项目路径
sys.path.append('d:/code/pyJianYingDraft')

try:
    from workflow.component.flow_python_implementation import VideoEditingWorkflow
    
    # 配置参数
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    project_name = "interactive_test"
    
    print("🎬 在Python交互式环境中运行")
    print("=" * 40)
    
    # 创建工作流
    workflow = VideoEditingWorkflow(draft_folder_path, project_name)
    print("✅ 工作流创建成功")
    
    # 创建草稿
    workflow.create_draft()
    print("✅ 草稿创建完成")
    
    # 保存项目
    workflow.script.save()
    save_path = workflow.script.save_path
    print(f"✅ 项目已保存: {save_path}")
    
    print("\n🎊 成功！现在您可以使用以下方法:")
    print("workflow.add_audio('音频路径', duration=30.0)")
    print("workflow.add_video('视频路径', duration=30.0)")
    print("workflow.add_background_music('音乐路径', volume=0.3)")
    print("workflow.script.save()")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    print("请检查路径是否正确")

# 运行结果后，workflow变量就可以使用了