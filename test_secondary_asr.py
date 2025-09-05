# -*- coding: utf-8 -*-
"""
测试二次ASR字幕生成功能
"""

import os
import sys

# 添加工作流组件路径
workflow_path = os.path.join(os.path.dirname(__file__), 'workflow', 'component')
sys.path.insert(0, workflow_path)

from flow_python_implementation import VideoEditingWorkflow

def test_secondary_asr():
    """测试二次ASR字幕生成功能"""
    print("=" * 60)
    print("测试二次ASR字幕生成功能")
    print("=" * 60)
    
    # 配置剪映草稿文件夹路径
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 创建工作流实例
    workflow = VideoEditingWorkflow(draft_folder_path, "secondary_asr_test")
    
    # 配置测试输入
    inputs = {
        # 使用你现有的测试音频和视频（确保触发停顿移除）
        "audio_url": "https://oss.oemi.jdword.com/prod/temp/srt/V20250904170025001.wav",
        "digital_video_url": "https://oss.oemi.jdword.com/prod/order/video/202509/V20250904171528001.mp4",
        "title": "二次ASR字幕测试",
        "content": "测试二次ASR字幕生成功能，确保字幕与音频波峰完美对齐",
        
        # 火山引擎ASR配置
        'volcengine_appid': '6046310832',
        'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',
        
        # 豆包API配置
        'doubao_token': 'adac0afb-5fd4-4c66-badb-370a7ff42df5',
        'doubao_model': 'doubao-1-5-pro-32k-250115',
    }
    
    print(f"[INFO] 开始测试二次ASR字幕生成功能")
    print(f"[INFO] 音频URL: {inputs['audio_url']}")
    print(f"[INFO] 启用停顿移除 + 二次ASR")
    
    try:
        # 运行工作流
        result = workflow.process_workflow(inputs)
        
        if result:
            print("\n" + "=" * 60)
            print("测试结果")
            print("=" * 60)
            
            # 显示字幕生成结果
            if hasattr(workflow, 'secondary_asr_subtitles') and workflow.secondary_asr_subtitles:
                print(f"✅ 二次ASR成功: 生成 {len(workflow.secondary_asr_subtitles)} 个字幕片段")
                print(f"📝 二次ASR字幕样例:")
                for i, sub in enumerate(workflow.secondary_asr_subtitles[:5]):  # 显示前5个
                    print(f"   {i+1}. [{sub['start']:.2f}s-{sub['end']:.2f}s] {sub['text']}")
                print()
                
            if hasattr(workflow, 'adjusted_subtitles') and workflow.adjusted_subtitles:
                print(f"📊 最终使用的字幕数量: {len(workflow.adjusted_subtitles)}")
                
                # 检查是否使用了二次ASR字幕
                if hasattr(workflow, 'secondary_asr_subtitles') and workflow.secondary_asr_subtitles:
                    if len(workflow.adjusted_subtitles) == len(workflow.secondary_asr_subtitles):
                        print("✅ 确认：最终使用了二次ASR生成的字幕")
                    else:
                        print("⚠️  注意：最终字幕与二次ASR字幕数量不匹配")
            
            print(f"✅ 测试完成！剪映项目已生成")
            
        else:
            print("❌ 工作流执行失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_secondary_asr()