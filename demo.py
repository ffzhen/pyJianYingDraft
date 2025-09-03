"""
pyJianYingDraft 演示程序 - 包含背景音乐功能
创建包含音视频素材、文本和华尔兹背景音乐的剪映草稿文件
"""

import os
import pyJianYingDraft as draft
from pyJianYingDraft import trange, tim

def main():
    # 草稿文件夹路径（请根据实际情况修改）
    draft_folder_path = r"<你的草稿文件夹>"  # 例如：C:\Users\YourName\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft
    
    print("🎬 pyJianYingDraft 演示程序（含背景音乐）")
    print("=" * 50)
    
    try:
        # 创建草稿文件夹管理器
        folder = draft.DraftFolder(draft_folder_path)
        script = folder.create_draft("demo", 1920, 1080, allow_replace=True)
        
        # 添加轨道
        script.add_track(draft.TrackType.video, "主视频")
        script.add_track(draft.TrackType.audio, "主音频")
        script.add_track(draft.TrackType.audio, "背景音乐")  # 🎵 背景音乐轨道
        script.add_track(draft.TrackType.text, "文本")
        
        print("✅ 草稿和轨道创建完成")
        
        # 检查并添加示例素材
        current_dir = os.path.dirname(os.path.abspath(__file__))
        tutorial_dir = os.path.join(current_dir, 'readme_assets', 'tutorial')
        
        # 添加视频
        video_path = os.path.join(tutorial_dir, 'video.mp4')
        if os.path.exists(video_path):
            video_segment = draft.VideoSegment(video_path, trange("0s", "5s"))
            # 添加入场动画
            video_segment.add_animation(draft.IntroType.淡入)
            script.add_segment(video_segment, "主视频")
            print("✅ 视频片段已添加（含入场动画）")
        else:
            print("⚠️  示例视频未找到，跳过视频添加")
        
        # 添加音频
        audio_path = os.path.join(tutorial_dir, 'audio.mp3')
        audio_duration = 5.0  # 默认5秒
        
        if os.path.exists(audio_path):
            audio_material = draft.AudioMaterial(audio_path)
            actual_duration = min(audio_material.duration / 1000000, 5.0)
            audio_duration = actual_duration
            
            audio_segment = draft.AudioSegment(
                audio_material, 
                trange("0s", f"{actual_duration}s"),
                volume=0.8
            )
            # 添加音频淡入淡出
            audio_segment.add_fade(tim("0.5s"), tim("0.5s"))
            script.add_segment(audio_segment, "主音频")
            print(f"✅ 音频片段已添加（{actual_duration:.1f}秒，含淡入淡出）")
        else:
            print("⚠️  示例音频未找到，使用默认时长")
        
        # 🎵 添加华尔兹背景音乐（智能音视频时长同步）
        background_music_path = os.path.join(current_dir, "华尔兹.mp3")
        if os.path.exists(background_music_path):
            print("🎵 正在添加华尔兹背景音乐...")
            
            # 确定项目时长：取音频和视频中的最长者
            video_duration = 5.0 if os.path.exists(video_path) else 0.0  # 视频时长
            project_duration = max(audio_duration, video_duration)
            
            print(f"📊 项目时长同步: 音频{audio_duration:.1f}s, 视频{video_duration:.1f}s, 使用{project_duration:.1f}s")
            
            bg_music_material = draft.AudioMaterial(background_music_path)
            bg_music_duration = bg_music_material.duration / 1000000
            
            if bg_music_duration >= project_duration:
                # 背景音乐够长，直接截取
                bg_segment = draft.AudioSegment(
                    bg_music_material,
                    trange("0s", f"{project_duration}s"),
                    volume=0.25  # 背景音乐音量较小
                )
                bg_segment.add_fade(tim("1.0s"), tim("1.0s"))
                script.add_segment(bg_segment, "背景音乐")
                print(f"✅ 华尔兹背景音乐已添加（{project_duration:.1f}秒，与项目时长同步）")
            else:
                # 背景音乐太短，循环播放
                print(f"🔄 华尔兹背景音乐较短（{bg_music_duration:.1f}s），将循环播放至{project_duration:.1f}s")
                loop_count = int(project_duration / bg_music_duration) + 1
                current_time = 0
                
                for i in range(loop_count):
                    remaining_time = project_duration - current_time
                    if remaining_time <= 0:
                        break
                    
                    current_duration = min(bg_music_duration, remaining_time)
                    
                    loop_segment = draft.AudioSegment(
                        bg_music_material,
                        trange(f"{current_time}s", f"{current_duration}s"),
                        volume=0.25
                    )
                    
                    # 首尾添加淡入淡出
                    if i == 0:
                        loop_segment.add_fade(tim("0.5s"), tim("0s"))
                    if current_time + current_duration >= project_duration - 0.1:
                        loop_segment.add_fade(tim("0s"), tim("0.5s"))
                    
                    script.add_segment(loop_segment, "背景音乐")
                    current_time += current_duration
                
                print(f"✅ 华尔兹背景音乐循环已添加（{loop_count}次，总时长{project_duration:.1f}s）")
        else:
            print(f"❌ 华尔兹背景音乐未找到: {background_music_path}")
            print("💡 请确保华尔兹.mp3文件在项目根目录中")
        
        # 添加文本片段（使用项目时长确保与音视频同步）
        text_duration = max(audio_duration, video_duration if os.path.exists(video_path) else 0.0)
        text_segment = draft.TextSegment(
            "🎵 华尔兹背景音乐演示\n音视频时长已同步",
            trange("1s", f"{text_duration-1}s"),
            font=draft.FontType.文轩体,
            style=draft.TextStyle(
                size=16.0,
                color=(1.0, 1.0, 1.0),
                bold=True
            ),
            clip_settings=draft.ClipSettings(transform_y=-0.3)
        )
        
        # 添加文本气泡效果（如果支持）
        try:
            # 这里可以添加气泡效果，具体实现取决于pyJianYingDraft的版本
            pass
        except:
            pass
        
        script.add_segment(text_segment, "文本")
        print("✅ 文本片段已添加")
        
        # 添加转场效果（如果有多个片段）
        if os.path.exists(video_path):
            try:
                # 为视频添加转场
                script.add_transition(draft.TransitionType.淡化, trange("4.5s", "1s"))
                print("✅ 转场效果已添加")
            except:
                print("⚠️  转场效果添加失败")
        
        # 保存草稿
        script.save()
        
        print(f"\n🎉 演示项目创建成功!")
        print(f"📁 项目位置: {script.save_path}")
        print("🎬 请在剪映中打开查看效果")
        print("\n📋 项目包含:")
        print("   - 🎬 主视频轨道（含入场动画）")
        print("   - 🎤 主音频轨道（含淡入淡出）")
        print("   - 🎵 华尔兹背景音乐轨道（音量25%，智能同步时长）")
        print("   - 📝 文本轨道（与项目时长同步）")
        print("   - ✨ 转场效果")
        print("   - 🔄 音视频时长自动同步，避免黑屏问题")
        
    except Exception as e:
        print(f"❌ 创建演示项目失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 请检查:")
        print("   1. 草稿文件夹路径是否正确")
        print("   2. 华尔兹.mp3文件是否在项目根目录")
        print("   3. readme_assets/tutorial/目录下是否有示例素材")


if __name__ == "__main__":
    # 检查华尔兹.mp3文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    waltz_path = os.path.join(current_dir, "华尔兹.mp3")
    
    if os.path.exists(waltz_path):
        print("✅ 发现华尔兹.mp3文件")
    else:
        print("❌ 未找到华尔兹.mp3文件")
        print("请确保华尔兹.mp3文件在项目根目录中")
    
    print("\n💡 使用前请修改 draft_folder_path 为您的剪映草稿文件夹路径")
    print("   例如: C:\\Users\\YourName\\AppData\\Local\\JianyingPro\\User Data\\Projects\\com.lveditor.draft")
    
    main()
