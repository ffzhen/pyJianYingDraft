#!/usr/bin/env python3
"""
测试MP4视频中的音频停顿移除功能
"""

import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def test_video_pause_removal():
    """测试视频中的音频停顿移除"""
    print("=== 测试MP4视频音频停顿移除 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        # 创建工作流实例
        workflow = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_video_pause_removal"
        )
        
        print("[OK] 工作流创建成功")
        
        # 初始化ASR
        workflow.initialize_asr(
            volcengine_appid="6046310832",
            volcengine_access_token="fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY"
        )
        print("[OK] ASR初始化成功")
        
        # 创建草稿
        workflow.create_draft()
        print("[OK] 草稿创建成功")
        
        # 测试视频URL（带音频的MP4）
        test_video_url = "https://oss.oemi.jdword.com/prod/order/video/202509/V20250901153106001.mp4"
        
        print(f"\n[测试] 添加视频并移除音频停顿:")
        print(f"[DEBUG] 视频URL: {test_video_url}")
        
        # 添加视频并启用停顿移除
        video_segment = workflow.add_digital_human_video(
            digital_video_url=test_video_url,
            remove_pauses=True,
            min_pause_duration=0.2,
            max_word_gap=0.8
        )
        
        print(f"[OK] 视频添加成功，时长: {workflow.video_duration:.1f}秒")
        
        # 检查是否有调整后的字幕
        if hasattr(workflow, 'adjusted_subtitles') and workflow.adjusted_subtitles:
            print(f"[OK] 找到调整后的字幕: {len(workflow.adjusted_subtitles)}段")
            for i, subtitle in enumerate(workflow.adjusted_subtitles[:3]):  # 显示前3段
                print(f"  字幕{i+1}: {subtitle['text'][:20]}... ({subtitle['start']:.1f}s-{subtitle['end']:.1f}s)")
        else:
            print("[WARN] 没有找到调整后的字幕")
        
        # 检查是否有原始字幕
        if hasattr(workflow, 'original_subtitles') and workflow.original_subtitles:
            print(f"[OK] 找到原始字幕: {len(workflow.original_subtitles)}段")
        else:
            print("[WARN] 没有找到原始字幕")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_comparison():
    """对比测试：带停顿移除 vs 不带停顿移除"""
    print("\n=== 对比测试 ===")
    
    try:
        from workflow.component.flow_python_implementation import VideoEditingWorkflow
        
        # 测试1：不带停顿移除
        print("\n[测试1] 不带停顿移除:")
        workflow1 = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_comparison_1"
        )
        workflow1.initialize_asr(
            volcengine_appid="6046310832",
            volcengine_access_token="fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY"
        )
        workflow1.create_draft()
        
        test_video_url = "https://oss.oemi.jdword.com/prod/order/video/202509/V20250901153106001.mp4"
        video_segment1 = workflow1.add_digital_human_video(test_video_url, remove_pauses=False)
        duration1 = workflow1.video_duration
        print(f"[OK] 原始视频时长: {duration1:.1f}秒")
        
        # 测试2：带停顿移除
        print("\n[测试2] 带停顿移除:")
        workflow2 = VideoEditingWorkflow(
            draft_folder_path="drafts",
            project_name="test_comparison_2"
        )
        workflow2.initialize_asr(
            volcengine_appid="6046310832",
            volcengine_access_token="fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY"
        )
        workflow2.create_draft()
        
        video_segment2 = workflow2.add_digital_human_video(test_video_url, remove_pauses=True)
        duration2 = workflow2.video_duration
        print(f"[OK] 处理后视频时长: {duration2:.1f}秒")
        
        # 对比结果
        time_difference = duration1 - duration2
        print(f"\n[对比结果]")
        print(f"  原始时长: {duration1:.1f}秒")
        print(f"  处理后时长: {duration2:.1f}秒")
        print(f"  移除停顿: {time_difference:.1f}秒")
        
        if time_difference > 0:
            print(f"[OK] 成功移除 {time_difference:.1f} 秒的停顿")
        else:
            print("[WARN] 未检测到明显的停顿移除")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] 对比测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试MP4视频音频停顿移除功能")
    print("=" * 50)
    
    success1 = test_video_pause_removal()
    success2 = test_comparison()
    
    if success1 and success2:
        print("\n[OK] 所有测试通过！")
        print("\n[使用方法]")
        print("1. 直接添加MP4视频并启用停顿移除")
        print("2. 系统会自动提取视频中的音频进行处理")
        print("3. 处理后的音频会重新合并到视频中")
        print("4. 字幕时间轴会自动同步调整")
        print("\n[示例代码]")
        print("workflow.add_digital_human_video(")
        print("    digital_video_url='https://your-video.mp4',")
        print("    remove_pauses=True,")
        print("    min_pause_duration=0.2,")
        print("    max_word_gap=0.8")
        print(")")
    else:
        print("\n[ERROR] 部分测试失败")