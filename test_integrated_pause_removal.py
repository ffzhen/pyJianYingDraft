#!/usr/bin/env python3
"""
测试新的集成方案：先ASR识别，再处理停顿，最后调整字幕时间轴
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def test_integrated_pause_removal():
    """测试集成的停顿移除方案"""
    print("=== 测试集成停顿移除方案 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        # 创建工作流实例
        workflow = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_integrated"
        )
        
        print("[OK] 工作流创建成功")
        
        # 检查新方法是否存在
        if hasattr(workflow, '_process_audio_pauses_with_asr_result'):
            print("[OK] _process_audio_pauses_with_asr_result 方法存在")
        else:
            print("[ERROR] _process_audio_pauses_with_asr_result 方法不存在")
            return False
            
        if hasattr(workflow, '_adjust_subtitle_timings'):
            print("[OK] _adjust_subtitle_timings 方法存在")
        else:
            print("[ERROR] _adjust_subtitle_timings 方法不存在")
            return False
        
        # 检查add_captions方法签名
        import inspect
        sig = inspect.signature(workflow.add_captions)
        params = list(sig.parameters.keys())
        print(f"add_captions 参数: {params}")
        
        if 'caption_data' in params and sig.parameters['caption_data'].default is None:
            print("[OK] add_captions 方法支持可选的caption_data参数")
        else:
            print("[ERROR] add_captions 方法不支持可选的caption_data参数")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_subtitle_timing_adjustment():
    """测试字幕时间轴调整逻辑"""
    print("\n=== 测试字幕时间轴调整逻辑 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        workflow = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_subtitle_adjustment"
        )
        
        # 模拟原始字幕数据
        original_subtitles = [
            {'text': '第一句话', 'start': 0.0, 'end': 2.0},
            {'text': '第二句话', 'start': 2.5, 'end': 4.5},
            {'text': '第三句话', 'start': 5.0, 'end': 7.0}
        ]
        
        # 模拟停顿段落
        pause_segments = [
            (2.0, 2.5),  # 0.5秒停顿
            (4.5, 5.0)   # 0.5秒停顿
        ]
        
        print(f"原始字幕: {len(original_subtitles)} 段")
        for sub in original_subtitles:
            print(f"  {sub['text']}: {sub['start']:.1f}s - {sub['end']:.1f}s")
        
        print(f"停顿段落: {len(pause_segments)} 段")
        for i, (start, end) in enumerate(pause_segments):
            print(f"  停顿{i+1}: {start:.1f}s - {end:.1f}s ({end-start:.1f}s)")
        
        # 调用字幕时间轴调整方法
        adjusted_subtitles = workflow._adjust_subtitle_timings(original_subtitles, pause_segments)
        
        print(f"调整后字幕: {len(adjusted_subtitles)} 段")
        for sub in adjusted_subtitles:
            print(f"  {sub['text']}: {sub['start']:.1f}s - {sub['end']:.1f}s")
        
        # 验证调整是否正确
        expected_adjustments = [
            {'text': '第一句话', 'start': 0.0, 'end': 2.0},    # 不变
            {'text': '第二句话', 'start': 2.0, 'end': 4.0},    # 前移0.5秒
            {'text': '第三句话', 'start': 4.0, 'end': 6.0}     # 前移1.0秒
        ]
        
        success = True
        for i, (expected, actual) in enumerate(zip(expected_adjustments, adjusted_subtitles)):
            if (abs(expected['start'] - actual['start']) > 0.01 or 
                abs(expected['end'] - actual['end']) > 0.01):
                print(f"[ERROR] 字幕{i+1}调整不正确")
                print(f"  期望: {expected['start']:.1f}s - {expected['end']:.1f}s")
                print(f"  实际: {actual['start']:.1f}s - {actual['end']:.1f}s")
                success = False
        
        if success:
            print("[OK] 字幕时间轴调整正确")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_integration():
    """测试工作流集成"""
    print("\n=== 测试工作流集成 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        workflow = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_workflow_integration"
        )
        
        # 检查属性初始化
        if hasattr(workflow, 'adjusted_subtitles'):
            print("[OK] adjusted_subtitles 属性存在")
        else:
            print("[ERROR] adjusted_subtitles 属性不存在")
            return False
            
        if hasattr(workflow, 'original_subtitles'):
            print("[OK] original_subtitles 属性存在")
        else:
            print("[ERROR] original_subtitles 属性不存在")
            return False
        
        # 检查初始状态
        if not hasattr(workflow, 'adjusted_subtitles') or workflow.adjusted_subtitles is None:
            print("[OK] adjusted_subtitles 初始化为None")
        else:
            print("[ERROR] adjusted_subtitles 未正确初始化")
            return False
        
        # 模拟设置字幕数据
        test_subtitles = [
            {'text': '测试字幕', 'start': 1.0, 'end': 3.0}
        ]
        workflow.adjusted_subtitles = test_subtitles
        workflow.original_subtitles = test_subtitles
        
        # 检查设置是否成功
        if workflow.adjusted_subtitles == test_subtitles:
            print("[OK] 字幕数据设置成功")
        else:
            print("[ERROR] 字幕数据设置失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试集成停顿移除方案")
    print("=" * 50)
    
    success1 = test_integrated_pause_removal()
    success2 = test_subtitle_timing_adjustment()
    success3 = test_workflow_integration()
    
    if success1 and success2 and success3:
        print("\n[OK] 所有测试通过！")
        print("\n[说明] 集成方案说明:")
        print("1. 先用原始URL进行ASR识别，得到字幕和停顿信息")
        print("2. 下载音频到本地")
        print("3. 根据ASR结果移除停顿")
        print("4. 根据移除的停顿重新计算字幕时间轴")
        print("5. 只需调用一次ASR，效率更高")
        print("6. 字幕时间轴自动调整，无需二次识别")
    else:
        print("\n[ERROR] 部分测试失败")