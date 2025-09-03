"""
视频模板基类和工厂模式实现

定义视频模板的抽象基类和工厂类，支持多种视频合成模板
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import os
import sys
import tempfile

# 添加本地 pyJianYingDraft 模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

import pyJianYingDraft as draft
from pyJianYingDraft import TrackType, trange, tim, TextShadow, IntroType, TransitionType
from .style_config import (
    VideoStyleConfig, CaptionStyleConfig, TitleStyleConfig,
    TextStyleConfig, HighlightStyleConfig, TextShadowConfig, TextBackgroundConfig,
    style_config_manager
)


class VideoTemplateBase(ABC):
    """视频模板抽象基类"""
    
    def __init__(self, draft_folder_path: str, project_name: str, style_config: VideoStyleConfig):
        """
        初始化模板
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            project_name: 项目名称
            style_config: 样式配置
        """
        self.draft_folder = draft.DraftFolder(draft_folder_path)
        self.project_name = project_name
        self.style_config = style_config
        self.script = None
        self.audio_duration = 0
        self.video_duration = 0
        self.project_duration = 0
        
        # 导入ASR模块
        try:
            from .volcengine_asr import VolcengineASR
            from .asr_silence_processor import ASRBasedSilenceRemover
            self.volcengine_asr = None
            self.silence_remover = None
        except ImportError:
            from volcengine_asr import VolcengineASR
            from asr_silence_processor import ASRBasedSilenceRemover
            self.volcengine_asr = None
            self.silence_remover = None
    
    def _update_project_duration(self):
        """更新项目总时长，取音视频中的最长者"""
        self.project_duration = max(self.audio_duration, self.video_duration)
        if self.project_duration > 0:
            print(f"📊 项目总时长更新为: {self.project_duration:.1f} 秒 (音频: {self.audio_duration:.1f}s, 视频: {self.video_duration:.1f}s)")
    
    def create_draft(self):
        """创建剪映草稿"""
        try:
            self.script = self.draft_folder.create_draft(
                self.project_name, 
                self.style_config.width, 
                self.style_config.height, 
                allow_replace=True
            )
        except Exception as e:
            # 回退到时间戳新名称
            from datetime import datetime
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fallback_name = f"{self.project_name}_{ts}"
            print(f"⚠️  创建草稿失败({e})，改用新项目名称: {fallback_name}")
            self.project_name = fallback_name
            self.script = self.draft_folder.create_draft(
                self.project_name, 
                self.style_config.width, 
                self.style_config.height, 
                allow_replace=False
            )
        
        # 添加基础轨道（通过调用顺序控制层级）
        self.script.add_track(TrackType.video, "主视频轨道", relative_index=1)
        self.script.add_track(TrackType.video, "数字人视频轨道", relative_index=2)  
        self.script.add_track(TrackType.audio, "音频轨道", relative_index=3)
        self.script.add_track(TrackType.audio, "背景音乐轨道", relative_index=4)
        self.script.add_track(TrackType.text, "内容字幕轨道", relative_index=5)
        self.script.add_track(TrackType.text, "标题字幕轨道", relative_index=6)
        
        return self.script
    
    def add_videos(self, video_urls: List[str], timelines: List[Dict[str, int]], 
                   volume: float = 1.0) -> List[draft.VideoSegment]:
        """添加视频片段"""
        if not self.script:
            raise ValueError("请先创建草稿")
        
        video_segments = []
        total_video_duration = 0
        
        for i, (video_url, timeline) in enumerate(zip(video_urls, timelines)):
            # 下载视频到本地
            local_video_path = self._download_material(video_url, f"temp_materials/video_{i}.mp4")
            
            # 计算时间范围
            start_time = timeline.get('start', 0)
            duration = timeline.get('end', 10) - start_time
            
            # 创建视频片段
            video_segment = draft.VideoSegment(
                local_video_path,
                trange(tim(f"{start_time}s"), tim(f"{duration}s"))
            )
            
            # 设置音量
            if hasattr(video_segment, 'set_volume'):
                video_segment.set_volume(volume)
            
            video_segments.append(video_segment)
            self.script.add_segment(video_segment, track_name="主视频轨道")
            
            # 累计视频时长
            total_video_duration += duration
        
        # 更新视频总时长
        self.video_duration = total_video_duration
        self._update_project_duration()
        print(f"📊 视频总时长: {self.video_duration:.1f} 秒")
        
        return video_segments
    
    def add_digital_human_video(self, digital_video_url: str, duration: int = None):
        """添加数字人视频"""
        if not self.script:
            raise ValueError("请先创建草稿")
        
        # 下载数字人视频
        local_path = self._download_material(digital_video_url, "temp_materials/digital_human.mp4")
        
        # 获取视频素材信息
        video_material = draft.VideoMaterial(local_path)
        
        # 计算持续时长
        if duration is None:
            duration_microseconds = video_material.duration
            duration_seconds = duration_microseconds / 1000000
        else:
            duration_microseconds = tim(f"{duration}s")
            duration_seconds = duration
        
        # 创建数字人视频片段
        digital_segment = draft.VideoSegment(
            video_material,
            trange(tim("0s"), duration_microseconds)
        )
        
        # 添加到数字人视频轨道
        self.script.add_segment(digital_segment, track_name="数字人视频轨道")
        
        # 更新视频时长
        self.video_duration = max(self.video_duration, duration_seconds)
        self._update_project_duration()
        print(f"📊 数字人视频时长: {duration_seconds:.1f} 秒")
        
        return digital_segment
    
    def add_audio(self, audio_url: str, duration: int = None, volume: float = None, remove_pauses: bool = False, 
                  min_pause_duration: float = 0.2, max_word_gap: float = 0.8):
        """添加音频
        
        Args:
            audio_url: 音频URL
            duration: 持续时长(秒)，如果为None则使用整个音频，如果有视频则限制为视频时长
            volume: 音量
            remove_pauses: 是否自动移除停顿，默认False
            min_pause_duration: 最小停顿时长(秒)，默认0.2秒
            max_word_gap: 单词间最大间隔(秒)，默认0.8秒
        """
        if not self.script:
            raise ValueError("请先创建草稿")
        
        # 使用配置中的音量
        if volume is None:
            volume = self.style_config.audio_volume
        
        # 下载音频
        local_path = self._download_material(audio_url, "temp_materials/audio.mp3")
        
        # 如果需要移除停顿，先处理音频
        if remove_pauses:
            processed_audio_path = self._remove_audio_pauses(
                local_path, min_pause_duration, max_word_gap
            )
            if processed_audio_path:
                local_path = processed_audio_path
        
        # 获取音频素材信息
        audio_material = draft.AudioMaterial(local_path)
        original_audio_duration = audio_material.duration / 1000000
        
        # 确定实际音频时长
        if duration is None:
            if self.video_duration > 0:
                actual_duration = min(original_audio_duration, self.video_duration)
                if original_audio_duration > self.video_duration:
                    print(f"⚠️  音频时长({original_audio_duration:.1f}s)超过视频时长({self.video_duration:.1f}s)，将截取至视频时长")
            else:
                actual_duration = original_audio_duration
        else:
            if self.video_duration > 0 and duration > self.video_duration:
                actual_duration = self.video_duration
                print(f"⚠️  指定音频时长({duration:.1f}s)超过视频时长({self.video_duration:.1f}s)，将截取至视频时长")
            else:
                actual_duration = duration
        
        duration_microseconds = tim(f"{actual_duration}s")
        self.audio_duration = actual_duration
        
        # 创建音频片段
        audio_segment = draft.AudioSegment(
            audio_material,
            trange(tim("0s"), duration_microseconds),
            volume=volume
        )
        
          
        # 添加到音频轨道
        self.script.add_segment(audio_segment, track_name="音频轨道")
        
        # 更新项目时长
        self._update_project_duration()
        print(f"📊 音频时长: {self.audio_duration:.1f} 秒")
        
        return audio_segment
    
    def add_background_music(self, music_path: str, target_duration: float = None, volume: float = None):
        """添加背景音乐"""
        if not self.script:
            raise ValueError("请先创建草稿")
        
        # 使用配置中的音量
        if volume is None:
            volume = self.style_config.background_music_volume
        
        if not os.path.exists(music_path):
            raise ValueError(f"背景音乐文件不存在: {music_path}")
        
        # 获取背景音乐素材信息
        bg_music_material = draft.AudioMaterial(music_path)
        
        # 确定目标时长
        if target_duration is None:
            if self.project_duration > 0:
                target_duration = self.project_duration
                print(f"🎵 背景音乐将使用项目总时长: {target_duration:.1f}s")
            elif self.video_duration > 0:
                target_duration = self.video_duration
                print(f"🎵 背景音乐将使用视频时长: {target_duration:.1f}s")
            elif self.audio_duration > 0:
                target_duration = self.audio_duration
                print(f"🎵 背景音乐将使用音频时长: {target_duration:.1f}s")
            else:
                raise ValueError("无法确定目标时长，请先添加音频或视频")
        
        target_duration_microseconds = tim(f"{target_duration}s")
        bg_music_duration_microseconds = bg_music_material.duration
        bg_music_duration_seconds = bg_music_duration_microseconds / 1000000
        
        if bg_music_duration_seconds >= target_duration:
            # 背景音乐够长，直接截取
            bg_music_segment = draft.AudioSegment(
                bg_music_material,
                trange(tim("0s"), target_duration_microseconds),
                volume=volume
            )
            # 添加淡入淡出已移除
            self.script.add_segment(bg_music_segment, track_name="背景音乐轨道")
            print(f"🎵 背景音乐已添加: {os.path.basename(music_path)}，截取时长: {target_duration:.1f}s")
        else:
            # 背景音乐太短，需要循环
            print(f"🎵 背景音乐时长 {bg_music_duration_seconds:.1f}s，目标时长 {target_duration:.1f}s，将循环播放")
            
            loop_count = int(target_duration / bg_music_duration_seconds) + 1
            current_time = 0
            
            for i in range(loop_count):
                remaining_time = target_duration - current_time
                if remaining_time <= 0:
                    break
                    
                current_duration = min(bg_music_duration_seconds, remaining_time)
                
                loop_segment = draft.AudioSegment(
                    bg_music_material,
                    trange(tim(f"{current_time}s"), tim(f"{current_duration}s")),
                    volume=volume
                )
                
                if i == 0:
                # 第一个片段淡入已移除
                if current_time + current_duration >= target_duration - 0.1:
                # 最后一个片段淡出已移除
                
                self.script.add_segment(loop_segment, track_name="背景音乐轨道")
                current_time += current_duration
            
            print(f"🎵 背景音乐循环已添加: {os.path.basename(music_path)}，{loop_count}次循环，总时长: {target_duration:.1f}s")
    
    def _download_material(self, url: str, local_path: str) -> str:
        """下载网络素材到本地"""
        if not url or url.startswith('file://') or os.path.exists(url):
            return url
        
        try:
            import requests
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
            return url
    
    @abstractmethod
    def add_captions(self, caption_data: List[Dict[str, Any]], keywords: List[str] = None):
        """添加字幕 - 子类必须实现"""
        pass
    
    @abstractmethod
    def add_title(self, title: str):
        """添加标题 - 子类必须实现"""
        pass
    
    def transcribe_audio_and_generate_subtitles(self, audio_url: str) -> List[Dict[str, Any]]:
        """音频转录生成字幕"""
        if not self.volcengine_asr:
            raise ValueError("ASR未初始化，请先配置火山引擎ASR")
        
        print(f"🎤 开始音频转录: {audio_url}")
        
        try:
            subtitle_objects = self.volcengine_asr.process_audio_file(audio_url)
            
            if subtitle_objects:
                print(f"✅ 转录完成，生成 {len(subtitle_objects)} 段字幕")
                return subtitle_objects
            else:
                print("❌ 转录失败")
                return []
                
        except Exception as e:
            print(f"❌ 音频转录失败: {e}")
            return []
    
    def process_workflow(self, inputs: Dict[str, Any]) -> str:
        """处理完整工作流"""
        print(f"🎬 开始处理视频模板: {self.project_name}")
        
        # 1. 初始化ASR
        volcengine_appid = inputs.get('volcengine_appid')
        volcengine_access_token = inputs.get('volcengine_access_token')
        doubao_token = inputs.get('doubao_token')
        doubao_model = inputs.get('doubao_model', 'doubao-1-5-pro-32k-250115')
        
        if volcengine_appid and volcengine_access_token:
            self.volcengine_asr = VolcengineASR(
                appid=volcengine_appid,
                access_token=volcengine_access_token,
                doubao_token=doubao_token,
                doubao_model=doubao_model
            )
            print(f"✅ ASR已初始化")
        else:
            raise ValueError("必须提供火山引擎ASR配置")
        
        # 2. 创建草稿
        self.create_draft()
        
        # 3. 添加数字人视频
        digital_video_url = inputs.get('digital_video_url')
        if digital_video_url:
            self.add_digital_human_video(digital_video_url)
        
        # 4. 添加素材视频
        material_video_url = inputs.get('material_video_url')
        if material_video_url:
            timelines = [{'start': 0, 'end': 10}]
            self.add_videos([material_video_url], timelines, volume=0.3)
        
        # 5. 添加音频
        audio_url = inputs.get('audio_url')
        if not audio_url:
            raise ValueError("audio_url 是必需参数")
        
        self.add_audio(audio_url, remove_pauses=True, min_pause_duration=0.2, max_word_gap=0.8)
        
        # 6. 添加背景音乐
        background_music_path = inputs.get('background_music_path')
        if background_music_path:
            bg_volume = inputs.get('background_music_volume', self.style_config.background_music_volume)
            self.add_background_music(background_music_path, volume=bg_volume)
        
        # 7. 音频转录生成字幕
        subtitle_objects = self.transcribe_audio_and_generate_subtitles(audio_url)
        
        if subtitle_objects:
            # 8. 提取关键词
            keywords = []
            if self.volcengine_asr:
                all_text = " ".join([sub['text'] for sub in subtitle_objects])
                keywords = self.volcengine_asr.extract_keywords_with_ai(all_text, max_keywords=8)
                print(f"🤖 提取到 {len(keywords)} 个关键词: {keywords}")
            
            # 9. 添加字幕
            self.add_captions(subtitle_objects, keywords)
            
            # 10. 添加标题
            title = inputs.get('title', '')
            if title:
                self.add_title(title)
        else:
            raise ValueError("音频转录失败")
        
        # 11. 保存草稿
        self.script.save()
        
        print(f"✅ 视频处理完成: {self.script.save_path}")
        return self.script.save_path
    
    def _remove_audio_pauses(self, audio_path: str, min_pause_duration: float = 0.8, 
                           max_word_gap: float = 1.5) -> Optional[str]:
        """
        移除音频中的停顿
        
        Args:
            audio_path: 音频文件路径
            min_pause_duration: 最小停顿时长(秒)
            max_word_gap: 单词间最大间隔(秒)
            
        Returns:
            Optional[str]: 处理后的音频文件路径，如果失败返回None
        """
        if not self.volcengine_asr:
            print("⚠️  ASR未初始化，跳过停顿移除")
            return None
        
        try:
            print("🔍 开始音频停顿检测和移除...")
            
            # 初始化停顿移除器
            if not self.silence_remover:
                self.silence_remover = ASRBasedSilenceRemover(min_pause_duration, max_word_gap)
            
            # 使用ASR转录音频
            asr_result = self.volcengine_asr.transcribe_audio_for_silence_detection(audio_path)
            
            if not asr_result:
                print("⚠️  ASR转录失败，跳过停顿移除")
                return None
            
            # 创建临时输出文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                output_path = temp_file.name
            
            # 移除停顿
            result = self.silence_remover.remove_pauses_from_audio(
                audio_path, asr_result, output_path
            )
            
            if result['success']:
                pause_stats = result['pause_statistics']
                print(f"✅ 停顿移除完成:")
                print(f"   - 移除停顿时长: {result['removed_duration']:.2f} 秒")
                print(f"   - 停顿次数: {pause_stats['pause_count']}")
                print(f"   - 平均停顿时长: {pause_stats['average_pause_duration']:.2f} 秒")
                print(f"   - 处理后音频时长: {result['processed_duration']:.2f} 秒")
                
                return output_path
            else:
                print("❌ 停顿移除失败")
                # 清理临时文件
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
                
        except Exception as e:
            print(f"❌ 停顿移除处理失败: {e}")
            return None


class VideoTemplateFactory:
    """视频模板工厂"""
    
    _templates = {}
    
    @classmethod
    def register_template(cls, name: str, template_class: type):
        """注册模板类"""
        cls._templates[name] = template_class
    
    @classmethod
    def create_template(cls, template_name: str, draft_folder_path: str, 
                       project_name: str, style_config: VideoStyleConfig = None) -> VideoTemplateBase:
        """创建模板实例"""
        if template_name not in cls._templates:
            raise ValueError(f"未知的模板类型: {template_name}")
        
        # 如果没有提供样式配置，使用默认配置
        if style_config is None:
            style_config = style_config_manager.get_config(template_name)
            if style_config is None:
                raise ValueError(f"未找到模板 '{template_name}' 的样式配置")
        
        return cls._templates[template_name](draft_folder_path, project_name, style_config)
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """列出所有可用模板"""
        return list(cls._templates.keys())
    
    @classmethod
    def get_template_info(cls, template_name: str) -> Dict[str, Any]:
        """获取模板信息"""
        if template_name not in cls._templates:
            return {}
        
        style_config = style_config_manager.get_config(template_name)
        if style_config:
            return style_config_manager.get_template_info(template_name)
        
        return {"name": template_name, "description": "自定义模板"}


# 使用示例和注册函数
def register_default_templates():
    """注册默认模板"""
    # 这里会在具体模板类实现后注册
    pass