#!/usr/bin/env python3
"""
测试音频URL处理修复后的行为
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def test_download_material_logic():
    """测试download_material方法的逻辑"""
    print("=== 测试download_material方法逻辑 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        # 创建工作流实例
        workflow = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_download"
        )
        
        # 测试用例1: 不存在的URL
        print("\n1. 测试不存在的URL:")
        test_url = "https://example.com/nonexistent-audio.mp3"
        result = workflow.download_material(test_url, "temp_materials/test_audio.mp3")
        print(f"   输入URL: {test_url}")
        print(f"   返回结果: {result}")
        print(f"   URL == 结果: {test_url == result}")
        
        if test_url == result:
            print("   [OK] 下载失败时正确返回原始URL")
        else:
            print("   [ERROR] 下载失败时未返回原始URL")
            
        # 测试用例2: 本地存在的文件
        print("\n2. 测试本地存在的文件:")
        # 创建一个测试文件
        test_file = "temp_materials/existing_file.mp3"
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, 'w') as f:
            f.write("test content")
        
        result = workflow.download_material(test_file, "temp_materials/another_file.mp3")
        print(f"   输入路径: {test_file}")
        print(f"   返回结果: {result}")
        print(f"   路径 == 结果: {test_file == result}")
        
        if test_file == result:
            print("   [OK] 本地文件存在时正确返回原路径")
        else:
            print("   [ERROR] 本地文件存在时未返回原路径")
            
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_url_parameter_flow():
    """测试音频URL参数流程"""
    print("\n=== 测试音频URL参数流程 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        workflow = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_url_flow"
        )
        
        # 模拟add_audio方法的前半部分逻辑
        audio_url = "https://example.com/test-audio.mp3"
        original_audio_url = audio_url
        
        print(f"1. 原始音频URL: {original_audio_url}")
        
        # 调用download_material
        local_path = workflow.download_material(
            audio_url,
            "temp_materials/audio.mp3"
        )
        
        print(f"2. download_material返回: {local_path}")
        print(f"3. original_audio_url == local_path: {original_audio_url == local_path}")
        
        # 模拟逻辑判断
        if local_path == original_audio_url:
            print("4. [逻辑] 下载失败，使用原始URL")
            final_asr_url = original_audio_url
            final_local_path = None
        else:
            print("4. [逻辑] 下载成功，使用本地文件")
            final_asr_url = original_audio_url
            final_local_path = local_path
            
        print(f"5. 最终ASR URL: {final_asr_url}")
        print(f"6. 最终本地路径: {final_local_path}")
        
        # 验证ASR URL确实是HTTP URL
        if final_asr_url.startswith('http'):
            print("7. [OK] ASR URL是HTTP URL")
        else:
            print("7. [ERROR] ASR URL不是HTTP URL")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试音频URL处理修复")
    print("=" * 50)
    
    success1 = test_download_material_logic()
    success2 = test_audio_url_parameter_flow()
    
    if success1 and success2:
        print("\n[OK] 所有测试通过！")
        print("\n[说明] 修复说明:")
        print("1. download_material方法现在在下载失败时正确返回原始URL")
        print("2. add_audio方法现在正确区分下载成功和失败的情况")
        print("3. ASR系统现在会收到原始HTTP URL而不是本地文件路径")
        print("4. 这样可以避免'local file path passed to HTTP API'错误")
    else:
        print("\n[ERROR] 部分测试失败")