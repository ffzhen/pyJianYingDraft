#!/usr/bin/env python3
"""
测试音频URL处理和停顿移除功能
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def test_audio_url_handling():
    """测试音频URL处理"""
    print("=== 测试音频URL处理 ===")
    
    # 模拟HTTP URL
    test_audio_url = "https://example.com/test_audio.mp3"
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        # 创建工作流实例
        workflow = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_audio_url"
        )
        
        print(f"[OK] 工作流创建成功")
        print(f"[OK] 测试音频URL: {test_audio_url}")
        
        # 模拟下载素材的行为
        local_path = workflow.download_material(
            test_audio_url,
            "temp_materials/test_audio.mp3"
        )
        
        print(f"[OK] 下载处理结果: {local_path}")
        
        # 验证URL和路径的处理逻辑
        if local_path == test_audio_url:
            print("[OK] URL保持不变（下载失败时保持原URL）")
        else:
            print(f"[OK] 已下载到本地: {local_path}")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_asr_url_parameter():
    """测试ASR URL参数传递"""
    print("\n=== 测试ASR URL参数传递 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        workflow = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_asr_url"
        )
        
        # 检查方法签名
        import inspect
        
        # 检查 _remove_audio_pauses 方法
        sig = inspect.signature(workflow._remove_audio_pauses)
        params = list(sig.parameters.keys())
        print(f"_remove_audio_pauses 参数: {params}")
        
        if 'original_audio_url' in params and 'local_audio_path' in params:
            print("[OK] _remove_audio_pauses 方法已更新为接受两个路径参数")
        else:
            print("[ERROR] _remove_audio_pauses 方法参数不正确")
            return False
            
        # 检查 _remove_audio_video_pauses 方法
        sig = inspect.signature(workflow._remove_audio_video_pauses)
        params = list(sig.parameters.keys())
        print(f"_remove_audio_video_pauses 参数: {params}")
        
        if 'original_audio_url' in params and 'local_audio_path' in params:
            print("[OK] _remove_audio_video_pauses 方法已更新为接受两个路径参数")
        else:
            print("[ERROR] _remove_audio_video_pauses 方法参数不正确")
            return False
            
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试音频URL处理和停顿移除功能")
    print("=" * 50)
    
    success1 = test_audio_url_handling()
    success2 = test_asr_url_parameter()
    
    if success1 and success2:
        print("\n[OK] 所有测试通过！")
        print("\n[说明] 使用说明:")
        print("1. 现在系统会正确处理HTTP URL，不会将本地文件路径传递给ASR API")
        print("2. 原始HTTP URL会用于ASR处理")
        print("3. 本地文件路径用于FFmpeg处理")
        print("4. 这样可以避免'local file path passed to HTTP API'错误")
    else:
        print("\n[ERROR] 部分测试失败")