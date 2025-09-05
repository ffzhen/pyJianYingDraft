# -*- coding: utf-8 -*-
"""
具体视频模板实现

实现几种不同风格的具体视频模板
"""

from typing import Dict, Any, List, Optional
import os
import sys

# 添加本地 pyJianYingDraft 模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

import pyJianYingDraft as draft
from pyJianYingDraft import TrackType, trange, tim, TextShadow

from .video_template_base import VideoTemplateBase
from .style_config import style_config_manager


class OriginalStyleTemplate(VideoTemplateBase):
    """原有风格模板 - 保持现有样式"""
    
    def add_captions(self, caption_data: List[Dict[str, Any]], keywords: List[str] = None):
        """添加字幕"""
        caption_style = self.style_config.caption_style
        
        for caption in caption_data:
            text = caption.get('text', '')
            start_time = caption.get('start', 0)
            end_time = caption.get('end', start_time + 2)
            
            if not text:
                continue
            
            # 创建文本片段
            text_segment = draft.TextSegment(
                text,
                trange(tim(f"{start_time}s"), tim(f"{end_time - start_time}s")),
                font=getattr(draft.FontType, caption_style.base_style.font_type, draft.FontType.俪金黑),
                style=draft.TextStyle(
                    color=caption_style.base_style.color,
                    size=caption_style.base_style.size,
                    auto_wrapping=caption_style.base_style.auto_wrapping,
                    bold=caption_style.base_style.bold,
                    align=caption_style.base_style.align,
                    max_line_width=caption_style.base_style.max_line_width
                ),
                clip_settings=draft.ClipSettings(
                    transform_y=caption_style.transform_y,
                    scale_x=caption_style.base_style.scale_x,
                    scale_y=caption_style.base_style.scale_y
                )
            )
            
            # 添加关键词高亮
            if keywords:
                for keyword in keywords:
                    if keyword in text:
                        start_idx = text.find(keyword)
                        end_idx = start_idx + len(keyword)
                        text_segment.add_highlight(
                            start_idx, end_idx, 
                            color=caption_style.highlight_style.color,
                            size=caption_style.highlight_style.size,
                            bold=caption_style.highlight_style.bold
                        )
            
            # 添加阴影
            shadow_style = caption_style.shadow_style
            text_segment.shadow = draft.TextShadow(
                alpha=shadow_style.alpha,
                color=shadow_style.color,
                diffuse=shadow_style.diffuse,
                distance=shadow_style.distance,
                angle=shadow_style.angle
            )
            
            self.script.add_segment(text_segment, track_name="内容字幕轨道")
        
        # 添加字幕背景
        if caption_style.background_style:
            self._add_caption_backgrounds(caption_data)
        
        print(f"✅ 已添加 {len(caption_data)} 段字幕")
    
    def add_title(self, title: str):
        """添加标题"""
        title_style = self.style_config.title_style
        
        # 拆分标题为三行
        lines = self._split_title_to_three_lines(title)
        while len(lines) < 3:
            lines.append("")
        text = "\n".join(lines[:3])
        
        # 计算时长
        duration = self.project_duration if self.project_duration > 0 else self.audio_duration
        
        # 创建标题文本片段
        title_segment = draft.TextSegment(
            text,
            trange(tim("0s"), tim(f"{duration}s")),
            font=getattr(draft.FontType, title_style.base_style.font_type, draft.FontType.俪金黑),
            style=draft.TextStyle(
                color=title_style.base_style.color,
                size=title_style.base_style.size,
                bold=title_style.base_style.bold,
                align=title_style.base_style.align,
                auto_wrapping=title_style.base_style.auto_wrapping,
                max_line_width=title_style.base_style.max_line_width,
                line_spacing=title_style.base_style.line_spacing
            ),
            clip_settings=draft.ClipSettings(transform_y=title_style.transform_y)
        )
        
        # 第二行高亮
        if len(lines) >= 2 and lines[1]:
            line1_len = len(lines[0]) + 1  # 包含换行符
            start_idx = line1_len
            end_idx = start_idx + len(lines[1])
            title_segment.add_highlight(
                start_idx, end_idx,
                color=title_style.highlight_style.color,
                size=title_style.highlight_style.size,
                bold=title_style.highlight_style.bold
            )
        
        # 添加阴影
        shadow_style = title_style.shadow_style
        title_segment.shadow = draft.TextShadow(
            alpha=shadow_style.alpha,
            color=shadow_style.color,
            diffuse=shadow_style.diffuse,
            distance=shadow_style.distance,
            angle=shadow_style.angle
        )
        
        self.script.add_segment(title_segment, track_name="标题字幕轨道")
        
        # 添加标题背景
        if title_style.background_style:
            self._add_title_background(title, duration)
        
        print(f"✅ 已添加标题: {title}")
    
    def _split_title_to_three_lines(self, title: str) -> List[str]:
        """将标题拆分为三行"""
        title = (title or "").strip()
        if not title:
            return ["", "", ""]
        
        # 优先使用AI拆分
        if self.volcengine_asr and self.volcengine_asr.doubao_token:
            try:
                import requests
                payload = {
                    "model": self.volcengine_asr.doubao_model,
                    "messages": [
                        {"role": "system", "content": (
                            "你是文案排版助手。请把给定中文标题合理断句为3行，"
                            "每行尽量语义完整、长度均衡。只返回三行内容，用\\n分隔，不要额外说明。"
                        )},
                        {"role": "user", "content": f"标题：{title}\\n输出3行："}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3
                }
                resp = requests.post(
                    'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.volcengine_asr.doubao_token}'
                    },
                    json=payload,
                    timeout=20
                )
                if resp.status_code == 200:
                    content = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '')
                    lines = [ln.strip() for ln in content.split("\\n") if ln.strip()]
                    if len(lines) >= 3:
                        return lines[:3]
            except Exception:
                pass
        
        # 本地回退：按标点切分
        import re
        tokens = re.split(r'[，。！？、;；\\s]+', title)
        tokens = [t for t in tokens if t]
        
        if not tokens:
            # 平均切分
            n = len(title)
            a = max(1, n // 3)
            b = max(1, (n - a) // 2)
            return [title[:a], title[a:a+b], title[a+b:]]
        
        # 均匀分配
        target = [[], [], []]
        lengths = [0, 0, 0]
        for tok in tokens:
            i = lengths.index(min(lengths))
            target[i].append(tok)
            lengths[i] += len(tok)
        
        return [''.join(x) for x in target]
    
    def _add_caption_backgrounds(self, caption_data: List[Dict[str, Any]]):
        """添加字幕背景"""
        caption_style = self.style_config.caption_style
        bg_style = caption_style.background_style
        
        if not caption_data or not bg_style:
            return
        
        # 计算总时长
        start_time = min(caption.get('start', 0) for caption in caption_data)
        end_time = max(caption.get('end', 0) for caption in caption_data)
        total_duration = end_time - start_time
        
        # 创建背景文本片段
        placeholder_text = " " * 50
        
        bg_segment = draft.TextSegment(
            placeholder_text,
            trange(tim(f"{start_time}s"), tim(f"{total_duration}s")),
            font=draft.FontType.文轩体,
            style=draft.TextStyle(
                size=15.0,
                color=(1.0, 1.0, 1.0),
                bold=True,
                align=0
            ),
            clip_settings=draft.ClipSettings(transform_y=caption_style.transform_y),
            background=draft.TextBackground(
                color=bg_style.color,
                alpha=bg_style.alpha,
                height=bg_style.height,
                width=bg_style.width,
                horizontal_offset=bg_style.horizontal_offset,
                vertical_offset=bg_style.vertical_offset,
                round_radius=bg_style.round_radius,
                style=bg_style.style
            )
        )
        
        self.script.add_segment(bg_segment, track_name="内容字幕背景")
    
    def _add_title_background(self, title: str, duration: float):
        """添加标题背景"""
        title_style = self.style_config.title_style
        bg_style = title_style.background_style
        
        if not bg_style:
            return
        
        # 创建背景文本片段
        placeholder_text = " " * 50
        
        bg_segment = draft.TextSegment(
            placeholder_text,
            trange(tim("0s"), tim(f"{duration}s")),
            font=draft.FontType.文轩体,
            style=draft.TextStyle(
                size=15.0,
                color=(1.0, 1.0, 1.0),
                bold=True,
                align=0
            ),
            clip_settings=draft.ClipSettings(transform_y=title_style.transform_y),
            background=draft.TextBackground(
                color=bg_style.color,
                alpha=bg_style.alpha,
                height=bg_style.height,
                width=bg_style.width,
                horizontal_offset=bg_style.horizontal_offset,
                vertical_offset=bg_style.vertical_offset,
                round_radius=bg_style.round_radius,
                style=bg_style.style
            )
        )
        
        self.script.add_segment(bg_segment, track_name="标题字幕背景")


class TechStyleTemplate(VideoTemplateBase):
    """科技风格模板"""
    
    def add_captions(self, caption_data: List[Dict[str, Any]], keywords: List[str] = None):
        """添加科技风格字幕"""
        caption_style = self.style_config.caption_style
        
        for caption in caption_data:
            text = caption.get('text', '')
            start_time = caption.get('start', 0)
            end_time = caption.get('end', start_time + 2)
            
            if not text:
                continue
            
            # 科技风格：青色字体，绿色高亮，黑色半透明背景
            text_segment = draft.TextSegment(
                text,
                trange(tim(f"{start_time}s"), tim(f"{end_time - start_time}s")),
                font=getattr(draft.FontType, caption_style.base_style.font_type, draft.FontType.俪金黑),
                style=draft.TextStyle(
                    color=caption_style.base_style.color,  # 青色
                    size=caption_style.base_style.size,
                    auto_wrapping=caption_style.base_style.auto_wrapping,
                    bold=caption_style.base_style.bold,
                    align=caption_style.base_style.align,
                    max_line_width=caption_style.base_style.max_line_width,
                    line_spacing=caption_style.base_style.line_spacing
                ),
                clip_settings=draft.ClipSettings(
                    transform_y=caption_style.transform_y,
                    scale_x=caption_style.base_style.scale_x,
                    scale_y=caption_style.base_style.scale_y
                )
            )
            
            # 科技风格关键词高亮
            if keywords:
                for keyword in keywords:
                    if keyword in text:
                        start_idx = text.find(keyword)
                        end_idx = start_idx + len(keyword)
                        text_segment.add_highlight(
                            start_idx, end_idx,
                            color=caption_style.highlight_style.color,  # 绿色
                            size=caption_style.highlight_style.size,
                            bold=caption_style.highlight_style.bold
                        )
            
            # 科技风格阴影
            shadow_style = caption_style.shadow_style
            text_segment.shadow = draft.TextShadow(
                alpha=shadow_style.alpha,
                color=shadow_style.color,
                diffuse=shadow_style.diffuse,
                distance=shadow_style.distance,
                angle=shadow_style.angle
            )
            
            self.script.add_segment(text_segment, track_name="内容字幕轨道")
        
        # 添加科技风格背景
        if caption_style.background_style:
            self._add_tech_caption_backgrounds(caption_data)
        
        print(f"✅ 已添加科技风格字幕 {len(caption_data)} 段")
    
    def add_title(self, title: str):
        """添加科技风格标题"""
        title_style = self.style_config.title_style
        
        # 拆分标题
        lines = self._split_title_to_three_lines(title)
        while len(lines) < 3:
            lines.append("")
        text = "\n".join(lines[:3])
        
        duration = self.project_duration if self.project_duration > 0 else self.audio_duration
        
        # 科技风格标题
        title_segment = draft.TextSegment(
            text,
            trange(tim("0s"), tim(f"{duration}s")),
            font=getattr(draft.FontType, title_style.base_style.font_type, draft.FontType.俪金黑),
            style=draft.TextStyle(
                color=title_style.base_style.color,  # 青色
                size=title_style.base_style.size,
                bold=title_style.base_style.bold,
                align=title_style.base_style.align,
                auto_wrapping=title_style.base_style.auto_wrapping,
                max_line_width=title_style.base_style.max_line_width,
                line_spacing=title_style.base_style.line_spacing
            ),
            clip_settings=draft.ClipSettings(transform_y=title_style.transform_y)
        )
        
        # 第二行高亮
        if len(lines) >= 2 and lines[1]:
            line1_len = len(lines[0]) + 1
            start_idx = line1_len
            end_idx = start_idx + len(lines[1])
            title_segment.add_highlight(
                start_idx, end_idx,
                color=title_style.highlight_style.color,  # 绿色
                size=title_style.highlight_style.size,
                bold=title_style.highlight_style.bold
            )
        
        # 科技风格阴影
        shadow_style = title_style.shadow_style
        title_segment.shadow = draft.TextShadow(
            alpha=shadow_style.alpha,
            color=shadow_style.color,
            diffuse=shadow_style.diffuse,
            distance=shadow_style.distance,
            angle=shadow_style.angle
        )
        
        self.script.add_segment(title_segment, track_name="标题字幕轨道")
        
        # 添加科技风格标题背景
        if title_style.background_style:
            self._add_tech_title_background(title, duration)
        
        print(f"✅ 已添加科技风格标题: {title}")
    
    def _split_title_to_three_lines(self, title: str) -> List[str]:
        """拆分标题为三行"""
        # 复用原有逻辑
        original_template = OriginalStyleTemplate(self.draft_folder_path, self.project_name, self.style_config)
        original_template.volcengine_asr = self.volcengine_asr
        return original_template._split_title_to_three_lines(title)
    
    def _add_tech_caption_backgrounds(self, caption_data: List[Dict[str, Any]]):
        """添加科技风格字幕背景"""
        caption_style = self.style_config.caption_style
        bg_style = caption_style.background_style
        
        if not caption_data or not bg_style:
            return
        
        start_time = min(caption.get('start', 0) for caption in caption_data)
        end_time = max(caption.get('end', 0) for caption in caption_data)
        total_duration = end_time - start_time
        
        placeholder_text = " " * 50
        
        bg_segment = draft.TextSegment(
            placeholder_text,
            trange(tim(f"{start_time}s"), tim(f"{total_duration}s")),
            font=draft.FontType.文轩体,
            style=draft.TextStyle(
                size=15.0,
                color=(1.0, 1.0, 1.0),
                bold=True,
                align=0
            ),
            clip_settings=draft.ClipSettings(transform_y=caption_style.transform_y),
            background=draft.TextBackground(
                color=bg_style.color,  # 黑色
                alpha=bg_style.alpha,  # 80%不透明度
                height=bg_style.height,
                width=bg_style.width,
                horizontal_offset=bg_style.horizontal_offset,
                vertical_offset=bg_style.vertical_offset,
                round_radius=bg_style.round_radius,
                style=bg_style.style
            )
        )
        
        self.script.add_segment(bg_segment, track_name="内容字幕背景")
    
    def _add_tech_title_background(self, title: str, duration: float):
        """添加科技风格标题背景"""
        title_style = self.style_config.title_style
        bg_style = title_style.background_style
        
        if not bg_style:
            return
        
        placeholder_text = " " * 50
        
        bg_segment = draft.TextSegment(
            placeholder_text,
            trange(tim("0s"), tim(f"{duration}s")),
            font=draft.FontType.文轩体,
            style=draft.TextStyle(
                size=15.0,
                color=(1.0, 1.0, 1.0),
                bold=True,
                align=0
            ),
            clip_settings=draft.ClipSettings(transform_y=title_style.transform_y),
            background=draft.TextBackground(
                color=bg_style.color,  # 深蓝色
                alpha=bg_style.alpha,
                height=bg_style.height,
                width=bg_style.width,
                horizontal_offset=bg_style.horizontal_offset,
                vertical_offset=bg_style.vertical_offset,
                round_radius=bg_style.round_radius,
                style=bg_style.style
            )
        )
        
        self.script.add_segment(bg_segment, track_name="标题字幕背景")


class WarmStyleTemplate(VideoTemplateBase):
    """温馨风格模板"""
    
    def add_captions(self, caption_data: List[Dict[str, Any]], keywords: List[str] = None):
        """添加温馨风格字幕"""
        caption_style = self.style_config.caption_style
        
        for caption in caption_data:
            text = caption.get('text', '')
            start_time = caption.get('start', 0)
            end_time = caption.get('end', start_time + 2)
            
            if not text:
                continue
            
            # 温馨风格：暖白色字体，粉红色高亮，棕色背景
            text_segment = draft.TextSegment(
                text,
                trange(tim(f"{start_time}s"), tim(f"{end_time - start_time}s")),
                font=getattr(draft.FontType, caption_style.base_style.font_type, draft.FontType.文轩体),
                style=draft.TextStyle(
                    color=caption_style.base_style.color,  # 暖白色
                    size=caption_style.base_style.size,
                    auto_wrapping=caption_style.base_style.auto_wrapping,
                    bold=caption_style.base_style.bold,
                    align=caption_style.base_style.align,
                    max_line_width=caption_style.base_style.max_line_width,
                    line_spacing=caption_style.base_style.line_spacing
                ),
                clip_settings=draft.ClipSettings(
                    transform_y=caption_style.transform_y,
                    scale_x=caption_style.base_style.scale_x,
                    scale_y=caption_style.base_style.scale_y
                )
            )
            
            # 温馨风格关键词高亮
            if keywords:
                for keyword in keywords:
                    if keyword in text:
                        start_idx = text.find(keyword)
                        end_idx = start_idx + len(keyword)
                        text_segment.add_highlight(
                            start_idx, end_idx,
                            color=caption_style.highlight_style.color,  # 粉红色
                            size=caption_style.highlight_style.size,
                            bold=caption_style.highlight_style.bold
                        )
            
            # 温馨风格阴影
            shadow_style = caption_style.shadow_style
            text_segment.shadow = draft.TextShadow(
                alpha=shadow_style.alpha,
                color=shadow_style.color,
                diffuse=shadow_style.diffuse,
                distance=shadow_style.distance,
                angle=shadow_style.angle
            )
            
            self.script.add_segment(text_segment, track_name="内容字幕轨道")
        
        # 添加温馨风格背景
        if caption_style.background_style:
            self._add_warm_caption_backgrounds(caption_data)
        
        print(f"✅ 已添加温馨风格字幕 {len(caption_data)} 段")
    
    def add_title(self, title: str):
        """添加温馨风格标题"""
        title_style = self.style_config.title_style
        
        # 拆分标题
        lines = self._split_title_to_three_lines(title)
        while len(lines) < 3:
            lines.append("")
        text = "\n".join(lines[:3])
        
        duration = self.project_duration if self.project_duration > 0 else self.audio_duration
        
        # 温馨风格标题
        title_segment = draft.TextSegment(
            text,
            trange(tim("0s"), tim(f"{duration}s")),
            font=getattr(draft.FontType, title_style.base_style.font_type, draft.FontType.文轩体),
            style=draft.TextStyle(
                color=title_style.base_style.color,  # 暖黄色
                size=title_style.base_style.size,
                bold=title_style.base_style.bold,
                align=title_style.base_style.align,
                auto_wrapping=title_style.base_style.auto_wrapping,
                max_line_width=title_style.base_style.max_line_width,
                line_spacing=title_style.base_style.line_spacing
            ),
            clip_settings=draft.ClipSettings(transform_y=title_style.transform_y)
        )
        
        # 第二行高亮
        if len(lines) >= 2 and lines[1]:
            line1_len = len(lines[0]) + 1
            start_idx = line1_len
            end_idx = start_idx + len(lines[1])
            title_segment.add_highlight(
                start_idx, end_idx,
                color=title_style.highlight_style.color,  # 红色
                size=title_style.highlight_style.size,
                bold=title_style.highlight_style.bold
            )
        
        # 温馨风格阴影
        shadow_style = title_style.shadow_style
        title_segment.shadow = draft.TextShadow(
            alpha=shadow_style.alpha,
            color=shadow_style.color,
            diffuse=shadow_style.diffuse,
            distance=shadow_style.distance,
            angle=shadow_style.angle
        )
        
        self.script.add_segment(title_segment, track_name="标题字幕轨道")
        
        # 添加温馨风格标题背景
        if title_style.background_style:
            self._add_warm_title_background(title, duration)
        
        print(f"✅ 已添加温馨风格标题: {title}")
    
    def _split_title_to_three_lines(self, title: str) -> List[str]:
        """拆分标题为三行"""
        original_template = OriginalStyleTemplate(self.draft_folder_path, self.project_name, self.style_config)
        original_template.volcengine_asr = self.volcengine_asr
        return original_template._split_title_to_three_lines(title)
    
    def _add_warm_caption_backgrounds(self, caption_data: List[Dict[str, Any]]):
        """添加温馨风格字幕背景"""
        caption_style = self.style_config.caption_style
        bg_style = caption_style.background_style
        
        if not caption_data or not bg_style:
            return
        
        start_time = min(caption.get('start', 0) for caption in caption_data)
        end_time = max(caption.get('end', 0) for caption in caption_data)
        total_duration = end_time - start_time
        
        placeholder_text = " " * 50
        
        bg_segment = draft.TextSegment(
            placeholder_text,
            trange(tim(f"{start_time}s"), tim(f"{total_duration}s")),
            font=draft.FontType.文轩体,
            style=draft.TextStyle(
                size=15.0,
                color=(1.0, 1.0, 1.0),
                bold=True,
                align=0
            ),
            clip_settings=draft.ClipSettings(transform_y=caption_style.transform_y),
            background=draft.TextBackground(
                color=bg_style.color,  # 棕色
                alpha=bg_style.alpha,
                height=bg_style.height,
                width=bg_style.width,
                horizontal_offset=bg_style.horizontal_offset,
                vertical_offset=bg_style.vertical_offset,
                round_radius=bg_style.round_radius,
                style=bg_style.style
            )
        )
        
        self.script.add_segment(bg_segment, track_name="内容字幕背景")
    
    def _add_warm_title_background(self, title: str, duration: float):
        """添加温馨风格标题背景"""
        title_style = self.style_config.title_style
        bg_style = title_style.background_style
        
        if not bg_style:
            return
        
        placeholder_text = " " * 50
        
        bg_segment = draft.TextSegment(
            placeholder_text,
            trange(tim("0s"), tim(f"{duration}s")),
            font=draft.FontType.文轩体,
            style=draft.TextStyle(
                size=15.0,
                color=(1.0, 1.0, 1.0),
                bold=True,
                align=0
            ),
            clip_settings=draft.ClipSettings(transform_y=title_style.transform_y),
            background=draft.TextBackground(
                color=bg_style.color,  # 暖色背景
                alpha=bg_style.alpha,
                height=bg_style.height,
                width=bg_style.width,
                horizontal_offset=bg_style.horizontal_offset,
                vertical_offset=bg_style.vertical_offset,
                round_radius=bg_style.round_radius,
                style=bg_style.style
            )
        )
        
        self.script.add_segment(bg_segment, track_name="标题字幕背景")


class BusinessStyleTemplate(VideoTemplateBase):
    """商务风格模板"""
    
    def add_captions(self, caption_data: List[Dict[str, Any]], keywords: List[str] = None):
        """添加商务风格字幕"""
        caption_style = self.style_config.caption_style
        
        for caption in caption_data:
            text = caption.get('text', '')
            start_time = caption.get('start', 0)
            end_time = caption.get('end', start_time + 2)
            
            if not text:
                continue
            
            # 商务风格：黑色字体，蓝色高亮，浅灰色背景
            text_segment = draft.TextSegment(
                text,
                trange(tim(f"{start_time}s"), tim(f"{end_time - start_time}s")),
                font=getattr(draft.FontType, caption_style.base_style.font_type, draft.FontType.宋体),
                style=draft.TextStyle(
                    color=caption_style.base_style.color,  # 黑色
                    size=caption_style.base_style.size,
                    auto_wrapping=caption_style.base_style.auto_wrapping,
                    bold=caption_style.base_style.bold,
                    align=caption_style.base_style.align,
                    max_line_width=caption_style.base_style.max_line_width,
                    line_spacing=caption_style.base_style.line_spacing
                ),
                clip_settings=draft.ClipSettings(
                    transform_y=caption_style.transform_y,
                    scale_x=caption_style.base_style.scale_x,
                    scale_y=caption_style.base_style.scale_y
                )
            )
            
            # 商务风格关键词高亮
            if keywords:
                for keyword in keywords:
                    if keyword in text:
                        start_idx = text.find(keyword)
                        end_idx = start_idx + len(keyword)
                        text_segment.add_highlight(
                            start_idx, end_idx,
                            color=caption_style.highlight_style.color,  # 蓝色
                            size=caption_style.highlight_style.size,
                            bold=caption_style.highlight_style.bold
                        )
            
            # 商务风格阴影
            shadow_style = caption_style.shadow_style
            text_segment.shadow = draft.TextShadow(
                alpha=shadow_style.alpha,
                color=shadow_style.color,
                diffuse=shadow_style.diffuse,
                distance=shadow_style.distance,
                angle=shadow_style.angle
            )
            
            self.script.add_segment(text_segment, track_name="内容字幕轨道")
        
        # 添加商务风格背景
        if caption_style.background_style:
            self._add_business_caption_backgrounds(caption_data)
        
        print(f"✅ 已添加商务风格字幕 {len(caption_data)} 段")
    
    def add_title(self, title: str):
        """添加商务风格标题"""
        title_style = self.style_config.title_style
        
        # 拆分标题
        lines = self._split_title_to_three_lines(title)
        while len(lines) < 3:
            lines.append("")
        text = "\n".join(lines[:3])
        
        duration = self.project_duration if self.project_duration > 0 else self.audio_duration
        
        # 商务风格标题
        title_segment = draft.TextSegment(
            text,
            trange(tim("0s"), tim(f"{duration}s")),
            font=getattr(draft.FontType, title_style.base_style.font_type, draft.FontType.黑体),
            style=draft.TextStyle(
                color=title_style.base_style.color,  # 黑色
                size=title_style.base_style.size,
                bold=title_style.base_style.bold,
                align=title_style.base_style.align,
                auto_wrapping=title_style.base_style.auto_wrapping,
                max_line_width=title_style.base_style.max_line_width,
                line_spacing=title_style.base_style.line_spacing
            ),
            clip_settings=draft.ClipSettings(transform_y=title_style.transform_y)
        )
        
        # 第二行高亮
        if len(lines) >= 2 and lines[1]:
            line1_len = len(lines[0]) + 1
            start_idx = line1_len
            end_idx = start_idx + len(lines[1])
            title_segment.add_highlight(
                start_idx, end_idx,
                color=title_style.highlight_style.color,  # 蓝色
                size=title_style.highlight_style.size,
                bold=title_style.highlight_style.bold
            )
        
        # 商务风格阴影
        shadow_style = title_style.shadow_style
        title_segment.shadow = draft.TextShadow(
            alpha=shadow_style.alpha,
            color=shadow_style.color,
            diffuse=shadow_style.diffuse,
            distance=shadow_style.distance,
            angle=shadow_style.angle
        )
        
        self.script.add_segment(title_segment, track_name="标题字幕轨道")
        
        # 添加商务风格标题背景
        if title_style.background_style:
            self._add_business_title_background(title, duration)
        
        print(f"✅ 已添加商务风格标题: {title}")
    
    def _split_title_to_three_lines(self, title: str) -> List[str]:
        """拆分标题为三行"""
        original_template = OriginalStyleTemplate(self.draft_folder_path, self.project_name, self.style_config)
        original_template.volcengine_asr = self.volcengine_asr
        return original_template._split_title_to_three_lines(title)
    
    def _add_business_caption_backgrounds(self, caption_data: List[Dict[str, Any]]):
        """添加商务风格字幕背景"""
        caption_style = self.style_config.caption_style
        bg_style = caption_style.background_style
        
        if not caption_data or not bg_style:
            return
        
        start_time = min(caption.get('start', 0) for caption in caption_data)
        end_time = max(caption.get('end', 0) for caption in caption_data)
        total_duration = end_time - start_time
        
        placeholder_text = " " * 50
        
        bg_segment = draft.TextSegment(
            placeholder_text,
            trange(tim(f"{start_time}s"), tim(f"{total_duration}s")),
            font=draft.FontType.宋体,
            style=draft.TextStyle(
                size=15.0,
                color=(0.0, 0.0, 0.0),
                bold=True,
                align=0
            ),
            clip_settings=draft.ClipSettings(transform_y=caption_style.transform_y),
            background=draft.TextBackground(
                color=bg_style.color,  # 浅灰色
                alpha=bg_style.alpha,
                height=bg_style.height,
                width=bg_style.width,
                horizontal_offset=bg_style.horizontal_offset,
                vertical_offset=bg_style.vertical_offset,
                round_radius=bg_style.round_radius,
                style=bg_style.style
            )
        )
        
        self.script.add_segment(bg_segment, track_name="内容字幕背景")
    
    def _add_business_title_background(self, title: str, duration: float):
        """添加商务风格标题背景"""
        title_style = self.style_config.title_style
        bg_style = title_style.background_style
        
        if not bg_style:
            return
        
        placeholder_text = " " * 50
        
        bg_segment = draft.TextSegment(
            placeholder_text,
            trange(tim("0s"), tim(f"{duration}s")),
            font=draft.FontType.黑体,
            style=draft.TextStyle(
                size=15.0,
                color=(0.0, 0.0, 0.0),
                bold=True,
                align=0
            ),
            clip_settings=draft.ClipSettings(transform_y=title_style.transform_y),
            background=draft.TextBackground(
                color=bg_style.color,  # 白色
                alpha=bg_style.alpha,
                height=bg_style.height,
                width=bg_style.width,
                horizontal_offset=bg_style.horizontal_offset,
                vertical_offset=bg_style.vertical_offset,
                round_radius=bg_style.round_radius,
                style=bg_style.style
            )
        )
        
        self.script.add_segment(bg_segment, track_name="标题字幕背景")


# 注册模板类
from .video_template_base import VideoTemplateFactory

VideoTemplateFactory.register_template("original", OriginalStyleTemplate)
VideoTemplateFactory.register_template("tech", TechStyleTemplate)
VideoTemplateFactory.register_template("warm", WarmStyleTemplate)
VideoTemplateFactory.register_template("business", BusinessStyleTemplate)