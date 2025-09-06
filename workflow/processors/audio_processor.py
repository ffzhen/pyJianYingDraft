"""
音频处理器

负责音频相关的处理功能
"""

import os
import pyJianYingDraft as draft
from pyJianYingDraft import tim, trange
from typing import Optional
from ..core.base import BaseProcessor, WorkflowContext
from ..core.exceptions import ProcessingError

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