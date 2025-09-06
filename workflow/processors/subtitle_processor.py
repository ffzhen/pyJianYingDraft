"""
字幕处理器

负责字幕相关的处理功能
"""

import os
import pyJianYingDraft as draft
from pyJianYingDraft import tim, trange
from typing import Optional, List, Dict, Any, Tuple
from ..core.base import BaseProcessor, WorkflowContext
from ..core.exceptions import ProcessingError

class SubtitleProcessor(BaseProcessor):
    """字幕处理器"""
    
    def process(self, *args, **kwargs):
        """占位方法"""
        pass
        
    def add_subtitle_from_asr(self, asr_result: List[Dict[str, Any]], track_name: str = "内容字幕轨道"):
        """从ASR结果添加字幕
        
        Args:
            asr_result: ASR识别结果列表，每个元素包含text, start_time, end_time
            track_name: 字幕轨道名称
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        if not asr_result:
            self._log("warning", "ASR结果为空，无法生成字幕")
            return
            
        # 确保字幕轨道存在
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.ensure_track_exists(draft.TrackType.text, track_name)
        
        # 清除现有字幕以避免重叠
        track_manager.clear_track_segments(track_name)
        
        # 获取有效视频时长用于验证
        effective_duration = self.context.get_effective_video_duration()
        
        subtitle_count = 0
        for segment in asr_result:
            try:
                text = segment.get('text', '').strip()
                if not text:
                    continue
                    
                start_time = float(segment.get('start_time', 0))
                end_time = float(segment.get('end_time', start_time + 1))
                
                # 验证时间边界
                from ..managers.duration_manager import DurationManager
                duration_manager = DurationManager(self.context, self.logger)
                
                # 确保开始时间和结束时间都在有效范围内
                if effective_duration > 0:
                    start_time = min(start_time, effective_duration)
                    end_time = min(end_time, effective_duration)
                
                # 确保结束时间大于开始时间
                if end_time <= start_time:
                    end_time = start_time + 1.00  # 最小1秒时长
                    
                duration = end_time - start_time
                duration = duration_manager.validate_duration_bounds(duration, f"字幕段({text[:10]}...)")
                
                # 重新计算结束时间
                end_time = start_time + duration
                
                # 创建字幕片段
                text_segment = draft.TextSegment(
                    text=text,
                    time_range=trange(tim(f"{start_time:.6f}s"), tim(f"{end_time:.6f}s"))
                )
                
                # 添加到字幕轨道
                self.context.script.add_segment(text_segment, track_name=track_name)
                subtitle_count += 1
                
                self._log("debug", f"字幕段 {subtitle_count}: '{text[:20]}...' ({start_time:.2f}s - {end_time:.2f}s)")
                
            except Exception as e:
                self._log("warning", f"处理字幕段时出错: {e}, 数据: {segment}")
                continue
        
        self._log("info", f"字幕已添加到轨道 '{track_name}': {subtitle_count} 个字幕段")
        return subtitle_count
        
    def add_title_subtitle(self, title: str, start_time: float = 0.0, duration: float = 3.0, 
                          track_name: str = "标题字幕轨道"):
        """添加标题字幕
        
        Args:
            title: 标题文本
            start_time: 开始时间(秒)
            duration: 持续时长(秒)
            track_name: 字幕轨道名称
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        if not title.strip():
            self._log("warning", "标题为空，跳过添加")
            return
            
        # 确保标题字幕轨道存在
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.ensure_track_exists(draft.TrackType.text, track_name)
        
        # 验证时长边界
        from ..managers.duration_manager import DurationManager
        duration_manager = DurationManager(self.context, self.logger)
        
        # 验证开始时间
        effective_duration = self.context.get_effective_video_duration()
        if effective_duration > 0 and start_time >= effective_duration:
            start_time = max(0, effective_duration - duration)
            self._log("warning", f"标题开始时间超出范围，调整为: {start_time:.2f}s")
        
        # 验证持续时长
        available_duration = effective_duration - start_time if effective_duration > 0 else duration
        duration = min(duration, available_duration)
        duration = duration_manager.validate_duration_bounds(duration, "标题字幕")
        
        end_time = start_time + duration
        
        # 创建标题字幕片段
        title_segment = draft.TextSegment(
            text=title,
            time_range=trange(tim(f"{start_time:.6f}s"), tim(f"{end_time:.6f}s"))
        )
        
        # 添加到标题字幕轨道
        self.context.script.add_segment(title_segment, track_name=track_name)
        
        self._log("info", f"标题字幕已添加: '{title}' ({start_time:.2f}s - {end_time:.2f}s)")
        return title_segment
        
    def add_custom_subtitle(self, text: str, start_time: float, end_time: float, 
                           track_name: str = "内容字幕轨道"):
        """添加自定义字幕
        
        Args:
            text: 字幕文本
            start_time: 开始时间(秒)
            end_time: 结束时间(秒)
            track_name: 字幕轨道名称
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        if not text.strip():
            self._log("warning", "字幕文本为空，跳过添加")
            return
            
        # 确保字幕轨道存在
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.ensure_track_exists(draft.TrackType.text, track_name)
        
        # 验证时间参数
        if end_time <= start_time:
            end_time = start_time + 1.00  # 最小1秒时长
            self._log("warning", f"字幕结束时间无效，调整为: {end_time:.2f}s")
        
        # 验证时长边界
        from ..managers.duration_manager import DurationManager
        duration_manager = DurationManager(self.context, self.logger)
        
        duration = end_time - start_time
        duration = duration_manager.validate_duration_bounds(duration, f"自定义字幕({text[:10]}...)")
        end_time = start_time + duration
        
        # 创建字幕片段
        text_segment = draft.TextSegment(
            text=text,
            time_range=trange(tim(f"{start_time:.6f}s"), tim(f"{end_time:.6f}s"))
        )
        
        # 添加到字幕轨道
        self.context.script.add_segment(text_segment, track_name=track_name)
        
        self._log("info", f"自定义字幕已添加: '{text}' ({start_time:.2f}s - {end_time:.2f}s)")
        return text_segment
        
    def process_subtitle_timing_optimization(self, min_duration: float = 1.0, max_duration: float = 8.0):
        """优化字幕时间，确保合适的显示时长
        
        Args:
            min_duration: 最小字幕时长(秒)
            max_duration: 最大字幕时长(秒)
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        # 找到所有字幕轨道
        subtitle_tracks = []
        for track_name, track in self.context.script.tracks.items():
            if hasattr(track, 'track_type') and track.track_type == draft.TrackType.text:
                subtitle_tracks.append((track_name, track))
        
        if not subtitle_tracks:
            self._log("warning", "没有找到字幕轨道")
            return
        
        optimized_count = 0
        for track_name, track in subtitle_tracks:
            if hasattr(track, 'segments') and track.segments:
                for segment in track.segments:
                    if hasattr(segment, 'time_range'):
                        # 获取当前时长
                        start_micro = segment.time_range.start
                        end_micro = segment.time_range.end
                        
                        current_duration = (end_micro - start_micro) / 1000000
                        
                        # 检查是否需要优化
                        needs_optimization = False
                        new_duration = current_duration
                        
                        if current_duration < min_duration:
                            new_duration = min_duration
                            needs_optimization = True
                        elif current_duration > max_duration:
                            new_duration = max_duration
                            needs_optimization = True
                        
                        if needs_optimization:
                            # 验证新时长
                            from ..managers.duration_manager import DurationManager
                            duration_manager = DurationManager(self.context, self.logger)
                            new_duration = duration_manager.validate_duration_bounds(new_duration, f"优化字幕({track_name})")
                            
                            # 更新时间范围
                            new_end_micro = start_micro + int(new_duration * 1000000)
                            segment.time_range = trange(start_micro, new_end_micro)
                            
                            optimized_count += 1
                            self._log("debug", f"优化字幕时长: {current_duration:.2f}s -> {new_duration:.2f}s")
        
        self._log("info", f"字幕时间优化完成，共优化 {optimized_count} 个字幕段")
        return optimized_count
        
    def get_subtitle_statistics(self) -> Dict[str, Any]:
        """获取字幕统计信息
        
        Returns:
            包含字幕统计信息的字典
        """
        if not self.context.script:
            return {}
            
        stats = {
            "total_tracks": 0,
            "total_segments": 0,
            "total_duration": 0.0,
            "tracks": {}
        }
        
        # 统计所有字幕轨道
        for track_name, track in self.context.script.tracks.items():
            if hasattr(track, 'track_type') and track.track_type == draft.TrackType.text:
                stats["total_tracks"] += 1
                
                track_stats = {
                    "segments": 0,
                    "duration": 0.0,
                    "avg_duration": 0.0
                }
                
                if hasattr(track, 'segments') and track.segments:
                    track_stats["segments"] = len(track.segments)
                    stats["total_segments"] += track_stats["segments"]
                    
                    # 计算轨道总时长
                    for segment in track.segments:
                        if hasattr(segment, 'time_range'):
                            segment_duration = (segment.time_range.end - segment.time_range.start) / 1000000
                            track_stats["duration"] += segment_duration
                    
                    # 计算平均时长
                    if track_stats["segments"] > 0:
                        track_stats["avg_duration"] = track_stats["duration"] / track_stats["segments"]
                    
                    stats["total_duration"] += track_stats["duration"]
                
                stats["tracks"][track_name] = track_stats
        
        # 计算整体平均时长
        if stats["total_segments"] > 0:
            stats["avg_duration"] = stats["total_duration"] / stats["total_segments"]
        else:
            stats["avg_duration"] = 0.0
        
        return stats