#!/usr/bin/env python3
"""
调试停顿移除功能
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def debug_pause_removal():
    """调试停顿移除功能"""
    print("=== 调试停顿移除功能 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        # 测试1：创建工作流实例用于不带停顿移除的测试
        workflow1 = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="debug_pause_removal_1"
        )
        
        print("[OK] 工作流1创建成功")
        
        # 检查ASR状态
        print(f"[DEBUG] workflow1.volcengine_asr: {workflow1.volcengine_asr}")
        
        # 如果你没有ASR配置，我们需要模拟一个
        if workflow1.volcengine_asr is None:
            print("[WARN] ASR未初始化，这可能是停顿移除不生效的原因")
            print("[INFO] 让我们检查ASR初始化方法...")
            
            # 检查是否有初始化ASR的方法
            if hasattr(workflow1, 'initialize_asr'):
                print("[OK] 找到initialize_asr方法")
                print("[INFO] 正在初始化ASR...")
                
                # 使用测试ASR配置
                try:
                    workflow1.initialize_asr(
                        volcengine_appid="6046310832",
                        volcengine_access_token="fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY"
                    )
                    print("[OK] ASR初始化成功")
                except Exception as e:
                    print(f"[ERROR] ASR初始化失败: {e}")
                    return False
            else:
                print("[ERROR] 没有找到initialize_asr方法")
                return False
        
        # 模拟一个音频URL
        test_audio_url = "https://oss.oemi.jdword.com/prod/temp/srt/V20250901152556001.wav"
        
        print(f"\n[DEBUG] 测试音频URL: {test_audio_url}")
        
        # 检查是否有现有的音频文件
        if os.path.exists("temp_materials/audio.mp3"):
            print("[DEBUG] 发现现有的音频文件")
            os.remove("temp_materials/audio.mp3")
            print("[DEBUG] 已删除现有音频文件")
        
        # 尝试创建草稿
        try:
            workflow1.create_draft()
            print("[OK] 草稿1创建成功")
        except Exception as e:
            print(f"[ERROR] 草稿1创建失败: {e}")
            return False
        
        # 如果你没有ASR配置，我们测试不带停顿移除的情况
        print(f"\n[测试1] 不带停顿移除:")
        try:
            audio_segment = workflow1.add_audio(
                audio_url=test_audio_url,
                remove_pauses=False
            )
            print(f"[OK] 音频添加成功，时长: {workflow1.audio_duration:.1f}秒")
        except Exception as e:
            print(f"[ERROR] 音频添加失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试带停顿移除的情况（需要ASR配置）- 创建新的工作流
        print(f"\n[测试2] 带停顿移除:")
        try:
            # 创建新的工作流实例以避免段重叠
            workflow2 = VideoEditingWorkflow(
                draft_folder_path="drafts",
                project_name="debug_pause_removal_2"
            )
            
            # 初始化ASR
            workflow2.initialize_asr(
                volcengine_appid="6046310832",
                volcengine_access_token="fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY"
            )
            
            # 创建草稿
            workflow2.create_draft()
            print("[OK] 草稿2创建成功")
            
            audio_segment = workflow2.add_audio(
                audio_url=test_audio_url,
                remove_pauses=True,
                min_pause_duration=0.2,
                max_word_gap=0.8
            )
            print(f"[OK] 音频添加成功，时长: {workflow2.audio_duration:.1f}秒")
            
            # 检查是否有调整后的字幕
            if hasattr(workflow2, 'adjusted_subtitles') and workflow2.adjusted_subtitles:
                print(f"[OK] 找到调整后的字幕: {len(workflow2.adjusted_subtitles)}段")
            else:
                print("[WARN] 没有找到调整后的字幕")
            
            # 检查是否有原始字幕
            if hasattr(workflow2, 'original_subtitles') and workflow2.original_subtitles:
                print(f"[OK] 找到原始字幕: {len(workflow2.original_subtitles)}段")
            else:
                print("[WARN] 没有找到原始字幕")
                
        except Exception as e:
            print(f"[ERROR] 带停顿移除的音频添加失败: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_asr_initialization():
    """检查ASR初始化相关的方法"""
    print("\n=== 检查ASR初始化 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        workflow = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="check_asr"
        )
        
        # 检查可用的方法
        methods = [method for method in dir(workflow) if 'asr' in method.lower()]
        print(f"[DEBUG] 包含'asr'的方法: {methods}")
        
        # 检查是否有initialize_asr方法
        if hasattr(workflow, 'initialize_asr'):
            print("[OK] 找到initialize_asr方法")
            
            # 检查方法签名
            import inspect
            sig = inspect.signature(workflow.initialize_asr)
            print(f"[DEBUG] initialize_asr签名: {sig}")
            
        else:
            print("[ERROR] 没有找到initialize_asr方法")
            print("[INFO] 可能需要先初始化ASR才能使用停顿移除功能")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        return False

if __name__ == "__main__":
    print("开始调试停顿移除功能")
    print("=" * 50)
    
    success1 = debug_pause_removal()
    success2 = check_asr_initialization()
    
    if success1 and success2:
        print("\n[OK] 调试完成")
        print("\n[可能的解决方案]")
        print("1. 确保已调用workflow.initialize_asr()配置ASR")
        print("2. 确保remove_pauses=True")
        print("3. 确保音频URL可以正常访问")
        print("4. 检查网络连接和ASR服务状态")
    else:
        print("\n[ERROR] 调试过程中发现问题")