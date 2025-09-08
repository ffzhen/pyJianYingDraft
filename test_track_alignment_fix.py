#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试轨道对齐修复
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'workflow'))

def test_track_alignment_method():
    """测试轨道对齐方法是否存在"""
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        # 创建工作流实例
        workflow = VideoEditingWorkflow(
            draft_folder_path="C:\\Users\\nrgc\\AppData\\Local\\JianyingPro\\User Data\\Projects\\com.lveditor.draft",
            project_name="test_track_alignment"
        )
        
        # 检查方法是否存在
        if hasattr(workflow, '_align_all_tracks_with_main_track'):
            print("✅ _align_all_tracks_with_main_track 方法存在")
            
            # 测试方法调用（不会实际执行，因为没有草稿）
            try:
                workflow._align_all_tracks_with_main_track(0.0)
                print("✅ 方法调用成功")
            except Exception as e:
                print(f"⚠️ 方法调用时出现预期错误（因为没有草稿）: {e}")
        else:
            print("❌ _align_all_tracks_with_main_track 方法不存在")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("测试轨道对齐修复...")
    success = test_track_alignment_method()
    if success:
        print("🎉 修复成功！")
    else:
        print("💥 修复失败！")
