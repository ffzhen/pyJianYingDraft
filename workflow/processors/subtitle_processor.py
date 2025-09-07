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
    
    def add_captions_with_highlights(self, caption_data: List[Dict[str, Any]], 
                                   track_name: str = "内容字幕轨道",
                                   position: str = "bottom",
                                   keywords: List[str] = None,
                                   base_font_size: float = 8.0,
                                   base_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
                                   font_type: Optional[Any] = None,
                                   highlight_color: Tuple[float, float, float] = (1.0, 0.7529411765, 0.2470588235),
                                   highlight_size: float = 10.0,
                                   bottom_transform_y: float = -0.3,
                                   scale: float = 1.39):
        """添加带关键词高亮的字幕
        
        Args:
            caption_data: 字幕数据列表，每个元素包含text, start, end等信息
            track_name: 轨道名称
            position: 字幕位置 ("top"顶部, "bottom"底部)
            keywords: 需要高亮的关键词列表
            base_font_size: 基础字体大小
            base_color: 基础文字颜色
            font_type: 字体类型
            highlight_color: 关键词高亮颜色
            highlight_size: 高亮字体大小
            bottom_transform_y: 底部位置的transform_y
            scale: 缩放比例
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
        
        if not caption_data:
            self._log("warning", "字幕数据为空")
            return
        
        # 确保字幕轨道存在
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.ensure_track_exists(draft.TrackType.text, track_name)
        
        # 清除现有字幕以避免重叠
        track_manager.clear_track_segments(track_name)
        
        # 设置字体类型
        if font_type is None:
            font_type = draft.FontType.俪金黑
            
        # 根据位置设置不同的垂直位置
        if position == "top":
            transform_y = 0.4
        else:
            transform_y = bottom_transform_y
            
        text_segments = []
        
        for caption in caption_data:
            text = caption.get('text', '')
            start_time = caption.get('start', 0)
            end_time = caption.get('end', start_time + 2)
            
            if not text:
                continue
            
            # 过滤出在当前文本中实际存在的关键词
            current_keywords = []
            if keywords:
                for keyword in keywords:
                    if keyword and keyword.strip() and keyword in text:
                        current_keywords.append(keyword)
            
            # 验证时间边界
            from ..managers.duration_manager import DurationManager
            duration_manager = DurationManager(self.context, self.logger)
            
            duration = end_time - start_time
            duration = duration_manager.validate_duration_bounds(duration, f"字幕段({text[:10]}...)")
            end_time = start_time + duration
            
            # 创建文本片段
            text_segment = draft.TextSegment(
                text,
                trange(tim(f"{start_time:.2f}s"), tim(f"{duration:.2f}s")),
                font=font_type,
                style=draft.TextStyle(
                    color=base_color,
                    size=base_font_size,
                    auto_wrapping=True,
                    bold=True,
                    align=0,  # 居中对齐
                    max_line_width=0.82
                ),
                clip_settings=draft.ClipSettings(transform_y=transform_y, scale_x=scale, scale_y=scale)
            )
            
            # 添加关键词高亮
            if current_keywords:
                for keyword in current_keywords:
                    start_idx = 0
                    while True:
                        pos = text.find(keyword, start_idx)
                        if pos == -1:
                            break
                        end_idx = pos + len(keyword)
                        try:
                            text_segment.add_highlight(pos, end_idx, color=highlight_color, size=highlight_size, bold=True)
                        except Exception as e:
                            self._log("debug", f"添加高亮失败: {e}")
                        start_idx = pos + 1
                
                self._log("info", f"字幕 '{text}' 中高亮关键词: {current_keywords}")
            
            text_segments.append(text_segment)
            self.context.script.add_segment(text_segment, track_name=track_name)
        
        self._log("info", f"带关键词高亮的字幕已添加到轨道 '{track_name}': {len(text_segments)} 个字幕段")
        return text_segments
    
    def add_caption_backgrounds(self, caption_data: List[Dict[str, Any]], 
                               track_name: str = "内容字幕背景",
                               position: str = "bottom",
                               bottom_transform_y: float = -0.3,
                               scale: float = 1.39,
                               background_style: Dict[str, Any] = None):
        """为字幕添加背景色块
        
        Args:
            caption_data: 字幕数据列表，用于计算总时长
            track_name: 背景轨道名称
            position: 字幕位置 ("top"顶部, "bottom"底部)
            bottom_transform_y: 底部位置的transform_y
            scale: 缩放比例
            background_style: 背景样式参数
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
        
        if not caption_data:
            return None
        
        # 默认背景样式
        if background_style is None:
            background_style = {
                "color": "#000000",      # 黑色
                "alpha": 0.67,           # 67% 不透明度
                "height": 0.25,          # 25% 高度
                "width": 0.14,           # 14% 宽度  
                "horizontal_offset": 0.5, # 50% 左右间隙
                "vertical_offset": 0.5,   # 50% 上下间隙
                "round_radius": 0.0,     # 圆角半径
                "style": 1               # 背景样式
            }
        
        # 计算字幕背景的总时长
        start_time = 0.0
        
        # 使用有效视频时长作为背景持续时间
        effective_duration = self.context.get_effective_video_duration()
        if effective_duration > 0:
            total_duration = round(effective_duration, 2)
            self._log("info", f"字幕背景使用有效视频时长: {total_duration:.2f}s")
        else:
            # 回退方案：使用字幕时长
            caption_start = min(caption.get('start', 0) for caption in caption_data)
            caption_end = max(caption.get('end', 0) for caption in caption_data)
            total_duration = round(caption_end - caption_start, 2)
            self._log("info", f"字幕背景使用字幕时长: {total_duration:.2f}s")
        
        # 验证背景时长不超过视频总时长
        from ..managers.duration_manager import DurationManager
        duration_manager = DurationManager(self.context, self.logger)
        total_duration = duration_manager.validate_duration_bounds(total_duration, "字幕背景")
        
        # 根据位置设置不同的垂直位置
        if position == "top":
            transform_y = 0.4
        else:
            transform_y = bottom_transform_y
        
        # 创建背景文本片段（使用占位符确保背景显示）
        placeholder_text = " " * 50  # 使用固定长度的占位符
        
        # 创建文本背景
        text_background = draft.TextBackground(
            color=background_style["color"],
            alpha=background_style["alpha"],
            height=background_style["height"],
            width=background_style["width"],
            horizontal_offset=background_style["horizontal_offset"],
            vertical_offset=background_style["vertical_offset"],
            round_radius=background_style.get("round_radius", 0.0),
            style=background_style.get("style", 1)
        )
        
        # 创建文本样式
        text_style = draft.TextStyle(
            size=15.0,
            color=(1.0, 1.0, 1.0),  # 白色文字
            bold=True,
            align=0,  # 居中对齐
            line_spacing=0
        )
        
        # 创建文本片段
        text_segment = draft.TextSegment(
            placeholder_text,
            trange(tim(f"{start_time:.6f}s"), tim(f"{total_duration:.6f}s")),
            font=draft.FontType.文轩体,
            style=text_style,
            clip_settings=draft.ClipSettings(transform_y=transform_y),
            background=text_background,
            shadow=draft.TextShadow(
                alpha=0.8,
                color=(0.0, 0.0, 0.0),
                diffuse=20.0,
                distance=10.0,
                angle=-45.0
            )
        )
        
        # 确保目标轨道存在
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.ensure_track_exists(draft.TrackType.text, track_name)
        
        # 添加到轨道
        self.context.script.add_segment(text_segment, track_name=track_name)
        
        self._log("info", f"字幕背景已添加到轨道 '{track_name}': {total_duration:.2f}秒")
        return text_segment
    
    def add_three_line_title(self, title: str,
                             start: float = 0.0,
                             duration: Optional[float] = None,
                             track_name: str = "标题字幕轨道",
                             transform_y: float = 0.72,
                             line_spacing: int = 4,
                             highlight_color: Tuple[float, float, float] = (1.0, 0.7529411765, 0.2470588235)):
        """添加三行标题：中间一行高亮
        
        Args:
            title: 标题文本
            start: 开始时间(秒)
            duration: 持续时长(秒)，如果None则使用有效视频时长
            track_name: 轨道名称
            transform_y: 垂直位置
            line_spacing: 行间距
            highlight_color: 高亮颜色
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
        
        # 简单的三行拆分（可以后续优化为AI拆分）
        lines = self._split_title_to_three_lines(title)
        
        # 保障三行
        while len(lines) < 3:
            lines.append("")
        text = "\n".join(lines[:3])
        
        # 计算时间
        if duration is None:
            effective_duration = self.context.get_effective_video_duration()
            duration = round(max(1.0, effective_duration) if effective_duration > 0 else 5.0, 2)
        
        # 验证时长边界
        from ..managers.duration_manager import DurationManager
        duration_manager = DurationManager(self.context, self.logger)
        duration = duration_manager.validate_duration_bounds(duration, "三行标题")
        
        style = draft.TextStyle(
            size=15.0,
            bold=True,
            align=0,  # 左对齐
            color=(1.0, 1.0, 1.0),
            auto_wrapping=True,
            max_line_width=0.7,
            line_spacing=line_spacing
        )
        
        seg = draft.TextSegment(
            text,
            trange(tim(f"{start:.6f}s"), tim(f"{duration:.6f}s")),
            font=draft.FontType.俪金黑,
            style=style,
            clip_settings=draft.ClipSettings(transform_y=transform_y)
        )
        
        # 中间行高亮：计算字符区间
        line1 = lines[0]
        line2 = lines[1]
        start_idx = len(line1) + 1  # 包含换行
        end_idx = start_idx + len(line2)
        if len(line2) > 0:
            seg.add_highlight(start_idx, end_idx, color=highlight_color, bold=True)
        
        # 确保轨道存在
        from ..managers.track_manager import TrackManager
        track_manager = TrackManager(self.context, self.logger)
        track_manager.ensure_track_exists(draft.TrackType.text, track_name)
        
        self.context.script.add_segment(seg, track_name=track_name)
        self._log("info", f"三行标题已添加到 {track_name}: {lines}")
        return seg
    
    def _split_title_to_three_lines(self, title: str) -> List[str]:
        """将标题拆分为3行（简单版本）"""
        if not title:
            return ["", "", ""]
        
        # 简单的平均切分
        length = len(title)
        if length <= 3:
            return [title, "", ""]
        
        # 按标点符号切分，再均匀分配到三行
        import re
        tokens = re.split(r'[，。！？、;；\s]+', title)
        tokens = [t for t in tokens if t]
        
        if len(tokens) <= 3:
            result = tokens[:]
            while len(result) < 3:
                result.append("")
            return result[:3]
        
        # 均匀分配
        target = [[], [], []]
        lengths = [0, 0, 0]
        for token in tokens:
            i = lengths.index(min(lengths))
            target[i].append(token)
            lengths[i] += len(token)
        
        return [''.join(x) for x in target]
        
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