"""
基于flow.json的Python实现 - 简化版（只使用火山引擎ASR）
使用pyJianYingDraft包重新实现视频编辑工作流逻辑
"""

import os
import json
import sys

# 添加本地 pyJianYingDraft 模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

import pyJianYingDraft as draft
from pyJianYingDraft import TrackType, trange, tim, TextShadow, IntroType, TransitionType
from typing import List, Dict, Any, Optional, Tuple
import requests
from urllib.parse import urlparse
import re
import math

# 火山引擎ASR - 唯一字幕识别方案
try:
    from .volcengine_asr import VolcengineASR
except ImportError:
    # 当直接运行此文件时，使用绝对导入
    from volcengine_asr import VolcengineASR


class VideoEditingWorkflow:
    """视频编辑工作流类，基于flow.json的逻辑实现"""
    
    def __init__(self, draft_folder_path: str, project_name: str = "flow_project"):
        """初始化工作流
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            project_name: 项目名称
        """
        self.draft_folder = draft.DraftFolder(draft_folder_path)
        self.project_name = project_name
        self.script = None
        self.audio_duration = 0  # 音频总时长（秒）
        self.volcengine_asr = None  # 火山引擎ASR客户端
        
    def download_material(self, url: str, local_path: str) -> str:
        """下载网络素材到本地
        
        Args:
            url: 素材URL
            local_path: 本地保存路径
            
        Returns:
            本地文件路径
        """
        if not url or url.startswith('file://') or os.path.exists(url):
            return url
            
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return local_path
        except Exception as e:
            print(f"下载素材失败: {url}, 错误: {e}")
            return url  # 返回原URL，让用户处理
    
    def create_draft(self, width: int = 1080, height: int = 1920, fps: int = 30):
        """创建剪映草稿
        
        Args:
            width: 视频宽度
            height: 视频高度  
            fps: 帧率
        """
        self.script = self.draft_folder.create_draft(
            self.project_name, width, height, allow_replace=True
        )
        
        # 添加基础轨道
        self.script.add_track(TrackType.video, "主视频轨道")      # 主视频轨道
        self.script.add_track(TrackType.video, "数字人视频轨道")   # 数字人视频轨道  
        self.script.add_track(TrackType.audio, "音频轨道")        # 音频轨道
        self.script.add_track(TrackType.text, "标题字幕轨道")     # 标题字幕轨道
        self.script.add_track(TrackType.text, "内容字幕轨道")     # 内容字幕轨道
        
        return self.script
    
    def add_videos(self, video_urls: List[str], timelines: List[Dict[str, int]], 
                   volume: float = 1.0, track_index: int = 0) -> List[draft.VideoSegment]:
        """批量添加视频
        
        Args:
            video_urls: 视频URL列表
            timelines: 时间轴信息列表，包含start和end(单位：秒)
            volume: 音量(0-1)
            track_index: 轨道索引
            
        Returns:
            视频片段列表
        """
        if not self.script:
            raise ValueError("请先创建草稿")
            
        video_segments = []
        
        for i, (video_url, timeline) in enumerate(zip(video_urls, timelines)):
            # 下载视频到本地
            local_video_path = self.download_material(
                video_url, 
                f"temp_materials/video_{i}.mp4"
            )
            
            # 计算时间范围
            start_time = timeline.get('start', 0)  # 秒
            duration = timeline.get('end', 10) - start_time  # 持续时长
            
            # 创建视频片段
            video_segment = draft.VideoSegment(
                local_video_path,
                trange(tim(f"{start_time}s"), tim(f"{duration}s"))
            )
            
            # 设置音量
            if hasattr(video_segment, 'set_volume'):
                video_segment.set_volume(volume)
            
            video_segments.append(video_segment)
            
            # 添加到主视频轨道
            self.script.add_segment(video_segment, track_name="主视频轨道")
            
        return video_segments
    
    def add_digital_human_video(self, digital_video_url: str, duration: int = None):
        """添加数字人视频
        
        Args:
            digital_video_url: 数字人视频URL
            duration: 持续时长(秒)，如果不指定则使用整个视频
        """
        if not self.script:
            raise ValueError("请先创建草稿")
            
        # 下载数字人视频
        local_path = self.download_material(
            digital_video_url,
            "temp_materials/digital_human.mp4"
        )
        
        # 获取视频素材信息
        video_material = draft.VideoMaterial(local_path)
        
        # 如果没有指定持续时长，使用整个视频
        if duration is None:
            duration_microseconds = video_material.duration
        else:
            duration_microseconds = tim(f"{duration}s")
        
        # 创建数字人视频片段
        digital_segment = draft.VideoSegment(
            video_material,
            trange(tim("0s"), duration_microseconds)
        )
        
        # 添加到数字人视频轨道
        self.script.add_segment(digital_segment, track_name="数字人视频轨道")
        
        return digital_segment
    
    def add_audio(self, audio_url: str, duration: int = None, volume: float = 1.0):
        """添加音频
        
        Args:
            audio_url: 音频URL
            duration: 持续时长(秒)
            volume: 音量(0-1)
        """
        if not self.script:
            raise ValueError("请先创建草稿")
            
        # 下载音频
        local_path = self.download_material(
            audio_url,
            "temp_materials/audio.mp3"
        )
        
        # 获取音频素材信息
        audio_material = draft.AudioMaterial(local_path)
        
        # 如果没有指定持续时长，使用整个音频
        if duration is None:
            duration_microseconds = audio_material.duration
            # 保存音频时长（转换为秒）
            self.audio_duration = duration_microseconds / 1000000
        else:
            duration_microseconds = tim(f"{duration}s")
            self.audio_duration = duration
        
        # 创建音频片段
        audio_segment = draft.AudioSegment(
            audio_material,
            trange(tim("0s"), duration_microseconds),
            volume=volume
        )
        
        # 添加淡入淡出
        audio_segment.add_fade(tim("0.5s"), tim("0.5s"))
        
        # 添加到音频轨道
        self.script.add_segment(audio_segment, track_name="音频轨道")
        
        return audio_segment
    
    def transcribe_audio_and_generate_subtitles(self, audio_url: str) -> List[Dict[str, Any]]:
        """使用火山引擎ASR进行音频转录生成字幕
        
        Args:
            audio_url: 音频URL（本地路径或网络URL）
            
        Returns:
            字幕对象数组 [{'text': str, 'start': float, 'end': float}, ...]
        """
        
        print(f"🎤 开始音频转录: {audio_url}")
        print(f"🔥 使用火山引擎ASR进行转录")
        
        try:
            if not self.volcengine_asr:
                print("❌ 火山引擎ASR未初始化，无法进行转录")
                return []
            
            # 使用火山引擎ASR进行转录
            subtitle_objects = self.volcengine_asr.process_audio_file(audio_url)
            
            if subtitle_objects:
                print(f"✅ 火山引擎转录完成，生成 {len(subtitle_objects)} 段字幕")
                
                # 显示最终的句子和时间戳
                print(f"\n📋 火山引擎ASR转录结果:")
                print("-" * 60)
                
                total_duration = 0
                for i, subtitle in enumerate(subtitle_objects, 1):
                    start = subtitle['start']
                    end = subtitle['end']
                    text = subtitle['text']
                    duration = end - start
                    total_duration += duration
                    
                    print(f"{i:2d}. [{start:7.3f}s-{end:7.3f}s] ({duration:5.2f}s) {text}")
                
                # 提取转录的完整文本
                transcribed_text = " ".join([sub['text'] for sub in subtitle_objects])
                print(f"\n📝 完整转录文本: {transcribed_text}")
                print(f"📊 统计: {len(subtitle_objects)}段, 总时长{total_duration:.1f}秒, 平均{total_duration/len(subtitle_objects):.1f}秒/段")
                
                return subtitle_objects
            else:
                print("❌ 火山引擎转录失败")
                return []
                
        except Exception as e:
            print(f"❌ 音频转录过程中出错: {e}")
            return []
    
    def adjust_subtitle_timing(self, subtitle_objects: List[Dict[str, Any]],
                             delay_seconds: float = 0.0, 
                             speed_factor: float = 1.0) -> List[Dict[str, Any]]:
        """调整字幕时间 - 添加延迟和调整语速
        
        Args:
            subtitle_objects: 字幕对象列表
            delay_seconds: 延迟时间（秒），正值表示字幕延后，负值表示字幕提前
            speed_factor: 速度系数，>1表示加快，<1表示减慢
            
        Returns:
            调整后的字幕对象列表
        """
        if not subtitle_objects:
            return []
        
        print(f"⏰ 调整字幕时间: 延迟={delay_seconds:.1f}s, 速度系数={speed_factor:.2f}")
        
        adjusted_subtitles = []
        
        for i, subtitle in enumerate(subtitle_objects):
            # 应用速度系数
            original_start = subtitle['start']
            original_end = subtitle['end']
            original_duration = original_end - original_start
            
            # 调整时间
            new_start = original_start / speed_factor + delay_seconds
            new_duration = original_duration / speed_factor
            new_end = new_start + new_duration
            
            # 确保时间不为负
            new_start = max(0, new_start)
            new_end = max(new_start + 0.5, new_end)  # 最少0.5秒显示时间
            
            adjusted_subtitle = {
                'text': subtitle['text'],
                'start': new_start,
                'end': new_end
            }
            adjusted_subtitles.append(adjusted_subtitle)
            
            print(f"   第{i+1}段: {original_start:.1f}s-{original_end:.1f}s → {new_start:.1f}s-{new_end:.1f}s")
        
        print(f"✅ 字幕时间调整完成")
        return adjusted_subtitles
    

    
    def add_captions(self, caption_data: List[Dict[str, Any]], font_size: float = 12.0, 
                    track_name: str = "内容字幕轨道", position: str = "bottom",
                    keywords: List[str] = None, keyword_color: Tuple[float, float, float] = None):
        """添加字幕，支持关键词高亮
        
        Args:
            caption_data: 字幕数据列表，每个元素包含text, start, end等信息
            font_size: 字体大小
            track_name: 轨道名称
            position: 字幕位置 ("top"顶部, "bottom"底部)
            keywords: 需要高亮的关键词列表
            keyword_color: 关键词高亮颜色，默认为黄色
        """
        if not self.script:
            raise ValueError("请先创建草稿")
            
        text_segments = []
        
        # 设置默认关键词高亮颜色
        if keyword_color is None:
            keyword_color = (1.0, 0.984313725490196, 0.7254901960784313)  # 黄色高亮
        
        for caption in caption_data:
            text = caption.get('text', '')
            start_time = caption.get('start', 0)  # 秒
            end_time = caption.get('end', start_time + 2)  # 秒
            
            if not text:
                continue
                
            # 根据位置设置不同的垂直位置
            if position == "top":
                transform_y = 0.4  # 顶部位置
                text_color = (1.0, 1.0, 0.0)  # 标题用黄色
            else:
                transform_y = -0.4  # 底部位置
                text_color = (1.0, 1.0, 1.0)  # 内容用白色
                
            # 过滤出在当前文本中实际存在的关键词
            current_keywords = []
            if keywords:
                for keyword in keywords:
                    if keyword and keyword.strip() and keyword in text:
                        current_keywords.append(keyword)
                        
            # 创建文本片段，只传入当前文本中存在的关键词
            text_segment = draft.TextSegment(
                text,
                trange(tim(f"{start_time}s"), tim(f"{end_time - start_time}s")),
                font=draft.FontType.宋体,
                style=draft.TextStyle(
                    color=text_color,
                    size=font_size,
                    bold=True
                ),
                clip_settings=draft.ClipSettings(transform_y=transform_y),
                shadow=draft.TextShadow(
                    alpha=0.8,
                    color=(0.0, 0.0, 0.0),  # 黑色阴影
                    diffuse=20.0,
                    distance=10.0,
                    angle=-45.0
                ),
                keywords=current_keywords if current_keywords else None,  # 只传入当前文本存在的关键词
                keyword_color=keyword_color  # 传入关键词颜色
            )
            
            # 如果有关键词被高亮，打印调试信息
            if current_keywords:
                print(f"   🎯 '{text}' 中高亮关键词: {current_keywords}")
            
            text_segments.append(text_segment)
            self.script.add_segment(text_segment, track_name=track_name)
            
        return text_segments
    
    def add_transitions_and_effects(self, video_segments: List[draft.VideoSegment]):
        """为视频片段添加转场和特效
        
        Args:
            video_segments: 视频片段列表
        """
        for i, segment in enumerate(video_segments):
            # 为每个片段添加入场动画
            if i < len(video_segments) - 1:  # 除最后一个片段外都添加转场
                segment.add_transition(TransitionType.淡化)
                
            # 添加入场动画
            segment.add_animation(IntroType.淡入)
    
    def process_workflow(self, inputs: Dict[str, Any]) -> str:
        """处理完整的工作流 - 专注音频转录生成字幕
        
        Args:
            inputs: 输入参数，包含：
                - digital_video_url: 数字人视频URL
                - material_video_url: 素材视频URL (可选)
                - audio_url: 音频URL (必需，用于转录)
                - title: 视频标题 (可选)
                - volcengine_appid: 火山引擎AppID (必需)
                - volcengine_access_token: 火山引擎访问令牌 (必需)
                - subtitle_delay: 字幕延迟（秒），正值延后，负值提前 (默认0)
                - subtitle_speed: 字幕速度系数，>1加快，<1减慢 (默认1.0)
                
        Returns:
            草稿保存路径
        """
        # 0. 获取配置参数
        # 火山引擎ASR配置（用于语音识别）
        volcengine_appid = inputs.get('volcengine_appid')
        volcengine_access_token = inputs.get('volcengine_access_token')
        
        # 豆包API配置（用于关键词提取）
        doubao_token = inputs.get('doubao_token')
        doubao_model = inputs.get('doubao_model', 'doubao-1-5-pro-32k-250115')
        
        # 其他参数
        audio_url = inputs.get('audio_url')
        subtitle_delay = inputs.get('subtitle_delay', 0.0)  # 字幕延迟
        subtitle_speed = inputs.get('subtitle_speed', 1.0)  # 字幕速度系数
        
        # 验证必需参数
        if not audio_url:
            raise ValueError("audio_url 是必需参数，用于音频转录")
        
        print(f"🎤 音频转录字幕工作流 + AI关键词高亮")
        print(f"📥 音频URL: {audio_url}")
        print(f"⏰ 字幕延迟: {subtitle_delay:.1f}秒")
        print(f"🚀 字幕速度: {subtitle_speed:.1f}x")
        print(f"🔥 火山引擎ASR (语音识别)")
        print(f"🤖 豆包API (关键词提取): {'已配置' if doubao_token else '未配置，将使用本地算法'}")
        
        # 初始化火山引擎ASR
        if volcengine_appid and volcengine_access_token:
            self.volcengine_asr = VolcengineASR(
                appid=volcengine_appid, 
                access_token=volcengine_access_token,
                doubao_token=doubao_token,
                doubao_model=doubao_model
            )
            print(f"✅ 火山引擎ASR已初始化 (AppID: {volcengine_appid})")
            if doubao_token:
                print(f"✅ 豆包API已配置 (Model: {doubao_model})")
        else:
            raise ValueError("必须提供 volcengine_appid 和 volcengine_access_token 参数")
        
        # 1. 创建草稿
        self.create_draft()
        
        # 2. 添加数字人视频
        digital_video_url = inputs.get('digital_video_url')
        if digital_video_url:
            self.add_digital_human_video(digital_video_url)
        
        # 3. 添加素材视频（如果有）
        material_video_url = inputs.get('material_video_url')
        if material_video_url:
            # 模拟时间轴数据
            timelines = [{'start': 0, 'end': 10}]  # 可以根据实际需求调整
            self.add_videos([material_video_url], timelines, volume=0.3)
        
        # 4. 添加音频
        self.add_audio(audio_url, volume=0.8)
        print(f"📊 音频时长: {self.audio_duration:.1f} 秒")
        
        # 5. 生成音频转录字幕
        title = inputs.get('title', '')
        
        # 音频转录生成字幕
        print("🎤 开始音频转录生成字幕")
        subtitle_objects = self.transcribe_audio_and_generate_subtitles(audio_url)
        print(f"🔍 音频转录字幕: {subtitle_objects}")
        
        if subtitle_objects:
            print(f"✅ 音频转录成功，生成 {len(subtitle_objects)} 段字幕")
            
            # 🔥 使用火山引擎ASR结果，直接使用
            print(f"🚀 使用火山引擎ASR结果")
            final_subtitles = subtitle_objects
            
            # 只在需要时应用时间调整
            if subtitle_delay != 0.0 or subtitle_speed != 1.0:
                print(f"⏰ 应用时间调整: 延迟{subtitle_delay:.1f}s, 速度{subtitle_speed:.1f}x")
                final_subtitles = self.adjust_subtitle_timing(final_subtitles, subtitle_delay, subtitle_speed)
            
            # 🤖 使用AI提取关键词用于高亮
            print("\n🤖 开始AI关键词提取...")
            all_text = " ".join([sub['text'] for sub in final_subtitles])
            keywords = self.volcengine_asr.extract_keywords_with_ai(all_text, max_keywords=8)
            
            if keywords:
                print(f"✅ AI提取到 {len(keywords)} 个关键词: {keywords}")
                keyword_color = (1.0, 0.984313725490196, 0.7254901960784313)  # 黄色高亮
            else:
                print("⚠️ 未提取到关键词，使用普通字幕")
                keyword_color = None
            
            # 添加字幕到视频项目（带关键词高亮）
            self.add_captions(final_subtitles, track_name="内容字幕轨道", position="bottom",
                            keywords=keywords, keyword_color=keyword_color)
            
            # 显示字幕添加结果
            print(f"\n📋 已添加 {len(final_subtitles)} 段字幕到剪映项目")
            print("前3段预览:")
            for i, subtitle in enumerate(final_subtitles[:3], 1):
                start = subtitle['start']
                end = subtitle['end']
                text = subtitle['text']
                print(f"   {i}. [{start:.3f}s-{end:.3f}s] {text}")
            
            # 添加标题字幕（如果有） - 全程显示在顶部
            if title:
                title_caption = [{
                    'text': title,
                    'start': 0,
                    'end': self.audio_duration  # 使用实际音频时长
                }]
                print(f"📋 添加标题字幕: {title} (0s - {self.audio_duration:.1f}s)")
                self.add_captions(title_caption, font_size=16.0, track_name="标题字幕轨道", position="top")
        else:
            print("❌ 音频转录失败，无法生成字幕")
            raise ValueError("音频转录失败，请检查音频文件和API配置")
        
        # 6. 保存草稿
        self.script.save()
        
        return self.script.save_path


def main():
    """主函数 - 音频转录智能字幕工作流"""
    # 配置剪映草稿文件夹路径（需要根据实际情况修改）
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    print("🎤 音频转录智能字幕工作流 + AI关键词高亮")
    print("=" * 60)
    print("自动转录音频并生成智能字幕，使用AI识别关键词进行高亮显示")
    
    # 创建工作流实例
    workflow = VideoEditingWorkflow(draft_folder_path, "audio_transcription_demo")
    
    # 配置输入参数
    inputs = {
        'digital_video_url': 'https://oss.oemi.jdword.com/prod/order/video/202509/V20250901153106001.mp4',
        'audio_url': 'https://oss.oemi.jdword.com/prod/temp/srt/V20250901152556001.wav',
        'title': '火山引擎ASR智能字幕演示',
        
        # 🔥 火山引擎ASR配置（用于语音识别）
        'volcengine_appid': '6046310832',                # 火山引擎ASR AppID
        'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',  # 火山引擎ASR AccessToken
        
        # 🤖 豆包API配置（用于关键词提取）
        'doubao_token': 'adac0afb-5fd4-4c66-badb-370a7ff42df5',  # 请替换为您的豆包API token
        'doubao_model': 'doubao-1-5-pro-32k-250115',  # 豆包模型名称
    }
    
    try:
        print(f"\n🎬 开始处理工作流...")
        save_path = workflow.process_workflow(inputs)
        print(f"\n✅ 音频转录工作流完成!")
        print(f"📁 剪映项目已保存到: {save_path}")
        print("🎬 请打开剪映查看生成的智能字幕视频项目")
        
    except Exception as e:
        print(f"❌ 工作流失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()