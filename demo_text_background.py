#!/usr/bin/env python3
"""
文本背景功能演示
展示如何为文字添加背景，特别是3个换行的文字示例
"""

import os
import sys

# 添加本地 pyJianYingDraft 模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import pyJianYingDraft as draft
from pyJianYingDraft import trange, tim
from workflow.component.flow_python_implementation import VideoEditingWorkflow

def create_text_background_demo():
    """创建文本背景演示项目"""
    
    # 配置草稿文件夹路径（请根据实际情况修改）
    draft_folder_path = r"<你的草稿文件夹>"  # 例如：C:\Users\YourName\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft
    
    print("🎨 文字背景功能演示")
    print("=" * 50)
    
    try:
        # 创建工作流实例
        workflow = VideoEditingWorkflow(draft_folder_path, "text_background_demo")
        workflow.create_draft()
        
        print("✅ 草稿创建完成")
        
        # 添加示例视频（如果存在）
        video_path = os.path.join(current_dir, "readme_assets", "tutorial", "video.mp4")
        if os.path.exists(video_path):
            workflow.add_digital_human_video(video_path, duration=10)
            print("✅ 示例视频已添加")
        
        # 示例1：3个换行的文字（使用您提供的背景参数）
        multiline_text = "第一行文字内容\n第二行文字内容\n第三行文字内容"
        
        # 使用您截图中的背景参数
        custom_background_style = {
            "color": "#000000",      # 黑色
            "alpha": 0.67,           # 67% 不透明度
            "height": 0.31,          # 31% 高度
            "width": 0.14,           # 14% 宽度  
            "horizontal_offset": 0.5, # 50% 左右间隙
            "vertical_offset": 0.5,   # 50% 上下间隙
            "round_radius": 0.0,     # 0% 圆角
            "style": 1               # 背景样式1
        }
        
        workflow.add_styled_text_with_background(
            text_content=multiline_text,
            timerange_start=0,
            timerange_duration=8,
            track_name="标题字幕轨道",
            position="center",
            background_style=custom_background_style
        )
        
        print("✅ 三行文字（黑色背景）已添加")
        
        # 示例2：不同样式的背景文字
        single_line_text = "单行标题文字"
        
        blue_background_style = {
            "color": "#0066CC",      # 蓝色
            "alpha": 0.8,            # 80% 不透明度
            "height": 0.2,           # 20% 高度
            "width": 0.1,            # 10% 宽度
            "horizontal_offset": 0.5, # 50% 左右间隙
            "vertical_offset": 0.5,   # 50% 上下间隙
            "round_radius": 0.2,     # 20% 圆角
            "style": 1
        }
        
        workflow.add_styled_text_with_background(
            text_content=single_line_text,
            timerange_start=8,
            timerange_duration=4,
            track_name="标题字幕轨道",
            position="top",
            background_style=blue_background_style
        )
        
        print("✅ 单行文字（蓝色背景）已添加")
        
        # 示例3：底部字幕样式
        subtitle_text = "这是底部字幕\n带有半透明背景\n便于阅读"
        
        subtitle_background_style = {
            "color": "#333333",      # 深灰色
            "alpha": 0.75,           # 75% 不透明度
            "height": 0.25,          # 25% 高度
            "width": 0.12,           # 12% 宽度
            "horizontal_offset": 0.5, # 50% 左右间隙
            "vertical_offset": 0.5,   # 50% 上下间隙
            "round_radius": 0.1,     # 10% 圆角
            "style": 1
        }
        
        workflow.add_styled_text_with_background(
            text_content=subtitle_text,
            timerange_start=2,
            timerange_duration=6,
            track_name="内容字幕轨道",
            position="bottom",
            background_style=subtitle_background_style
        )
        
        print("✅ 底部字幕（深灰背景）已添加")
        
        # 保存草稿
        workflow.script.save()
        
        print(f"\n🎉 文字背景演示项目创建完成!")
        print(f"📁 项目位置: {workflow.script.save_path}")
        print("🎬 请在剪映中打开查看效果")
        print("\n📋 项目包含:")
        print("   - 🎬 数字人视频（如果有示例视频）")
        print("   - 📝 三行文字（黑色背景，居中）")
        print("   - 📝 单行标题（蓝色背景，顶部）")
        print("   - 📝 底部字幕（深灰背景，底部）")
        print("\n🎨 背景参数示例:")
        print("   - 颜色：黑色 (#000000)")
        print("   - 不透明度：67%")
        print("   - 高度：31%, 宽度：14%")
        print("   - 上下左右间隙：50%")
        
    except Exception as e:
        print(f"❌ 创建演示项目失败: {e}")
        import traceback
        traceback.print_exc()


def show_text_background_usage():
    """展示文本背景的使用方法"""
    print("\n" + "="*60)
    print("🎨 文字背景使用方法")
    print("="*60)
    
    print("""
🔧 基础用法:

    from workflow.component.flow_python_implementation import VideoEditingWorkflow
    
    workflow = VideoEditingWorkflow(draft_folder_path, "项目名")
    workflow.create_draft()
    
    # 添加3个换行的文字（使用您的背景参数）
    multiline_text = "第一行文字\\n第二行文字\\n第三行文字"
    
    background_style = {
        "color": "#000000",      # 颜色：黑色
        "alpha": 0.67,           # 不透明度：67%
        "height": 0.31,          # 高度：31%
        "width": 0.14,           # 宽度：14%
        "horizontal_offset": 0.5, # 左右间隙：50%
        "vertical_offset": 0.5,   # 上下间隙：50%
        "round_radius": 0.0,     # 圆角：0%
        "style": 1               # 背景样式
    }
    
    workflow.add_styled_text_with_background(
        text_content=multiline_text,
        timerange_start=0,       # 开始时间（秒）
        timerange_duration=10,   # 持续时间（秒）
        track_name="标题字幕轨道",
        position="center",       # 位置：center/top/bottom
        background_style=background_style
    )

🎛️ 背景参数说明:
    - color: 背景颜色（#RRGGBB格式）
    - alpha: 不透明度（0.0-1.0）
    - height: 背景高度比例（0.0-1.0）
    - width: 背景宽度比例（0.0-1.0）
    - horizontal_offset: 水平间隙（0.0-1.0，0.5为居中）
    - vertical_offset: 垂直间隙（0.0-1.0，0.5为居中）
    - round_radius: 圆角半径（0.0-1.0）
    - style: 背景样式（1或2）

📍 位置选项:
    - "top": 顶部显示
    - "center": 中间显示
    - "bottom": 底部显示

✨ 特性:
    - ✅ 支持多行文字（使用\\n换行）
    - ✅ 自定义背景颜色和透明度
    - ✅ 可调节背景尺寸和位置
    - ✅ 自动添加阴影效果
    - ✅ 支持自动换行
    - ✅ 字体样式可自定义
""")


if __name__ == "__main__":
    print("🎨 pyJianYingDraft 文字背景功能演示")
    print("=" * 50)
    
    choice = input("\n请选择操作:\n1. 创建文字背景演示项目\n2. 查看使用方法\n请输入选择 (1/2): ").strip()
    
    if choice == "1":
        print("\n💡 请先修改脚本中的草稿文件夹路径，然后运行演示")
        print("   draft_folder_path = r\"你的剪映草稿文件夹路径\"")
        print("\n如果已配置，是否继续创建演示项目？(y/n): ", end="")
        confirm = input().strip().lower()
        if confirm == 'y':
            create_text_background_demo()
        else:
            print("已取消创建")
    elif choice == "2":
        show_text_background_usage()
    else:
        print("无效选择")
        
    show_text_background_usage()
