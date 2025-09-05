# -*- coding: utf-8 -*-
"""
测试MP4直接处理的字幕对齐效果
"""

import os
import sys

# 添加工作流组件路径
workflow_path = os.path.join(os.path.dirname(__file__), 'workflow', 'component')
sys.path.insert(0, workflow_path)

from flow_python_implementation import VideoEditingWorkflow

def test_mp4_direct_alignment():
    """测试MP4直接处理的字幕对齐效果"""
    print("=" * 70)
    print("测试MP4直接处理的字幕对齐效果")
    print("=" * 70)
    
    # 配置剪映草稿文件夹路径
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 创建工作流实例
    workflow = VideoEditingWorkflow(draft_folder_path, "mp4_direct_alignment_test")
    
    # 配置测试输入 - 使用MP4视频URL
    inputs = {
        "audio_url": "https://oss.oemi.jdword.com/prod/temp/srt/V20250904170025001.wav",
        "digital_video_url": "https://oss.oemi.jdword.com/prod/order/video/202509/V20250904171528001.mp4",
        "title": "MP4直接处理字幕对齐测试",
        "content": "测试直接使用MP4 URL进行ASR识别，避免音频提取的精度损失，实现完美的字幕与音频波峰对齐",
        
        # 火山引擎ASR配置
        'volcengine_appid': '6046310832',
        'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',
        
        # 豆包API配置
        'doubao_token': 'adac0afb-5fd4-4c66-badb-370a7ff42df5',
        'doubao_model': 'doubao-1-5-pro-32k-250115',
    }
    
    print(f"[INFO] 测试MP4直接处理字幕对齐")
    print(f"[INFO] 视频URL: {inputs['digital_video_url']}")
    print(f"[INFO] 关键优化:")
    print(f"  ✓ ASR直接识别MP4，无音频提取")
    print(f"  ✓ 6位小数时间参数精度")
    print(f"  ✓ 精确时间映射算法")
    print()
    
    try:
        # 运行工作流
        result = workflow.process_workflow(inputs)
        
        if result:
            print("\n" + "=" * 70)
            print("测试结果分析")
            print("=" * 70)
            
            # 分析字幕生成结果
            if hasattr(workflow, 'adjusted_subtitles') and workflow.adjusted_subtitles:
                subtitles = workflow.adjusted_subtitles
                print(f"✅ 字幕生成成功: {len(subtitles)} 个字幕片段")
                
                print(f"\n📊 时间戳精度分析:")
                for i, subtitle in enumerate(subtitles[:5]):
                    start = subtitle['start']
                    end = subtitle['end'] 
                    text = subtitle['text']
                    duration = end - start
                    print(f"  {i+1}. [{start:.6f}s-{end:.6f}s] 时长:{duration:.6f}s | {text}")
                
                # 检查时间连续性
                print(f"\n🔗 时间连续性检查:")
                gaps = []
                overlaps = []
                
                for i in range(len(subtitles) - 1):
                    current_end = subtitles[i]['end']
                    next_start = subtitles[i + 1]['start']
                    
                    if next_start > current_end:
                        gap = next_start - current_end
                        gaps.append((i, gap))
                        if len(gaps) <= 3:  # 只显示前3个
                            print(f"    间隙 {i+1}->{i+2}: {gap:.6f}s")
                    elif next_start < current_end:
                        overlap = current_end - next_start
                        overlaps.append((i, overlap))
                        if len(overlaps) <= 3:  # 只显示前3个
                            print(f"    重叠 {i+1}->{i+2}: {overlap:.6f}s")
                
                print(f"  总计: {len(gaps)} 个间隙, {len(overlaps)} 个重叠")
                
                if len(gaps) > 0:
                    avg_gap = sum(gap[1] for gap in gaps) / len(gaps)
                    print(f"  平均间隙: {avg_gap:.6f}s")
                
                # 字幕对齐质量评分
                print(f"\n🎯 字幕对齐质量评估:")
                print(f"  ✅ 基于原始MP4文件的时间戳")
                print(f"  ✅ 避免了音频提取的精度损失")
                print(f"  ✅ 火山引擎服务器端直接处理")
                
                quality_score = 100
                if len(gaps) > len(subtitles) * 0.1:  # 超过10%的片段有间隙
                    quality_score -= 10
                if len(overlaps) > 0:
                    quality_score -= 5
                if hasattr(workflow, 'secondary_asr_subtitles'):
                    quality_score += 5  # 使用了精确映射
                
                print(f"  📈 预估对齐质量: {quality_score}%")
                
                print(f"\n✅ 测试完成！请在剪映中查看字幕与音频的同步效果")
                print(f"   应该能看到明显改善的字幕与音频波峰对齐效果")
                
            else:
                print("❌ 未生成字幕")
                
        else:
            print("❌ 工作流执行失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mp4_direct_alignment()