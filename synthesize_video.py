#!/usr/bin/env python3
"""
单独执行视频合成任务
使用已获得的Coze工作流数据进行视频合成
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from workflow.examples.coze_complete_video_workflow import CozeVideoWorkflow


def synthesize_video_from_coze_data(coze_data: dict, output_title: str = None):
    """从Coze数据合成视频
    
    Args:
        coze_data: Coze工作流返回的数据
        output_title: 输出视频标题（可选）
        
    Returns:
        视频文件路径或None
    """
    print("🎬 开始视频合成")
    print("=" * 50)
    
    try:
        # 创建工作流实例
        workflow = CozeVideoWorkflow("draft_output")
        
        # 设置豆包API
        workflow.set_doubao_api(
            token='adac0afb-5fd4-4c66-badb-370a7ff42df5',
            model='ep-m-20250902010446-mlwmf'
        )
        
        # 设置背景音乐
        background_music_path = "华尔兹.mp3"
        if os.path.exists(background_music_path):
            workflow.set_background_music(background_music_path, volume=0.3)
            print(f"✅ 背景音乐已设置: {background_music_path}")
        else:
            print("⚠️  背景音乐文件未找到，跳过背景音乐")
        
        # 设置任务配置（避免task_config错误）
        workflow.task_config = {
            "content": coze_data.get("content", ""),
            "title": output_title or coze_data.get("title", "合成视频"),
            "audio_url": coze_data.get("audioUrl", ""),
            "video_url": coze_data.get("videoUrl", "")
        }
        
        print(f"📋 任务标题: {workflow.task_config['title']}")
        print(f"🎵 音频URL: {coze_data.get('audioUrl', '')}")
        print(f"🎬 视频URL: {coze_data.get('videoUrl', '')}")
        
        # 直接调用视频合成方法
        result = workflow.synthesize_video(coze_data)
        
        if result:
            print(f"\n✅ 视频合成成功!")
            print(f"📁 输出路径: {result}")
            return result
        else:
            print(f"\n❌ 视频合成失败")
            return None
            
    except Exception as e:
        print(f"\n❌ 视频合成异常: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    # Coze工作流返回的数据
    coze_data = {
        "audioUrl": "https://oss.oemi.jdword.com/prod/temp/srt/V20250904170025001.wav",
        "content": "中国以后还会有大规模拆迁吗？答案是：会。\n从二零二五年开始，国家将把拆迁改造范围从三十个城市扩大到三百个，全面推进城中村和老旧小区更新，并重新提倡货币化安置——也就是直接发放现金补偿。\n这意味着，一批拆迁户将获得数百万元甚至上千万元的补偿款，确实有可能成为千万富翁。但关键在于钱怎么用：用于改善住房或稳健配置，财富才能留存；若盲目消费或投机，也可能一夜暴富、转眼归零。\n与过去不同，这一轮改造有两个重要变化：\n一是多拆少建。当前全国房产库存偏高，拆旧不等于大建，而是严控新增供应。\n二是拆小建大。拆除的主要是老破小，新建的则是大面积、改善型、舒适型住宅，推动居住品质升级。\n目前小户型库存充足，能满足刚需，政策重心已转向支持改善型需求。\n这一轮不是简单拆迁，而是通过城市更新优化住房结构、激活内需、带动经济。\n面对这笔补偿款，理性规划比一时致富更重要。\n理解政策方向，才能真正把握时代红利。",
        "recordId": "",
        "tableId": "",
        "title": "拆迁暴富后能否守住财富",
        "videoUrl": "https://oss.oemi.jdword.com/prod/order/video/202509/V20250904171528001.mp4"
    }
    
    # 自定义输出标题
    output_title = "中国还会大规模拆迁吗？"
    
    print("🎯 单独视频合成任务")
    print(f"📝 原始标题: {coze_data['title']}")
    print(f"📝 输出标题: {output_title}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行视频合成
    result = synthesize_video_from_coze_data(coze_data, output_title)
    
    if result:
        print(f"\n🎉 任务完成!")
        print(f"📁 最终视频文件: {result}")
        
        # 检查文件是否存在
        if os.path.exists(result):
            file_size = os.path.getsize(result)
            print(f"📊 文件大小: {file_size / (1024*1024):.2f} MB")
        else:
            print("⚠️  警告: 输出文件不存在")
    else:
        print(f"\n💔 任务失败")
    
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()