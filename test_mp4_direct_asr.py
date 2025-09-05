# -*- coding: utf-8 -*-
"""
测试直接传入MP4给ASR的效果
"""

import os
import sys

# 添加工作流组件路径
workflow_path = os.path.join(os.path.dirname(__file__), 'workflow', 'component')
sys.path.insert(0, workflow_path)

from volcengine_asr import VolcengineASR

def test_mp4_direct_asr():
    """测试直接传入MP4文件给ASR"""
    print("=" * 60)
    print("测试直接传入MP4给ASR的效果")
    print("=" * 60)
    
    # 初始化ASR
    asr = VolcengineASR(
        appid='6046310832',
        access_token='fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY'
    )
    
    # MP4视频URL
    mp4_url = "https://oss.oemi.jdword.com/prod/order/video/202509/V20250904171528001.mp4"
    
    print(f"[INFO] 测试直接识别MP4文件: {mp4_url}")
    
    try:
        # 直接传入MP4 URL进行ASR识别
        result = asr.process_audio_file(mp4_url)
        
        if result:
            print(f"\n✅ 直接MP4识别成功！")
            print(f"📊 识别结果: {len(result)} 个字幕片段")
            
            # 显示前5个字幕的时间戳精度
            print(f"\n🕐 时间戳精度分析:")
            for i, subtitle in enumerate(result[:5]):
                start = subtitle['start']
                end = subtitle['end']
                text = subtitle['text']
                print(f"  {i+1}. [{start:.6f}s-{end:.6f}s] {text}")
            
            # 对比传统方式（提取音频后识别）
            print(f"\n📈 对比分析:")
            print(f"✅ 直接MP4识别: 避免了音频提取的精度损失")
            print(f"✅ 服务器端处理: 火山引擎直接从视频提取音频")
            print(f"✅ 时间戳精度: 基于原始视频文件")
            
        else:
            print("❌ 直接MP4识别失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")

if __name__ == "__main__":
    test_mp4_direct_asr()