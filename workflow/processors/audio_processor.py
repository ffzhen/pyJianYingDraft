"""
音频处理器

负责音频相关的处理功能，包括ASR转录
"""

import os
import pyJianYingDraft as draft
from pyJianYingDraft import tim, trange
from typing import Optional, List, Dict, Any
from ..core.base import BaseProcessor, WorkflowContext
from ..core.exceptions import ProcessingError

# 导入ASR相关模块
try:
    from ..component.volcengine_asr import VolcengineASR
    from ..component.asr_silence_processor import ASRBasedSilenceRemover, ASRSilenceDetector
except ImportError:
    # 尝试从当前目录导入
    try:
        import sys
        from pathlib import Path
        current_dir = Path(__file__).parent.parent
        sys.path.append(str(current_dir / 'component'))
        from volcengine_asr import VolcengineASR
        from asr_silence_processor import ASRBasedSilenceRemover, ASRSilenceDetector
    except ImportError as e:
        print(f"Warning: ASR modules not available: {e}")
        VolcengineASR = None
        ASRBasedSilenceRemover = None
        ASRSilenceDetector = None

class AudioProcessor(BaseProcessor):
    """音频处理器"""
    
    def process(self, *args, **kwargs):
        """占位方法"""
        pass
        
    def add_audio(self, audio_url: str, duration: Optional[int] = None, volume: float = 1.0):
        """添加音频
        
        Args:
            audio_url: 音频URL
            duration: 持续时长(秒)，如果为None则使用整个音频
            volume: 音量(0-1)
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
        
        # 下载音频到本地（这里需要依赖MaterialManager）
        from ..managers.material_manager import MaterialManager
        material_manager = MaterialManager(self.context, self.logger)
        
        audio_local_path = material_manager.generate_unique_filename("audio", ".mp3")
        local_path = material_manager.download_material(audio_url, audio_local_path)
        
        # 处理本地路径
        if local_path != audio_url:
            if not os.path.isabs(local_path):
                local_path = os.path.abspath(local_path)
            
            if os.path.exists(local_path):
                self._log("debug", f"本地音频文件大小: {os.path.getsize(local_path)} bytes")
            else:
                raise ProcessingError(f"音频文件不存在: {local_path}")
        
        self._log("debug", f"最终音频路径: {local_path}")
        
        # 获取音频素材信息
        audio_material = draft.AudioMaterial(local_path)
        actual_audio_duration = audio_material.duration / 1000000  # 转换为秒
        
        self._log("debug", f"实际音频时长: {actual_audio_duration:.2f} 秒")
        
        # 确定实际音频时长
        if duration is None:
            # 如果有视频，音频时长不应超过视频时长
            if self.context.video_duration > 0:
                actual_duration = min(actual_audio_duration, self.context.video_duration)
                if actual_audio_duration > self.context.video_duration:
                    self._log("warning", f"音频时长({actual_audio_duration:.2f}s)超过视频时长({self.context.video_duration:.2f}s)，将截取至视频时长")
            else:
                actual_duration = actual_audio_duration
        else:
            # 如果有视频，检查指定时长是否超过视频时长
            if self.context.video_duration > 0 and duration > self.context.video_duration:
                actual_duration = self.context.video_duration
                self._log("warning", f"指定音频时长({duration:.2f}s)超过视频时长({self.context.video_duration:.2f}s)，将截取至视频时长")
            else:
                actual_duration = duration
        
        duration_microseconds = tim(f"{actual_duration:.6f}s")
        self.context.audio_duration = round(actual_duration, 2)
        
        # 创建音频片段
        audio_segment = draft.AudioSegment(
            audio_material,
            trange(tim("0s"), duration_microseconds),
            volume=volume
        )
        
        # 清除现有音频段以避免重叠
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.clear_track_segments("音频轨道")
        
        # 添加到音频轨道
        self.context.script.add_segment(audio_segment, track_name="音频轨道")
        
        # 更新项目时长
        from ..managers.duration_manager import DurationManager
        duration_manager = DurationManager(self.context, self.logger)
        duration_manager.update_project_duration()
        
        self._log("info", f"音频时长: {self.context.audio_duration:.2f} 秒")
        
        return audio_segment
        
    def add_background_music(self, music_path: str, target_duration: Optional[float] = None, volume: float = 0.3):
        """添加背景音乐
        
        Args:
            music_path: 背景音乐文件路径（本地路径）
            target_duration: 目标时长（秒），如果None则使用项目总时长
            volume: 音量(0-1)，默认0.3比较适合背景音乐
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        if not os.path.exists(music_path):
            raise ProcessingError(f"背景音乐文件不存在: {music_path}")
        
        # 获取背景音乐素材信息
        bg_music_material = draft.AudioMaterial(music_path)
        
        # 确定目标时长
        if target_duration is None:
            effective_duration = self.context.get_effective_video_duration()
            if effective_duration > 0:
                target_duration = round(effective_duration, 2)
                self._log("info", f"背景音乐将使用有效视频时长: {target_duration:.2f}s")
            elif self.context.video_duration > 0:
                target_duration = round(self.context.video_duration, 2)
                self._log("info", f"背景音乐将使用视频时长: {target_duration:.2f}s")
            elif self.context.audio_duration > 0:
                target_duration = round(self.context.audio_duration, 2)
                self._log("info", f"背景音乐将使用音频时长: {target_duration:.2f}s")
            else:
                raise ProcessingError("无法确定目标时长，请先添加音频或视频，或指定target_duration")
        else:
            # 验证用户指定的目标时长
            from ..managers.duration_manager import DurationManager
            duration_manager = DurationManager(self.context, self.logger)
            target_duration = duration_manager.validate_duration_bounds(target_duration, "背景音乐")
        
        target_duration_microseconds = tim(f"{target_duration:.6f}s")
        bg_music_duration_microseconds = bg_music_material.duration
        
        # 计算是否需要循环播放
        bg_music_duration_seconds = bg_music_duration_microseconds / 1000000
        
        if bg_music_duration_seconds >= target_duration:
            # 背景音乐够长，直接截取
            bg_music_segment = draft.AudioSegment(
                bg_music_material,
                trange(tim("0s"), target_duration_microseconds),
                volume=volume
            )
            self.context.script.add_segment(bg_music_segment, track_name="背景音乐轨道")
            self._log("info", f"背景音乐已添加: {os.path.basename(music_path)}，截取时长: {target_duration:.2f}s，音量: {volume}")
        else:
            # 背景音乐太短，需要循环
            self._log("info", f"背景音乐时长 {bg_music_duration_seconds:.2f}s，目标时长 {target_duration:.2f}s，将循环播放")
            
            # 计算需要循环的次数
            loop_count = int(target_duration / bg_music_duration_seconds) + 1
            current_time = 0
            
            for i in range(loop_count):
                # 计算当前循环的持续时间
                remaining_time = target_duration - current_time
                if remaining_time <= 0:
                    break
                    
                current_duration = min(bg_music_duration_seconds, remaining_time)
                
                # 创建当前循环的音频片段
                loop_segment = draft.AudioSegment(
                    bg_music_material,
                    trange(tim(f"{current_time:.6f}s"), tim(f"{current_duration:.6f}s")),
                    volume=volume
                )
                
                # 添加到背景音乐轨道
                self.context.script.add_segment(loop_segment, track_name="背景音乐轨道")
                
                current_time += current_duration
            
            self._log("info", f"背景音乐循环已添加: {os.path.basename(music_path)}，{loop_count}次循环，总时长: {target_duration:.2f}s，音量: {volume}")
        
        return
    
    def initialize_asr(self, volcengine_appid: str = None, volcengine_access_token: str = None,
                       doubao_token: str = None, doubao_model: str = "doubao-1-5-pro-32k-250115"):
        """初始化火山引擎ASR
        
        Args:
            volcengine_appid: 火山引擎ASR AppID
            volcengine_access_token: 火山引擎ASR AccessToken
            doubao_token: 豆包API Token（用于关键词提取）
            doubao_model: 豆包模型名称
        """
        if not VolcengineASR:
            raise ProcessingError("ASR模块不可用，请检查导入")
            
        if volcengine_appid and volcengine_access_token:
            self.volcengine_asr = VolcengineASR(
                appid=volcengine_appid,
                access_token=volcengine_access_token,
                doubao_token=doubao_token,
                doubao_model=doubao_model
            )
            self._log("info", f"火山引擎ASR已初始化 (AppID: {volcengine_appid})")
            if doubao_token:
                self._log("info", f"豆包API已配置 (Model: {doubao_model})")
        else:
            raise ProcessingError("必须提供 volcengine_appid 和 volcengine_access_token 参数")
    
    def transcribe_audio(self, audio_url: str) -> List[Dict[str, Any]]:
        """使用火山引擎ASR进行音频转录
        
        Args:
            audio_url: 音频URL（本地路径或网络URL）
            
        Returns:
            字幕对象数组 [{'text': str, 'start': float, 'end': float}, ...]
        """
        if not hasattr(self, 'volcengine_asr') or not self.volcengine_asr:
            raise ProcessingError("火山引擎ASR未初始化，请先调用initialize_asr")
        
        self._log("info", f"开始音频转录: {audio_url}")
        
        try:
            # 使用火山引擎ASR进行转录
            subtitle_objects = self.volcengine_asr.process_audio_file(audio_url)
            
            if subtitle_objects:
                self._log("info", f"火山引擎转录完成，生成 {len(subtitle_objects)} 段字幕")
                
                # 记录转录结果摘要
                total_duration = 0
                for subtitle in subtitle_objects:
                    duration = subtitle['end'] - subtitle['start']
                    total_duration += duration
                
                self._log("info", f"转录统计: {len(subtitle_objects)}段, 总时长{total_duration:.1f}秒")
                return subtitle_objects
            else:
                self._log("error", "火山引擎转录失败")
                return []
                
        except Exception as e:
            self._log("error", f"音频转录过程中出错: {e}")
            raise ProcessingError(f"音频转录失败: {e}")
    
    def extract_keywords(self, text: str) -> List[str]:
        """使用AI提取关键词
        
        Args:
            text: 需要分析的文本
            
        Returns:
            关键词列表
        """
        if not hasattr(self, 'volcengine_asr') or not self.volcengine_asr:
            raise ProcessingError("火山引擎ASR未初始化，请先调用initialize_asr")
        
        try:
            keywords = self.volcengine_asr.extract_keywords_with_ai(text)
            if keywords:
                self._log("info", f"AI提取到 {len(keywords)} 个关键词: {keywords}")
            else:
                self._log("warning", "未提取到关键词")
            return keywords or []
        except Exception as e:
            self._log("error", f"关键词提取失败: {e}")
            return []
    
    def remove_audio_pauses(self, audio_url: str, min_pause_duration: float = 0.2,
                           max_word_gap: float = 0.8) -> Optional[str]:
        """移除音频中的停顿
        
        Args:
            audio_url: 原始音频URL
            min_pause_duration: 最小停顿时长(秒)
            max_word_gap: 单词间最大间隔(秒)
            
        Returns:
            处理后的音频文件路径，如果失败返回None
        """
        if not hasattr(self, 'volcengine_asr') or not self.volcengine_asr:
            self._log("warning", "ASR未初始化，跳过停顿移除")
            return None
        
        if not ASRBasedSilenceRemover or not ASRSilenceDetector:
            self._log("warning", "停顿处理模块不可用，跳过停顿移除")
            return None
        
        try:
            self._log("info", "开始音频停顿检测和移除...")
            
            # 使用ASR转录音频
            asr_result = self.volcengine_asr.transcribe_audio_for_silence_detection(audio_url)
            
            if not asr_result:
                self._log("warning", "ASR转录失败，跳过停顿移除")
                return None
            
            # 检测停顿
            pause_detector = ASRSilenceDetector(min_pause_duration, max_word_gap)
            pause_segments = pause_detector.detect_pauses_from_asr(asr_result)
            
            if not pause_segments:
                self._log("info", "未检测到需要移除的停顿")
                return None
            
            # 下载音频到本地进行处理
            from ..managers.material_manager import MaterialManager
            material_manager = MaterialManager(self.context, self.logger)
            
            audio_local_path = material_manager.generate_unique_filename("audio", ".mp3")
            local_path = material_manager.download_material(audio_url, audio_local_path)
            
            # 移除停顿
            silence_remover = ASRBasedSilenceRemover(min_pause_duration, max_word_gap)
            
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                output_path = temp_file.name
            
            result = silence_remover.remove_pauses_from_audio(
                local_path, asr_result, output_path
            )
            
            if result['success']:
                pause_stats = result['pause_statistics']
                self._log("info", f"停顿移除完成:")
                self._log("info", f"   - 移除停顿时长: {result['removed_duration']:.2f} 秒")
                self._log("info", f"   - 停顿次数: {pause_stats['pause_count']}")
                self._log("info", f"   - 处理后音频时长: {result['processed_duration']:.2f} 秒")
                
                return output_path
            else:
                self._log("error", "停顿移除失败")
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
                
        except Exception as e:
            self._log("error", f"停顿移除处理失败: {e}")
            return None