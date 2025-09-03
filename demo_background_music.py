#!/usr/bin/env python3
"""
背景音乐功能演示
使用华尔兹.mp3作为背景音乐，展示如何为视频项目添加背景音乐
"""

import os
import sys

# 添加本地 pyJianYingDraft 模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import pyJianYingDraft as draft
from pyJianYingDraft import trange, tim

def create_demo_with_background_music():
    """创建一个包含背景音乐的演示项目"""
    
    # 配置草稿文件夹路径（请根据实际情况修改）
    draft_folder_path = r"<你的草稿文件夹>"  # 例如：C:\Users\YourName\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft
    
    print("🎵 背景音乐功能演示")
    print("=" * 50)
    
    try:
        # 1. 创建草稿文件夹管理器
        folder = draft.DraftFolder(draft_folder_path)
        script = folder.create_draft("背景音乐演示", 1920, 1080, allow_replace=True)
        
        # 2. 添加必要的轨道
        script.add_track(draft.TrackType.video, "主视频轨道")
        script.add_track(draft.TrackType.audio, "主音频轨道")
        script.add_track(draft.TrackType.audio, "背景音乐轨道")
        script.add_track(draft.TrackType.text, "字幕轨道")
        
        print("✅ 草稿和轨道创建完成")
        
        # 3. 添加示例视频（如果存在）
        video_path = os.path.join(current_dir, "readme_assets", "tutorial", "video.mp4")
        if os.path.exists(video_path):
            video_segment = draft.VideoSegment(
                video_path,
                trange("0s", "10s")  # 前10秒
            )
            script.add_segment(video_segment, "主视频轨道")
            print("✅ 示例视频已添加")
        else:
            print("⚠️  示例视频未找到，跳过视频添加")
        
        # 4. 添加示例音频（如果存在）
        audio_path = os.path.join(current_dir, "readme_assets", "tutorial", "audio.mp3")
        audio_duration = 10  # 默认10秒
        
        if os.path.exists(audio_path):
            audio_material = draft.AudioMaterial(audio_path)
            audio_duration = min(audio_material.duration / 1000000, 10)  # 最多10秒
            
            audio_segment = draft.AudioSegment(
                audio_material,
                trange("0s", f"{audio_duration}s"),
                volume=0.8
            )
            audio_segment.add_fade(tim("0.5s"), tim("0.5s"))
            script.add_segment(audio_segment, "主音频轨道")
            print(f"✅ 示例音频已添加（{audio_duration:.1f}秒）")
        else:
            print("⚠️  示例音频未找到，使用默认时长")
        
        # 5. 添加华尔兹背景音乐 🎵
        background_music_path = os.path.join(current_dir, "华尔兹.mp3")
        
        if os.path.exists(background_music_path):
            print(f"🎵 正在添加背景音乐: {background_music_path}")
            
            # 获取背景音乐素材信息
            bg_music_material = draft.AudioMaterial(background_music_path)
            bg_music_duration = bg_music_material.duration / 1000000  # 转换为秒
            
            print(f"📊 背景音乐信息:")
            print(f"   - 文件: 华尔兹.mp3")
            print(f"   - 时长: {bg_music_duration:.1f}秒")
            print(f"   - 目标时长: {audio_duration:.1f}秒")
            
            # 根据需要调整背景音乐
            if bg_music_duration >= audio_duration:
                # 背景音乐够长，直接截取
                bg_segment = draft.AudioSegment(
                    bg_music_material,
                    trange("0s", f"{audio_duration}s"),
                    volume=0.25  # 较小音量作为背景
                )
                bg_segment.add_fade(tim("1.0s"), tim("1.0s"))
                script.add_segment(bg_segment, "背景音乐轨道")
                print(f"✅ 背景音乐已添加（截取前{audio_duration:.1f}秒）")
            else:
                # 背景音乐太短，需要循环
                print(f"🔄 背景音乐时长不足，将循环播放")
                
                loop_count = int(audio_duration / bg_music_duration) + 1
                current_time = 0
                
                for i in range(loop_count):
                    remaining_time = audio_duration - current_time
                    if remaining_time <= 0:
                        break
                    
                    current_duration = min(bg_music_duration, remaining_time)
                    
                    loop_segment = draft.AudioSegment(
                        bg_music_material,
                        trange(f"{current_time}s", f"{current_duration}s"),
                        volume=0.25
                    )
                    
                    # 为第一个和最后一个片段添加淡入淡出
                    if i == 0:  # 第一个片段
                        loop_segment.add_fade(tim("1.0s"), tim("0s"))
                    if current_time + current_duration >= audio_duration - 0.1:  # 最后一个片段
                        loop_segment.add_fade(tim("0s"), tim("1.0s"))
                    
                    script.add_segment(loop_segment, "背景音乐轨道")
                    current_time += current_duration
                
                print(f"✅ 背景音乐循环播放已添加（{loop_count}次循环）")
        else:
            print(f"❌ 背景音乐文件未找到: {background_music_path}")
            print("   请确保华尔兹.mp3文件在项目根目录中")
            return
        
        # 6. 添加示例文本
        text_segment = draft.TextSegment(
            "🎵 背景音乐演示\n华尔兹音乐已添加",
            trange("0s", f"{audio_duration}s"),
            font=draft.FontType.文轩体,
            style=draft.TextStyle(
                size=12.0,
                color=(1.0, 1.0, 1.0),
                bold=True
            ),
            clip_settings=draft.ClipSettings(transform_y=-0.3),
            shadow=draft.TextShadow(
                alpha=0.8,
                color=(0.0, 0.0, 0.0),
                diffuse=20.0,
                distance=10.0
            )
        )
        script.add_segment(text_segment, "字幕轨道")
        print("✅ 演示文本已添加")
        
        # 7. 保存草稿
        script.save()
        print(f"\n🎉 背景音乐演示项目创建完成!")
        print(f"📁 项目位置: {script.save_path}")
        print("🎬 请在剪映中打开查看效果")
        print("\n📋 项目包含:")
        print("   - 主视频轨道（如果有示例视频）")
        print("   - 主音频轨道（如果有示例音频）")
        print("   - 背景音乐轨道（华尔兹.mp3，音量25%）")
        print("   - 字幕轨道（演示文本）")
        
    except Exception as e:
        print(f"❌ 创建演示项目失败: {e}")
        import traceback
        traceback.print_exc()


def show_background_music_usage():
    """展示背景音乐的使用方法"""
    print("\n" + "="*60)
    print("🎵 背景音乐使用方法")
    print("="*60)
    
    print("""
🔧 在flow_python_implementation.py中使用:

    # 创建工作流实例
    workflow = VideoEditingWorkflow(draft_folder_path, "项目名称")
    
    # 添加背景音乐（方法1：使用华尔兹.mp3）
    background_music_path = "华尔兹.mp3"
    workflow.add_background_music(background_music_path, volume=0.3)
    
    # 添加背景音乐（方法2：使用绝对路径）
    import os
    background_music_path = os.path.join(os.getcwd(), "华尔兹.mp3")
    workflow.add_background_music(background_music_path, volume=0.3)

🔧 在coze_complete_video_workflow.py中使用:

    # 创建工作流实例
    workflow = CozeVideoWorkflow(draft_folder_path)
    
    # 设置背景音乐（自动使用华尔兹.mp3）
    background_music_path = os.path.join(os.path.dirname(__file__), '..', '..', '华尔兹.mp3')
    workflow.set_background_music(background_music_path, volume=0.3)

🎛️ 参数说明:
    - music_path: 背景音乐文件路径
    - volume: 音量大小 (0.0-1.0)，推荐0.2-0.4用于背景
    - target_duration: 目标时长，默认使用主音频时长
    
✨ 特性:
    - ✅ 自动循环播放（如果音乐比目标时长短）
    - ✅ 自动截取（如果音乐比目标时长长）
    - ✅ 淡入淡出效果
    - ✅ 音量控制
    - ✅ 独立背景音乐轨道
""")


if __name__ == "__main__":
    print("🎵 pyJianYingDraft 背景音乐功能演示")
    print("=" * 50)
    
    # 检查华尔兹.mp3是否存在
    waltz_path = os.path.join(current_dir, "华尔兹.mp3")
    if os.path.exists(waltz_path):
        print(f"✅ 发现背景音乐文件: 华尔兹.mp3")
        
        choice = input("\n请选择操作:\n1. 创建背景音乐演示项目\n2. 查看使用方法\n请输入选择 (1/2): ").strip()
        
        if choice == "1":
            print("\n💡 请先修改脚本中的草稿文件夹路径，然后运行演示")
            print("   draft_folder_path = r\"你的剪映草稿文件夹路径\"")
            print("\n如果已配置，是否继续创建演示项目？(y/n): ", end="")
            confirm = input().strip().lower()
            if confirm == 'y':
                create_demo_with_background_music()
            else:
                print("已取消创建")
        elif choice == "2":
            show_background_music_usage()
        else:
            print("无效选择")
    else:
        print(f"❌ 未找到背景音乐文件: {waltz_path}")
        print("请确保华尔兹.mp3文件在项目根目录中")
        
    show_background_music_usage()
