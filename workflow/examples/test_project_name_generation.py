#!/usr/bin/env python3
"""
测试 title + 时间戳作为项目名称的功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from workflow.examples.coze_complete_video_workflow import CozeVideoWorkflow

def test_project_name_generation():
    """测试项目名称生成"""
    print("Testing project name generation with title + timestamp...")
    
    # 创建工作流实例
    draft_folder_path = r"C:\Users\rgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    workflow = CozeVideoWorkflow(draft_folder_path)
    
    # 测试不同的标题
    test_titles = [
        "未来中国可能出现的九大变化",
        "做生意就不要对低端客户过度的服务",
        "AI Video Generation Test",
        "Test Title with Special Characters!@#$%"
    ]
    
    for title in test_titles:
        project_name = workflow.generate_project_name(title)
        print(f"Title: {title}")
        print(f"Generated Project Name: {project_name}")
        print("-" * 60)
    
    # 测试空标题
    empty_title_project = workflow.generate_project_name("")
    print(f"Empty Title - Generated Project Name: {empty_title_project}")
    print("-" * 60)
    
    # 测试 None 标题
    none_title_project = workflow.generate_project_name(None)
    print(f"None Title - Generated Project Name: {none_title_project}")

if __name__ == "__main__":
    test_project_name_generation()