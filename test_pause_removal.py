#!/usr/bin/env python3
"""
测试停顿移除功能的诊断脚本
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def test_pause_removal():
    """测试停顿移除功能"""
    print("[诊断] 开始诊断停顿移除功能...")
    
    # 1. 检查ffmpeg是否可用
    print("\n1. 检查ffmpeg...")
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] ffmpeg可用")
        else:
            print("[ERROR] ffmpeg不可用")
            return False
    except FileNotFoundError:
        print("[ERROR] ffmpeg未找到，请确保ffmpeg已安装并添加到PATH")
        return False
    
    # 2. 检查ASR模块
    print("\n2. 检查ASR模块...")
    try:
        from workflow.component.volcengine_asr import VolcengineASR
        print("[OK] 火山ASR模块可用")
    except ImportError as e:
        print(f"[ERROR] 火山ASR模块导入失败: {e}")
        return False
    
    # 3. 检查停顿处理模块
    print("\n3. 检查停顿处理模块...")
    try:
        from workflow.component.asr_silence_processor import ASRBasedSilenceRemover
        print("[OK] 停顿处理模块可用")
    except ImportError as e:
        print(f"[ERROR] 停顿处理模块导入失败: {e}")
        return False
    
    # 4. 检查工作流模块
    print("\n4. 检查工作流模块...")
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        print("[OK] 工作流模块可用")
        
        # 检查add_audio方法的签名
        import inspect
        sig = inspect.signature(VideoEditingWorkflow.add_audio)
        params = list(sig.parameters.keys())
        print(f"   add_audio方法参数: {params}")
        
        if 'remove_pauses' in params:
            print("[OK] add_audio方法包含remove_pauses参数")
        else:
            print("[ERROR] add_audio方法缺少remove_pauses参数")
            return False
            
    except ImportError as e:
        print(f"[ERROR] 工作流模块导入失败: {e}")
        return False
    
    # 5. 检查是否有测试音频文件
    print("\n5. 检查测试音频文件...")
    test_audio_paths = [
        "temp_materials/audio.mp3",
        "D:/code/pyJianYingDraft/temp_materials/audio.mp3"
    ]
    
    audio_path = None
    for path in test_audio_paths:
        if os.path.exists(path):
            audio_path = path
            print(f"[OK] 找到测试音频文件: {path}")
            break
    
    if not audio_path:
        print("[ERROR] 未找到测试音频文件")
        return False
    
    # 6. 测试ASR配置
    print("\n6. 测试ASR配置...")
    # 这里需要真实的ASR配置才能测试
    print("[WARN] 需要ASR配置才能进行完整测试")
    print("   请确保以下配置正确:")
    print("   - volcengine_appid")
    print("   - volcengine_access_token")
    
    print("\n[OK] 基础诊断完成")
    print("如果停顿移除仍然不生效，请检查:")
    print("1. 调用add_audio时是否设置了remove_pauses=True")
    print("2. ASR配置是否正确")
    print("3. 音频文件是否可以正常访问")
    print("4. 网络连接是否正常")
    
    return True

if __name__ == "__main__":
    test_pause_removal()