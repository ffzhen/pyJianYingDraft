"""
视频处理器

负责视频相关的处理功能
"""

import os
import pyJianYingDraft as draft
from pyJianYingDraft import tim, trange
from typing import Optional, List, Dict, Any
from ..core.base import BaseProcessor, WorkflowContext
from ..core.exceptions import ProcessingError

class VideoProcessor(BaseProcessor):
    """视频处理器"""
    
    def process(self, *args, **kwargs):
        """占位方法"""
        pass
        
    def add_video(self, video_url: str, duration: Optional[float] = None, start_time: float = 0.0):
        """添加主视频
        
        Args:
            video_url: 视频URL或本地路径
            duration: 持续时长(秒)，如果为None则使用整个视频
            start_time: 开始时间(秒)
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
        
        # 下载视频到本地（依赖MaterialManager）
        from ..managers.material_manager import MaterialManager
        material_manager = MaterialManager(self.context, self.logger)
        
        video_local_path = material_manager.generate_unique_filename("video", ".mp4")
        local_path = material_manager.download_material(video_url, video_local_path)
        
        # 处理本地路径
        if local_path != video_url:
            if not os.path.isabs(local_path):
                local_path = os.path.abspath(local_path)
            
            if os.path.exists(local_path):
                self._log("debug", f"本地视频文件大小: {os.path.getsize(local_path)} bytes")
            else:
                raise ProcessingError(f"视频文件不存在: {local_path}")
        
        self._log("debug", f"最终视频路径: {local_path}")
        
        # 获取视频素材信息
        video_material = draft.VideoMaterial(local_path)
        actual_video_duration = video_material.duration / 1000000  # 转换为秒
        
        self._log("debug", f"实际视频时长: {actual_video_duration:.2f} 秒")
        
        # 确定实际视频时长
        if duration is None:
            actual_duration = actual_video_duration - start_time
        else:
            available_duration = actual_video_duration - start_time
            if duration > available_duration:
                actual_duration = available_duration
                self._log("warning", f"指定视频时长({duration:.2f}s)超过可用时长({available_duration:.2f}s)，将截取至可用时长")
            else:
                actual_duration = duration
        
        # 验证时长边界
        from ..managers.duration_manager import DurationManager
        duration_manager = DurationManager(self.context, self.logger)
        actual_duration = duration_manager.validate_duration_bounds(actual_duration, "视频")
        
        start_time_microseconds = tim(f"{start_time:.6f}s")
        duration_microseconds = tim(f"{actual_duration:.6f}s")
        self.context.video_duration = round(actual_duration, 2)
        
        # 创建视频片段
        video_segment = draft.VideoSegment(
            video_material,
            trange(start_time_microseconds, duration_microseconds)
        )
        
        # 清除现有视频段以避免重叠
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.clear_track_segments("主视频轨道")
        
        # 添加到主视频轨道
        self.context.script.add_segment(video_segment, track_name="主视频轨道")
        
        # 更新项目时长
        duration_manager.update_project_duration()
        
        self._log("info", f"主视频已添加: {os.path.basename(local_path)}，时长: {self.context.video_duration:.2f} 秒")
        
        return video_segment
        
    def add_digital_human_video(self, digital_human_url: str, target_duration: Optional[float] = None):
        """添加数字人视频
        
        Args:
            digital_human_url: 数字人视频URL或本地路径
            target_duration: 目标时长（秒），如果None则使用项目总时长
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        # 下载数字人视频到本地
        from ..managers.material_manager import MaterialManager
        material_manager = MaterialManager(self.context, self.logger)
        
        digital_human_local_path = material_manager.generate_unique_filename("digital_human", ".mp4")
        local_path = material_manager.download_material(digital_human_url, digital_human_local_path)
        
        if local_path != digital_human_url and not os.path.exists(local_path):
            raise ProcessingError(f"数字人视频文件不存在: {local_path}")
        
        # 获取数字人视频素材信息
        digital_human_material = draft.VideoMaterial(local_path)
        
        # 确定目标时长
        if target_duration is None:
            effective_duration = self.context.get_effective_video_duration()
            if effective_duration > 0:
                target_duration = round(effective_duration, 2)
                self._log("info", f"数字人视频将使用有效视频时长: {target_duration:.2f}s")
            elif self.context.video_duration > 0:
                target_duration = round(self.context.video_duration, 2)
                self._log("info", f"数字人视频将使用主视频时长: {target_duration:.2f}s")
            elif self.context.audio_duration > 0:
                target_duration = round(self.context.audio_duration, 2)
                self._log("info", f"数字人视频将使用音频时长: {target_duration:.2f}s")
            else:
                raise ProcessingError("无法确定目标时长，请先添加音频或视频，或指定target_duration")
        else:
            # 验证用户指定的目标时长
            from ..managers.duration_manager import DurationManager
            duration_manager = DurationManager(self.context, self.logger)
            target_duration = duration_manager.validate_duration_bounds(target_duration, "数字人视频")
        
        target_duration_microseconds = tim(f"{target_duration:.6f}s")
        digital_human_duration_microseconds = digital_human_material.duration
        
        # 计算是否需要循环播放
        digital_human_duration_seconds = digital_human_duration_microseconds / 1000000
        
        # 清除现有数字人视频段
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.clear_track_segments("数字人视频轨道")
        
        if digital_human_duration_seconds >= target_duration:
            # 数字人视频够长，直接截取
            digital_human_segment = draft.VideoSegment(
                digital_human_material,
                trange(tim("0s"), target_duration_microseconds)
            )
            self.context.script.add_segment(digital_human_segment, track_name="数字人视频轨道")
            self._log("info", f"数字人视频已添加: {os.path.basename(local_path)}，截取时长: {target_duration:.2f}s")
        else:
            # 数字人视频太短，需要循环
            self._log("info", f"数字人视频时长 {digital_human_duration_seconds:.2f}s，目标时长 {target_duration:.2f}s，将循环播放")
            
            # 计算需要循环的次数
            loop_count = int(target_duration / digital_human_duration_seconds) + 1
            current_time = 0
            
            for i in range(loop_count):
                # 计算当前循环的持续时间
                remaining_time = target_duration - current_time
                if remaining_time <= 0:
                    break
                    
                current_duration = min(digital_human_duration_seconds, remaining_time)
                
                # 创建当前循环的视频片段
                loop_segment = draft.VideoSegment(
                    digital_human_material,
                    trange(tim(f"{current_time:.6f}s"), tim(f"{current_duration:.6f}s"))
                )
                
                # 添加到数字人视频轨道
                self.context.script.add_segment(loop_segment, track_name="数字人视频轨道")
                
                current_time += current_duration
            
            self._log("info", f"数字人视频循环已添加: {os.path.basename(local_path)}，{loop_count}次循环，总时长: {target_duration:.2f}s")
        
        return
        
    def add_background_video(self, background_video_url: str, target_duration: Optional[float] = None):
        """添加背景视频（作为视频背景层）
        
        Args:
            background_video_url: 背景视频URL或本地路径
            target_duration: 目标时长（秒），如果None则使用项目总时长
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        # 确保背景视频轨道存在
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.ensure_track_exists(draft.TrackType.video, "背景视频轨道")
        
        # 下载背景视频到本地
        from ..managers.material_manager import MaterialManager
        material_manager = MaterialManager(self.context, self.logger)
        
        bg_video_local_path = material_manager.generate_unique_filename("background_video", ".mp4")
        local_path = material_manager.download_material(background_video_url, bg_video_local_path)
        
        if local_path != background_video_url and not os.path.exists(local_path):
            raise ProcessingError(f"背景视频文件不存在: {local_path}")
        
        # 获取背景视频素材信息
        bg_video_material = draft.VideoMaterial(local_path)
        
        # 确定目标时长（类似数字人视频的逻辑）
        if target_duration is None:
            effective_duration = self.context.get_effective_video_duration()
            if effective_duration > 0:
                target_duration = round(effective_duration, 2)
            elif self.context.video_duration > 0:
                target_duration = round(self.context.video_duration, 2)
            elif self.context.audio_duration > 0:
                target_duration = round(self.context.audio_duration, 2)
            else:
                raise ProcessingError("无法确定目标时长，请先添加音频或视频，或指定target_duration")
        
        # 验证时长边界
        from ..managers.duration_manager import DurationManager
        duration_manager = DurationManager(self.context, self.logger)
        target_duration = duration_manager.validate_duration_bounds(target_duration, "背景视频")
        
        # 添加背景视频（实现类似背景音乐的循环逻辑）
        target_duration_microseconds = tim(f"{target_duration:.6f}s")
        bg_video_duration_microseconds = bg_video_material.duration
        bg_video_duration_seconds = bg_video_duration_microseconds / 1000000
        
        # 清除现有背景视频段
        track_manager.clear_track_segments("背景视频轨道")
        
        if bg_video_duration_seconds >= target_duration:
            # 背景视频够长，直接截取
            bg_video_segment = draft.VideoSegment(
                bg_video_material,
                trange(tim("0s"), target_duration_microseconds)
            )
            self.context.script.add_segment(bg_video_segment, track_name="背景视频轨道")
            self._log("info", f"背景视频已添加: {os.path.basename(local_path)}，截取时长: {target_duration:.2f}s")
        else:
            # 背景视频太短，需要循环
            self._log("info", f"背景视频时长 {bg_video_duration_seconds:.2f}s，目标时长 {target_duration:.2f}s，将循环播放")
            
            loop_count = int(target_duration / bg_video_duration_seconds) + 1
            current_time = 0
            
            for i in range(loop_count):
                remaining_time = target_duration - current_time
                if remaining_time <= 0:
                    break
                    
                current_duration = min(bg_video_duration_seconds, remaining_time)
                
                loop_segment = draft.VideoSegment(
                    bg_video_material,
                    trange(tim(f"{current_time:.6f}s"), tim(f"{current_duration:.6f}s"))
                )
                
                self.context.script.add_segment(loop_segment, track_name="背景视频轨道")
                current_time += current_duration
            
            self._log("info", f"背景视频循环已添加: {os.path.basename(local_path)}，{loop_count}次循环，总时长: {target_duration:.2f}s")
        
        return