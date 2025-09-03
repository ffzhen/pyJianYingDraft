"""
基于flow.json的Python实现 - 简化版（只使用火山引擎ASR）
使用pyJianYingDraft包重新实现视频编辑工作流逻辑
"""

import os
import json
import sys
import tempfile
import subprocess

# 添加本地 pyJianYingDraft 模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

import pyJianYingDraft as draft
from pyJianYingDraft import TrackType, trange, tim, TextShadow, IntroType, TransitionType
from typing import List, Dict, Any, Optional, Tuple
import requests
from datetime import datetime
from urllib.parse import urlparse
import re
import math

# 火山引擎ASR - 唯一字幕识别方案
try:
    from .volcengine_asr import VolcengineASR
    from .asr_silence_processor import ASRBasedSilenceRemover, ASRSilenceDetector
except ImportError:
    # 当直接运行此文件时，使用绝对导入
    from volcengine_asr import VolcengineASR
    from asr_silence_processor import ASRBasedSilenceRemover, ASRSilenceDetector


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
        self.video_duration = 0  # 视频总时长（秒）
        self.project_duration = 0  # 项目总时长（秒），取音视频最长者
        self.volcengine_asr = None  # 火山引擎ASR客户端
        self.silence_remover = None  # 停顿移除器
        self.digital_video_path = None  # 数字人视频路径
        self.material_video_path = None  # 素材视频路径
        
        # 初始化字幕相关属性
        self.adjusted_subtitles = None  # 调整后的字幕（停顿移除后）
        self.original_subtitles = None  # 原始字幕（停顿移除前）
        
    def _generate_unique_filename(self, prefix: str, extension: str = ".mp4") -> str:
        """生成唯一的文件名，避免不同项目之间的文件冲突
        
        Args:
            prefix: 文件名前缀
            extension: 文件扩展名
            
        Returns:
            唯一的文件路径
        """
        import time
        import uuid
        
        # 使用时间戳和UUID生成唯一文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]  # 使用UUID的前8位
        filename = f"{prefix}_{timestamp}_{unique_id}{extension}"
        
        # 确保temp_materials目录存在
        os.makedirs("temp_materials", exist_ok=True)
        
        return f"temp_materials/{filename}"
    
    def initialize_asr(self, volcengine_appid: str = None, volcengine_access_token: str = None,
                       doubao_token: str = None, doubao_model: str = "ep-20241227135740-g7v7w"):
        """初始化火山引擎ASR
        
        Args:
            volcengine_appid: 火山引擎ASR AppID
            volcengine_access_token: 火山引擎ASR AccessToken
            doubao_token: 豆包API Token（用于标题拆分）
            doubao_model: 豆包模型名称
        """
        if volcengine_appid and volcengine_access_token:
            self.volcengine_asr = VolcengineASR(
                appid=volcengine_appid, 
                access_token=volcengine_access_token,
                doubao_token=doubao_token,
                doubao_model=doubao_model
            )
            print(f"[OK] 火山引擎ASR已初始化 (AppID: {volcengine_appid})")
        else:
            print("[ERROR] ASR初始化失败：缺少必需的参数")
            raise ValueError("必须提供 volcengine_appid 和 volcengine_access_token 参数")
        
    def _split_title_to_three_lines(self, title: str) -> List[str]:
        """使用豆包模型将标题智能拆分为3行；失败时使用本地回退规则。
        Returns: [line1, line2, line3]
        """
        title = (title or "").strip()
        if not title:
            return ["", "", ""]

        # 优先走豆包API
        try:
            if self.volcengine_asr and self.volcengine_asr.doubao_token:
                payload = {
                    "model": self.volcengine_asr.doubao_model,
                    "messages": [
                        {"role": "system", "content": (
                            "你是文案排版助手。请把给定中文标题合理断句为3行，" \
                            "每行尽量语义完整、长度均衡。只返回三行内容，用\n分隔，不要额外说明。"
                        )},
                        {"role": "user", "content": f"标题：{title}\n输出3行："}
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
                    lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
                    if len(lines) >= 3:
                        return lines[:3]
        except Exception as _:
            pass

        # 本地回退：按中文标点切分，再均匀合并到三份
        import re
        tokens = re.split(r'[，。！？、;；\s]+', title)
        tokens = [t for t in tokens if t]
        if not tokens:
            # 最简单退化：平均切字符
            n = len(title)
            a = max(1, n // 3)
            b = max(1, (n - a) // 2)
            return [title[:a], title[a:a+b], title[a+b:]]

        target = [[], [], []]
        lengths = [0, 0, 0]
        for tok in tokens:
            i = lengths.index(min(lengths))
            target[i].append(tok)
            lengths[i] += len(tok)
        return [''.join(x) for x in target]

    def add_three_line_title(self, title: str,
                             start: float = 0.0,
                             duration: Optional[float] = None,
                             *,
                             transform_y: float = 0.72,
                             line_spacing: int = 4,
                             highlight_color: Tuple[float, float, float] = (1.0, 0.7529411765, 0.2470588235),
                             track_name: str = "标题字幕轨道") -> draft.TextSegment:
        """添加三行标题：中间一行高亮。
        - 字体：俪金黑；字号：15；左对齐；max_line_width=0.6；自动换行
        - transform_y=0.72；行间距可配
        """
        if not self.script:
            raise ValueError("请先创建草稿")

        lines = self._split_title_to_three_lines(title)
        # 保障三行
        while len(lines) < 3:
            lines.append("")
        text = "\n".join(lines[:3])

        # 计算时间
        if duration is None:
            base = self.project_duration or self.audio_duration or 5.0
            duration = max(1.0, min(base, base))

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
            trange(tim(f"{start}s"), tim(f"{duration}s")),
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

        # 确保轨道（按调用顺序设置层级）
        try:
            _ = self.script.tracks[track_name]
        except KeyError:
            # 计算下一个可用的相对索引（基于现有轨道数量）
            existing_text_tracks = [name for name in self.script.tracks.keys() 
                                  if self.script.tracks[name].track_type == TrackType.text]
            next_index = len(existing_text_tracks) + 1
            self.script.add_track(TrackType.text, track_name, relative_index=next_index)

        self.script.add_segment(seg, track_name=track_name)
        print(f"[OK] 三行标题已添加到 {track_name}: {lines}")
        return seg

    def _update_project_duration(self):
        """更新项目总时长，取音视频中的最长者"""
        self.project_duration = max(self.audio_duration, self.video_duration)
        if self.project_duration > 0:
            print(f"[INFO] 项目总时长更新为: {self.project_duration:.1f} 秒 (音频: {self.audio_duration:.1f}s, 视频: {self.video_duration:.1f}s)")
        
    def download_material(self, url: str, local_path: str) -> str:
        """下载网络素材到本地
        
        Args:
            url: 素材URL
            local_path: 本地保存路径
            
        Returns:
            本地文件路径（如果下载成功）或原始URL（如果下载失败）
        """
        if not url or url.startswith('file://') or os.path.exists(url):
            return url
            
        try:
            print(f"[DEBUG] 尝试下载: {url} -> {local_path}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[DEBUG] 下载成功: {local_path}")
            return local_path
        except Exception as e:
            print(f"[DEBUG] 下载失败: {url}, 错误: {e}")
            print(f"[DEBUG] 返回原始URL: {url}")
            return url  # 返回原URL，让用户处理
    
    def create_draft(self, width: int = 1080, height: int = 1920, fps: int = 30):
        """创建剪映草稿
        
        Args:
            width: 视频宽度
            height: 视频高度  
            fps: 帧率
        """
        try:
            self.script = self.draft_folder.create_draft(
                self.project_name, width, height, allow_replace=True
            )
        except PermissionError as e:
            # 可能存在 .locked 文件或草稿被占用；回退为时间戳新名称避免冲突
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fallback_name = f"{self.project_name}_{ts}"
            print(f"[WARN] 发现锁定文件或占用，切换到新项目名称: {fallback_name}")
            self.project_name = fallback_name
            self.script = self.draft_folder.create_draft(
                self.project_name, width, height, allow_replace=False
            )
        except Exception as e:
            # 其他异常也尝试使用时间戳新名称
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fallback_name = f"{self.project_name}_{ts}"
            print(f"⚠️  创建草稿失败({e})，改用新项目名称: {fallback_name}")
            self.project_name = fallback_name
            self.script = self.draft_folder.create_draft(
                self.project_name, width, height, allow_replace=False
            )
        
        # 添加基础轨道（通过调用顺序控制层级，索引递增）
        self.script.add_track(TrackType.video, "主视频轨道", relative_index=1)
        self.script.add_track(TrackType.video, "数字人视频轨道", relative_index=2)  
        self.script.add_track(TrackType.audio, "音频轨道", relative_index=3)
        self.script.add_track(TrackType.audio, "背景音乐轨道", relative_index=4)
        # 文本类：按调用顺序设置层级
        self.script.add_track(TrackType.text, "内容字幕轨道", relative_index=5)
        self.script.add_track(TrackType.text, "标题字幕轨道", relative_index=6)
        
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
        total_video_duration = 0
        
        for i, (video_url, timeline) in enumerate(zip(video_urls, timelines)):
            # 下载视频到本地
            local_video_path = self.download_material(
                video_url, 
                f"temp_materials/video_{i}.mp4"
            )
            
            # 保存素材视频路径（只保存第一个）
            if i == 0:
                self.material_video_path = local_video_path
            
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
            
            # 累计视频时长
            total_video_duration += duration
            
        # 更新视频总时长
        self.video_duration = total_video_duration
        self._update_project_duration()
        print(f"[INFO] 视频总时长: {self.video_duration:.1f} 秒")
            
        return video_segments
    
    def add_digital_human_video(self, digital_video_url: str, duration: int = None, remove_pauses: bool = False,
                               min_pause_duration: float = 0.2, max_word_gap: float = 0.8):
        """添加数字人视频
        
        Args:
            digital_video_url: 数字人视频URL
            duration: 持续时长(秒)，如果不指定则使用整个视频
            remove_pauses: 是否移除视频中的音频停顿，默认False
            min_pause_duration: 最小停顿时长(秒)，默认0.2秒
            max_word_gap: 单词间最大间隔(秒)，默认0.8秒
        """
        # 检查是否已经手动处理过多片段
        if hasattr(self, 'skip_normal_processing') and self.skip_normal_processing:
            print(f"[DEBUG] 跳过正常的数字人视频处理，因为已经手动添加了多片段")
            # 重置标志
            self.skip_normal_processing = False
            return None
        if not self.script:
            raise ValueError("请先创建草稿")
            
        # 下载数字人视频（使用唯一文件名）
        digital_video_local_path = self._generate_unique_filename("digital_human")
        local_path = self.download_material(
            digital_video_url,
            digital_video_local_path
        )
        
        # 如果需要移除停顿，处理视频中的音频
        if remove_pauses and self.volcengine_asr:
            print("[DEBUG] 开始处理视频中的音频停顿移除...")
            
            # 1. 提取视频中的音频
            temp_audio_path = self._generate_unique_filename("video_audio", ".mp3")
            try:
                # 使用FFmpeg提取音频
                subprocess.run([
                    'ffmpeg', '-i', local_path, '-q:a', '0', '-map', 'a', temp_audio_path, '-y'
                ], check=True, capture_output=True)
                print(f"[DEBUG] 音频提取成功: {temp_audio_path}")
                
                # 2. 使用ASR处理音频停顿
                asr_result = self.volcengine_asr.transcribe_audio_for_silence_detection(digital_video_url)
                
                if asr_result:
                    # 3. 分析停顿段落
                    pause_detector = ASRSilenceDetector(min_pause_duration, max_word_gap)
                    pause_segments = pause_detector.detect_pauses_from_asr(asr_result)
                    
                    # 4. 生成原始字幕
                    subtitle_objects = self.volcengine_asr.parse_result_to_subtitles(asr_result)
                    self.original_subtitles = subtitle_objects
                    
                    if pause_segments:
                        print(f"[DEBUG] 检测到 {len(pause_segments)} 个停顿段落")
                        
                        # 5. 处理音频停顿
                        processed_audio_path = self._process_audio_pauses_with_asr_result(
                            temp_audio_path, asr_result, pause_segments, 
                            min_pause_duration, max_word_gap
                        )
                        
                        if processed_audio_path:
                            # 6. 调整字幕时间轴
                            adjusted_subtitles = self._adjust_subtitle_timings(
                                subtitle_objects, pause_segments
                            )
                            self.adjusted_subtitles = adjusted_subtitles
                            self.original_subtitles = subtitle_objects
                            
                            # 7. 使用视频片段切割方式处理停顿（保持原始视频质量）
                            processed_video_segments = self._process_video_pauses_by_segmentation(
                                local_path, "", pause_segments
                            )
                            
                            if len(processed_video_segments) == 1:
                                # 只有一个片段，直接使用
                                local_path = processed_video_segments[0]
                                print(f"[OK] 视频停顿移除完成（保持原始质量），新视频: {local_path}")
                            else:
                                # 多个片段：统一添加所有片段到数字人视频轨道
                                print(f"[OK] 视频停顿移除完成，生成 {len(processed_video_segments)} 个片段")
                                print(f"[DEBUG] 统一添加所有片段到数字人视频轨道")
                                
                                # 暂时禁用自动时长计算，我们手动管理
                                temp_adjusted_subtitles = self.adjusted_subtitles
                                self.adjusted_subtitles = None  # 临时禁用字幕时长计算
                                
                                # 统一添加所有片段
                                current_time_offset = 0
                                total_duration = 0
                                
                                for i, segment_path in enumerate(processed_video_segments):
                                    try:
                                        # 获取片段实际时长
                                        probe_cmd = [
                                            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                                            '-of', 'csv=p=0', segment_path
                                        ]
                                        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
                                        segment_duration = float(result.stdout.strip())
                                        
                                        print(f"[DEBUG] 添加片段 {i+1}: {segment_path} (时长: {segment_duration:.3f}s, 时间偏移: {current_time_offset:.3f}s)")
                                        
                                        # 直接创建视频片段并添加到数字人视频轨道
                                        video_material = draft.VideoMaterial(segment_path)
                                        
                                        # 创建视频片段
                                        # target_timerange: 在轨道上的位置（从 current_time_offset 开始）
                                        # source_timerange: 从素材中截取的范围（从 0 开始，因为已经切割好了）
                                        # 使用素材的实际时长而不是计算时长，避免精度问题
                                        material_duration = video_material.duration / 1000000  # 转换为秒
                                        video_segment = draft.VideoSegment(
                                            video_material,
                                            trange(tim(f"{current_time_offset}s"), tim(f"{material_duration}s")),
                                            source_timerange=trange(tim("0s"), tim(f"{material_duration}s"))
                                        )
                                        
                                        # 添加到数字人视频轨道
                                        self.script.add_segment(video_segment, track_name="数字人视频轨道")
                                        
                                        print(f"[DEBUG] 视频片段 {i+1} 已添加到数字人视频轨道，时间位置: {current_time_offset:.3f}s-{current_time_offset+material_duration:.3f}s")
                                        
                                        # 更新时间偏移和总时长
                                        current_time_offset += material_duration
                                        total_duration += material_duration
                                        
                                    except Exception as e:
                                        print(f"[ERROR] 添加视频片段 {i+1} 失败: {e}")
                                
                                print(f"[DEBUG] 所有片段添加完成，总时长: {total_duration:.3f}s")
                                
                                # 恢复字幕设置
                                self.adjusted_subtitles = temp_adjusted_subtitles
                                
                                # 设置第一个片段路径（用于兼容性）
                                local_path = processed_video_segments[0]
                                
                                # 手动更新视频时长
                                self.video_duration = total_duration
                                print(f"[DEBUG] 手动更新视频时长为: {total_duration:.3f}s")
                                
                                # 更新项目时长
                                self._update_project_duration()
                                
                                # 设置标志，表示已经手动添加了所有片段，需要跳过正常的 add_digital_human_video 逻辑
                                self.skip_normal_processing = True
                            
                            # 8. 添加调整后的字幕到视频
                            if adjusted_subtitles:
                                print(f"[DEBUG] 添加调整后的字幕到视频: {len(adjusted_subtitles)} 段")
                                print(f"[DEBUG] 打印去除停顿后的字幕信息:")
                                for i, subtitle in enumerate(adjusted_subtitles):
                                    print(f"  字幕{i+1}: [{subtitle['start']:.3f}s-{subtitle['end']:.3f}s] {subtitle['text']}")
                                
                                # 提取关键词用于高亮
                                all_text = " ".join([sub['text'] for sub in adjusted_subtitles])
                                keywords = self.volcengine_asr.extract_keywords_with_ai(all_text, max_keywords=8)
                                
                                if keywords:
                                    print(f"[OK] 视频字幕提取到 {len(keywords)} 个关键词: {keywords}")
                                else:
                                    print("[WARN] 视频字幕未提取到关键词")
                                
                                # 清理现有的字幕轨道以避免重叠
                                self._clear_caption_tracks()
                                
                                # 添加字幕（带关键词高亮）
                                self.add_captions(adjusted_subtitles, track_name="内容字幕轨道", position="bottom",
                                                keywords=keywords, 
                                                base_color=(1.0, 1.0, 1.0),  # 白色
                                                base_font_size=8.0,  # 8号
                                                font_type=draft.FontType.俪金黑,  # 俪金黑
                                                highlight_size=10.0,  # 高亮10号
                                                highlight_color=(1.0, 0.7529411765, 0.2470588235),  # #ffc03f
                                                scale=1.39)  # 缩放1.39
                                
                                # 为字幕添加背景色块
                                self.add_caption_backgrounds(adjusted_subtitles, position="bottom", 
                                                           bottom_transform_y=-0.3, scale=1.39)
                                
                                print(f"[OK] 调整后的字幕已添加到视频（含关键词高亮和背景色块）")
                        else:
                            print("[WARN] 音频停顿处理失败，使用原始视频")
                    else:
                        print("[DEBUG] 未检测到需要移除的停顿")
                else:
                    print("[WARN] ASR识别失败，跳过停顿移除")
                    
            except Exception as e:
                print(f"[WARN] 视频音频停顿处理失败: {e}")
        
        # 保存数字人视频路径
        self.digital_video_path = local_path
        
        # 检查是否已经手动处理过多片段
        if hasattr(self, 'skip_normal_processing') and self.skip_normal_processing:
            print(f"[DEBUG] 跳过正常的数字人视频片段添加，因为已经手动添加了多片段")
            # 重置标志
            self.skip_normal_processing = False
            return None
        
        # 获取视频素材信息
        video_material = draft.VideoMaterial(local_path)
        
        # 如果没有指定持续时长，使用整个视频
        if duration is None:
            duration_microseconds = video_material.duration
            duration_seconds = duration_microseconds / 1000000
            
            # 如果进行了停顿移除，使用处理后的音频时长
            if remove_pauses and hasattr(self, 'adjusted_subtitles') and self.adjusted_subtitles:
                # 计算处理后的总时长
                if self.adjusted_subtitles:
                    processed_duration = self.adjusted_subtitles[-1]['end']
                    print(f"[DEBUG] 使用停顿移除后的时长: {processed_duration:.1f} 秒 (原始: {duration_seconds:.1f} 秒)")
                    
                    # 确保不超过原始视频时长
                    if processed_duration <= duration_seconds:
                        duration_seconds = processed_duration
                        duration_microseconds = tim(f"{duration_seconds}s")
                        print(f"[DEBUG] 使用处理后的时长: {duration_seconds:.1f}s")
                    else:
                        print(f"[WARN] 处理后时长({processed_duration:.1f}s)超过原始视频时长({duration_seconds:.1f}s)，使用原始时长")
                        duration_microseconds = tim(f"{duration_seconds}s")
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
        print(f"[INFO] 数字人视频时长: {duration_seconds:.1f} 秒")
        
        self._update_project_duration()
        
        return digital_segment
    
    def add_audio(self, audio_url: str, duration: int = None, volume: float = 1.0, remove_pauses: bool = False,
                  min_pause_duration: float = 0.2, max_word_gap: float = 0.8):
        """添加音频
        
        Args:
            audio_url: 音频URL
            duration: 持续时长(秒)，如果为None则使用整个音频，如果有视频则限制为视频时长
            volume: 音量(0-1)
            remove_pauses: 是否自动移除停顿，默认False
            min_pause_duration: 最小停顿时长(秒)，默认0.2秒
            max_word_gap: 单词间最大间隔(秒)，默认0.8秒
        """
        if not self.script:
            raise ValueError("请先创建草稿")
        
        # 保存原始URL用于ASR处理
        original_audio_url = audio_url
        print(f"[DEBUG] 原始音频URL: {original_audio_url}")
        
        # 新的集成方案：先进行ASR识别，再处理停顿
        asr_result = None
        pause_segments = []
        subtitle_objects = []
        
        print(f"[DEBUG] remove_pauses参数: {remove_pauses}")
        print(f"[DEBUG] self.volcengine_asr是否存在: {self.volcengine_asr is not None}")
        
        if remove_pauses and self.volcengine_asr:
            print(f"[DEBUG] 开始集成方案：先ASR识别，再处理停顿")
            
            # 1. 先用原始URL进行ASR识别
            print(f"[DEBUG] 步骤1：使用原始URL进行ASR识别")
            asr_result = self.volcengine_asr.transcribe_audio_for_silence_detection(original_audio_url)
            
            if asr_result:
                print(f"[DEBUG] ASR识别成功，开始分析停顿")
                
                # 2. 分析停顿段落
                pause_detector = ASRSilenceDetector(min_pause_duration, max_word_gap)
                pause_segments = pause_detector.detect_pauses_from_asr(asr_result)
                
                # 3. 生成原始字幕
                subtitle_objects = self.volcengine_asr.parse_result_to_subtitles(asr_result)
                
                print(f"[DEBUG] 检测到 {len(pause_segments)} 个停顿段落")
                print(f"[DEBUG] 生成 {len(subtitle_objects)} 段原始字幕")
                
                # 4. 如果有停顿，下载音频并进行处理
                if pause_segments:
                    print(f"[DEBUG] 步骤2：下载音频并移除停顿")
                    
                    # 下载音频到本地（使用唯一文件名）
                    audio_local_path = self._generate_unique_filename("audio", ".mp3")
                    local_path = self.download_material(
                        audio_url,
                        audio_local_path
                    )
                    
                    if local_path != original_audio_url:
                        # 下载成功，处理停顿
                        if not os.path.isabs(local_path):
                            local_path = os.path.abspath(local_path)
                        
                        print(f"[DEBUG] 音频下载成功: {local_path}")
                        
                        # 处理音频停顿
                        processed_audio_path = self._process_audio_pauses_with_asr_result(
                            local_path, asr_result, pause_segments, min_pause_duration, max_word_gap
                        )
                        
                        if processed_audio_path:
                            local_path = processed_audio_path
                            print(f"[DEBUG] 音频停顿处理完成: {local_path}")
                            
                            # 5. 重新计算字幕时间轴
                            adjusted_subtitles = self._adjust_subtitle_timings(
                                subtitle_objects, pause_segments
                            )
                            print(f"[DEBUG] 字幕时间轴调整完成，{len(adjusted_subtitles)} 段字幕")
                            
                            # 保存调整后的字幕供后续使用
                            self.adjusted_subtitles = adjusted_subtitles
                            self.original_subtitles = subtitle_objects
                        else:
                            print("[DEBUG] 音频停顿处理失败，使用原始音频")
                    else:
                        print("[DEBUG] 音频下载失败，跳过停顿移除")
                        local_path = original_audio_url
                else:
                    print("[DEBUG] 未检测到停顿，跳过停顿移除")
                    # 下载音频但不处理停顿（使用唯一文件名）
                    audio_local_path = self._generate_unique_filename("audio", ".mp3")
                    local_path = self.download_material(audio_url, audio_local_path)
                    self.adjusted_subtitles = subtitle_objects
                    self.original_subtitles = subtitle_objects
            else:
                print("[DEBUG] ASR识别失败，回退到原始方案")
                remove_pauses = False  # 禁用停顿移除，使用原始流程
                audio_local_path = self._generate_unique_filename("audio", ".mp3")
                local_path = self.download_material(audio_url, audio_local_path)
        else:
            # 不需要移除停顿或ASR未初始化，使用原始流程
            if not self.volcengine_asr:
                print(f"[DEBUG] ASR未初始化，使用原始流程")
            if not remove_pauses:
                print(f"[DEBUG] remove_pauses=False，使用原始流程")
            print(f"[DEBUG] 使用原始流程：下载音频")
            audio_local_path = self._generate_unique_filename("audio", ".mp3")
            local_path = self.download_material(audio_url, audio_local_path)
        
        # 处理本地路径
        if local_path != original_audio_url:
            if not os.path.isabs(local_path):
                local_path = os.path.abspath(local_path)
            
            if os.path.exists(local_path):
                print(f"[DEBUG] 本地音频文件大小: {os.path.getsize(local_path)} bytes")
            else:
                print(f"[ERROR] 音频文件不存在: {local_path}")
                raise FileNotFoundError(f"音频文件不存在: {local_path}")
        
        print(f"[DEBUG] 最终音频路径: {local_path}")
        
        # 获取音频素材信息
        audio_material = draft.AudioMaterial(local_path)
        actual_audio_duration = audio_material.duration / 1000000  # 转换为秒
        
        print(f"[DEBUG] 实际音频时长: {actual_audio_duration:.1f} 秒")
        
        # 如果进行了停顿移除，更新音频时长
        if hasattr(self, 'adjusted_subtitles') and self.adjusted_subtitles and remove_pauses:
            print(f"[DEBUG] 检测到停顿移除，使用处理后的音频时长: {actual_audio_duration:.1f} 秒")
            original_audio_duration = actual_audio_duration
        else:
            original_audio_duration = actual_audio_duration
        
        # 确定实际音频时长
        if duration is None:
            # 如果有视频，音频时长不应超过视频时长
            if self.video_duration > 0:
                actual_duration = min(original_audio_duration, self.video_duration)
                if original_audio_duration > self.video_duration:
                    print(f"[WARN] 音频时长({original_audio_duration:.1f}s)超过视频时长({self.video_duration:.1f}s)，将截取至视频时长")
            else:
                actual_duration = original_audio_duration
        else:
            # 如果有视频，检查指定时长是否超过视频时长
            if self.video_duration > 0 and duration > self.video_duration:
                actual_duration = self.video_duration
                print(f"[WARN] 指定音频时长({duration:.1f}s)超过视频时长({self.video_duration:.1f}s)，将截取至视频时长")
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
        
          
        # 清除现有音频段以避免重叠
        try:
            audio_tracks = [track for track in self.script.main_track.tracks if track.track_type == TrackType.AUDIO]
            for track in audio_tracks:
                if track.segments:
                    track.segments.clear()
                    print("[DEBUG] 已清除现有音频段")
        except Exception as e:
            print(f"[WARN] 清除音频段失败: {e}")
        
        # 添加到音频轨道
        self.script.add_segment(audio_segment, track_name="音频轨道")
        
        # 更新项目时长
        self._update_project_duration()
        print(f"[INFO] 音频时长: {self.audio_duration:.1f} 秒")
        
        return audio_segment
    
    def add_background_music(self, music_path: str, target_duration: float = None, volume: float = 0.3):
        """添加背景音乐
        
        Args:
            music_path: 背景音乐文件路径（本地路径）
            target_duration: 目标时长（秒），如果None则使用项目总时长（音视频中最长者）
            volume: 音量(0-1)，默认0.3比较适合背景音乐
        """
        if not self.script:
            raise ValueError("请先创建草稿")
            
        if not os.path.exists(music_path):
            raise ValueError(f"背景音乐文件不存在: {music_path}")
        
        # 获取背景音乐素材信息
        bg_music_material = draft.AudioMaterial(music_path)
        
        # 确定目标时长 - 优先使用项目总时长确保音视频同步
        if target_duration is None:
            if self.project_duration > 0:
                target_duration = self.project_duration
                print(f"[INFO] 背景音乐将使用项目总时长: {target_duration:.1f}s (确保与音视频同步)")
            elif self.video_duration > 0:
                target_duration = self.video_duration
                print(f"[INFO] 背景音乐将使用视频时长: {target_duration:.1f}s")
            elif self.audio_duration > 0:
                target_duration = self.audio_duration
                print(f"[INFO] 背景音乐将使用音频时长: {target_duration:.1f}s")
            else:
                raise ValueError("无法确定目标时长，请先添加音频或视频，或指定target_duration")
        
        target_duration_microseconds = tim(f"{target_duration}s")
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
            # 添加淡入淡出已移除
            # 添加到背景音乐轨道
            self.script.add_segment(bg_music_segment, track_name="背景音乐轨道")
            print(f"[INFO] 背景音乐已添加: {os.path.basename(music_path)}，截取时长: {target_duration:.1f}s，音量: {volume}")
        else:
            # 背景音乐太短，需要循环
            print(f"[INFO] 背景音乐时长 {bg_music_duration_seconds:.1f}s，目标时长 {target_duration:.1f}s，将循环播放")
            
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
                    trange(tim(f"{current_time}s"), tim(f"{current_duration}s")),
                    volume=volume
                )
                
                # 为第一个和最后一个片段添加淡入淡出
                # 第一个片段淡入已移除
                # 最后一个片段淡出已移除
                
                # 添加到背景音乐轨道
                self.script.add_segment(loop_segment, track_name="背景音乐轨道")
                
                current_time += current_duration
            
            print(f"[INFO] 背景音乐循环已添加: {os.path.basename(music_path)}，{loop_count}次循环，总时长: {target_duration:.1f}s，音量: {volume}")
        
        return
    
    def add_styled_text_with_background(self, text_content: str, timerange_start: float, timerange_duration: float,
                                       track_name: str = "标题字幕轨道", position: str = "center",
                                       background_style: Dict[str, Any] = None,
                                       text_transform_y: Optional[float] = None,
                                       line_spacing: int = 0,
                                       bg_height: Optional[float] = None) -> draft.TextSegment:
        """添加带背景的样式化文本
        
        Args:
            text_content: 文本内容（支持换行符\\n）
            timerange_start: 开始时间（秒）
            timerange_duration: 持续时间（秒）
            track_name: 轨道名称
            position: 文本位置 ("top"顶部, "center"中间, "bottom"底部)
            background_style: 背景样式参数字典
            text_transform_y: 文本片段的transform_y（-1.0~1.0）。传入则覆盖position映射。
            line_spacing: 行间距（与剪映一致的整数单位，默认0）。
            bg_height: 背景高度比例（0.0-1.0）。传入则覆盖 background_style["height"]。
            
        Returns:
            创建的文本片段
        """
        if not self.script:
            raise ValueError("请先创建草稿")
        
        # 默认背景样式（根据您提供的截图参数）
        if background_style is None:
            background_style = {
                "color": "#000000",      # 黑色
                "alpha": 0.67,           # 67% 不透明度
                "height": 0.31,          # 31% 高度
                "width": 0.14,           # 14% 宽度  
                "horizontal_offset": 0.5, # 50% 左右间隙
                "vertical_offset": 0.5,   # 50% 上下间隙
                "round_radius": 0.0,     # 圆角半径
                "style": 1               # 背景样式
            }
        
        # 根据位置设置垂直偏移（transform_y），可被text_transform_y覆盖
        if position == "top":
            transform_y = 0.4
        elif position == "center":
            transform_y = 0.0
        else:  # bottom
            transform_y = -0.4
        if text_transform_y is not None:
            # 支持整数输入：若为-100~100按百分比映射到-1~1；若已在-1~1内则直接使用
            ty = float(text_transform_y)
            if isinstance(text_transform_y, int) and abs(ty) > 1:
                ty = ty / 100.0
            transform_y = max(-1.0, min(1.0, ty))
        
        # 覆盖背景高度（若提供）
        if bg_height is not None:
            background_style["height"] = float(bg_height)

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
            line_spacing=line_spacing
        )
        
        # 创建文本片段
        text_segment = draft.TextSegment(
            text_content,
            trange(tim(f"{timerange_start}s"), tim(f"{timerange_duration}s")),
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
        
        # 确保目标轨道存在（若不存在则自动创建为文本轨道，按调用顺序设置层级）
        try:
            _ = self.script.tracks[track_name]
        except KeyError:
            # 计算下一个可用的相对索引（基于现有轨道数量）
            existing_text_tracks = [name for name in self.script.tracks.keys() 
                                  if self.script.tracks[name].track_type == TrackType.text]
            next_index = len(existing_text_tracks) + 1
            self.script.add_track(TrackType.text, track_name, relative_index=next_index)

        # 添加到轨道
        self.script.add_segment(text_segment, track_name=track_name)
        
        print(f"[OK] 带背景的文本已添加: '{text_content[:20]}...' 到 {track_name}")
        print(f"   背景: {background_style['color']} {background_style['alpha']*100:.0f}% 透明度")
        print(f"   位置: {position}, 时长: {timerange_duration:.1f}秒")
        
        return text_segment
    
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
                print("[ERROR] 火山引擎ASR未初始化，无法进行转录")
                return []
            
            # 使用火山引擎ASR进行转录
            subtitle_objects = self.volcengine_asr.process_audio_file(audio_url)
            
            if subtitle_objects:
                print(f"[OK] 火山引擎转录完成，生成 {len(subtitle_objects)} 段字幕")
                
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
                print(f"[INFO] 统计: {len(subtitle_objects)}段, 总时长{total_duration:.1f}秒, 平均{total_duration/len(subtitle_objects):.1f}秒/段")
                
                return subtitle_objects
            else:
                print("[ERROR] 火山引擎转录失败")
                return []
                
        except Exception as e:
            print(f"[ERROR] 音频转录过程中出错: {e}")
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
        
        print(f"[OK] 字幕时间调整完成")
        return adjusted_subtitles
    
    def _clear_caption_tracks(self):
        """清理现有的字幕轨道以避免重叠"""
        try:
            # 查找所有字幕轨道
            caption_track_names = []
            for track_name, track in self.script.tracks.items():
                if hasattr(track, 'track_type') and track.track_type == TrackType.text:
                    caption_track_names.append(track_name)
            
            print(f"[DEBUG] 找到 {len(caption_track_names)} 个字幕轨道需要清理: {caption_track_names}")
            
            # 清理每个字幕轨道中的段
            for track_name in caption_track_names:
                track = self.script.tracks[track_name]
                if hasattr(track, 'segments') and track.segments:
                    print(f"[DEBUG] 清理字幕轨道 '{track_name}' 中的 {len(track.segments)} 个段")
                    track.segments.clear()
                    print(f"[OK] 字幕轨道 '{track_name}' 已清理")
            
        except Exception as e:
            print(f"[WARN] 清理字幕轨道时出错: {e}")
    
    
    def add_captions(self, caption_data: List[Dict[str, Any]] = None,
                    track_name: str = "内容字幕轨道", position: str = "bottom",
                    keywords: List[str] = None,
                    base_font_size: float = 8.0,
                    base_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
                    font_type: Optional[draft.FontType] = None,
                    highlight_color: Tuple[float, float, float] = (1.0, 0.7529411765, 0.2470588235),
                    highlight_size: float = 10.0,
                    bottom_transform_y: float = -0.3,
                    scale: float = 1.39):
        """添加字幕，支持关键词高亮
        
        Args:
            caption_data: 字幕数据列表，每个元素包含text, start, end等信息。
                       如果为None，会使用停顿移除时生成的调整后字幕
            font_size: 字体大小
            track_name: 轨道名称
            position: 字幕位置 ("top"顶部, "bottom"底部)
            keywords: 需要高亮的关键词列表
            keyword_color: 关键词高亮颜色，默认为黄色
        """
        if not self.script:
            raise ValueError("请先创建草稿")
        
        # 如果没有提供字幕数据，尝试使用调整后的字幕
        if caption_data is None:
            if hasattr(self, 'adjusted_subtitles') and self.adjusted_subtitles:
                caption_data = self.adjusted_subtitles
                print(f"[DEBUG] 使用调整后的字幕: {len(caption_data)} 段")
            else:
                print("[DEBUG] 没有可用的字幕数据")
                return
        
        # 清理现有的字幕轨道以避免重叠
        self._clear_caption_tracks()
            
        text_segments = []
        
        for caption in caption_data:
            text = caption.get('text', '')
            start_time = caption.get('start', 0)  # 秒
            end_time = caption.get('end', start_time + 2)  # 秒
            
            if not text:
                continue
                
            # 根据位置设置不同的垂直位置
            if position == "top":
                transform_y = 0.4
                text_color = base_color
            else:
                transform_y = bottom_transform_y
                text_color = base_color
                
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
                font=(font_type if font_type is not None else draft.FontType.俪金黑),
                style=draft.TextStyle(
                    color=text_color,
                    size=base_font_size,
                    auto_wrapping=True,
                    bold=True,
                    align=0,
                    max_line_width=0.82
                ),
                clip_settings=draft.ClipSettings(transform_y=transform_y, scale_x=scale, scale_y=scale)
            )

            # 外部传入的关键词高亮：按给定颜色与字号
            if current_keywords:
                for kw in current_keywords:
                    start_idx = 0
                    while True:
                        pos = text.find(kw, start_idx)
                        if pos == -1:
                            break
                        end_idx = pos + len(kw)
                        try:
                            text_segment.add_highlight(pos, end_idx, color=highlight_color, size=highlight_size, bold=True)
                        except Exception:
                            pass
                        start_idx = pos + 1
            
            # 如果有关键词被高亮，打印调试信息
            if current_keywords:
                print(f"   [INFO] '{text}' 中高亮关键词: {current_keywords}")
            
            text_segments.append(text_segment)
            self.script.add_segment(text_segment, track_name=track_name)
            
        return text_segments
    
    def add_caption_backgrounds(self, caption_data: List[Dict[str, Any]], 
                               position: str = "bottom",
                               bottom_transform_y: float = -0.3,
                               scale: float = 1.39,
                               background_style: Dict[str, Any] = None):
        """为字幕添加背景色块（独立功能，全程显示一个背景，复用标题背景方法）
        
        Args:
            caption_data: 字幕数据列表，用于计算总时长
            position: 字幕位置 ("top"顶部, "bottom"底部)
            bottom_transform_y: 底部位置的transform_y
            scale: 缩放比例
            background_style: 背景样式参数
        """
        if not self.script:
            raise ValueError("请先创建草稿")
        
        if not caption_data:
            return None
        
        # 默认背景样式（参考标题背景样式，但高度调整为适合字幕）
        if background_style is None:
            background_style = {
                "color": "#000000",      # 黑色
                "alpha": 0.67,           # 67% 不透明度
                "height": 0.25,          # 25% 高度（比标题背景稍小）
                "width": 0.14,           # 14% 宽度  
                "horizontal_offset": 0.5, # 50% 左右间隙
                "vertical_offset": 0.5,   # 50% 上下间隙
                "round_radius": 0.0,     # 圆角半径
                "style": 1               # 背景样式
            }
        
        # 计算字幕的总时长（从第一个字幕开始到最后一个字幕结束）
        start_time = min(caption.get('start', 0) for caption in caption_data)
        end_time = max(caption.get('end', 0) for caption in caption_data)
        total_duration = end_time - start_time
        
        # 根据位置设置不同的垂直位置
        if position == "top":
            transform_y = 0.4
        else:
            transform_y = bottom_transform_y
        
        # 创建背景文本片段（使用占位符确保背景显示）
        placeholder_text = " " * 50  # 使用固定长度的占位符
        
        # 复用 add_styled_text_with_background 方法，创建全程显示的背景
        bg_segment = self.add_styled_text_with_background(
            text_content=placeholder_text,
            timerange_start=start_time,
            timerange_duration=total_duration,
            track_name="内容字幕背景",
            position=position,
            background_style=background_style,
            text_transform_y=transform_y,
            line_spacing=0,
            bg_height=background_style["height"]
        )
        
        return bg_segment
    
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
                - background_music_path: 背景音乐文件路径 (可选)
                - background_music_volume: 背景音乐音量 (默认0.3)
                
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
        background_music_path = inputs.get('background_music_path')  # 背景音乐路径
        background_music_volume = inputs.get('background_music_volume', 0.3)  # 背景音乐音量
        
        # 验证必需参数
        if not audio_url:
            raise ValueError("audio_url 是必需参数，用于音频转录")
        
        print(f"[INFO] 音频转录字幕工作流 + AI关键词高亮")
        print(f"[INFO] 音频URL: {audio_url}")
        print(f"[INFO] 字幕延迟: {subtitle_delay:.1f}秒")
        print(f"[INFO] 字幕速度: {subtitle_speed:.1f}x")
        print(f"[INFO] 火山引擎ASR (语音识别)")
        print(f"[INFO] 豆包API (关键词提取): {'已配置' if doubao_token else '未配置，将使用本地算法'}")
        
        # 初始化火山引擎ASR
        if volcengine_appid and volcengine_access_token:
            self.volcengine_asr = VolcengineASR(
                appid=volcengine_appid, 
                access_token=volcengine_access_token,
                doubao_token=doubao_token,
                doubao_model=doubao_model
            )
            print(f"[OK] 火山引擎ASR已初始化 (AppID: {volcengine_appid})")
            if doubao_token:
                print(f"[OK] 豆包API已配置 (Model: {doubao_model})")
        else:
            raise ValueError("必须提供 volcengine_appid 和 volcengine_access_token 参数")
        
        # 1. 创建草稿
        self.create_draft()
        
        # 2. 添加数字人视频（如果提供了音频URL，则直接处理视频中的音频）
        digital_video_url = inputs.get('digital_video_url')
        if digital_video_url:
            # 如果提供了音频URL，使用视频URL作为音频源进行处理
            if audio_url:
                print(f"[INFO] 使用视频音频进行停顿移除和字幕识别")
                # 直接使用视频URL进行音频处理，不需要单独的音频轨道
                self.add_digital_human_video(
                    digital_video_url, 
                    remove_pauses=True, 
                    min_pause_duration=0.2, 
                    max_word_gap=0.8
                )
            else:
                # 没有音频URL，正常添加视频
                self.add_digital_human_video(digital_video_url)
        
        # 3. 添加素材视频（如果有）
        material_video_url = inputs.get('material_video_url')
        if material_video_url:
            # 模拟时间轴数据
            timelines = [{'start': 0, 'end': 10}]  # 可以根据实际需求调整
            self.add_videos([material_video_url], timelines, volume=0.3)
        
        # 4.1. 视频音频停顿处理已完成，字幕已同步
        video_subtitles_added = False
        if hasattr(self, 'adjusted_subtitles') and self.adjusted_subtitles:
            print(f"[INFO] 视频音频停顿处理完成，字幕已同步")
            video_subtitles_added = True
        
        # 4.3. 添加背景音乐（如果提供）
        if background_music_path:
            print(f"[INFO] 准备添加背景音乐: {background_music_path}")
            try:
                self.add_background_music(background_music_path, volume=background_music_volume)
                print(f"[OK] 背景音乐已成功添加: {background_music_path}")
            except Exception as e:
                print(f"[ERROR] 背景音乐添加失败: {e}")
                import traceback
                print(f"错误详情: {traceback.format_exc()}")
        else:
            print("📋 未提供背景音乐路径，跳过背景音乐添加")

        # 4.8 添加一个三行文本并应用背景样式（位于画面中部）
        try:
            multiline_text = "                                                           \n\n "
            # 使用与截图一致的背景参数
            background_style = {
                "color": "#000000",      # 黑色
                "alpha": 0.67,           # 不透明度 67%
                "height": 1,          # 高度 31%
                "width": 1,           # 宽度 14%
                "horizontal_offset": 0.5, # 左右间隙 50%
                "vertical_offset": 0.5,   # 上下间隙 50%
                "round_radius": 0.0,
                "style": 1
            }
            # 背景时长与标题一致：使用项目总时长（或音频时长）
            display_duration = self.project_duration if self.project_duration > 0 else (self.audio_duration if self.audio_duration > 0 else 5.0)
            self.add_styled_text_with_background(
                text_content=multiline_text,
                timerange_start=0,
                timerange_duration=display_duration,
                track_name="标题字幕背景",
                position="center",
                background_style=background_style,
                text_transform_y=0.73,
                line_spacing=4,
                bg_height=0.48
            )
        except Exception as e:
            print(f"[ERROR] 添加三行背景文字失败: {e}")
        
        # 5. 生成音频转录字幕
        title = inputs.get('title', '')
        
        # 检查是否已经通过视频处理添加了字幕
        if video_subtitles_added and hasattr(self, 'adjusted_subtitles') and self.adjusted_subtitles:
            print(f"[INFO] 视频处理已添加字幕，跳过音频转录字幕添加")
            final_subtitles = self.adjusted_subtitles
        else:
            # 音频转录生成字幕
            print("🎤 开始音频转录生成字幕")
            subtitle_objects = self.transcribe_audio_and_generate_subtitles(audio_url)
            print(f"🔍 音频转录字幕: {subtitle_objects}")
            
            if subtitle_objects:
                print(f"[OK] 音频转录成功，生成 {len(subtitle_objects)} 段字幕")
                
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
                    print(f"[OK] AI提取到 {len(keywords)} 个关键词: {keywords}")
                    keyword_color = (1.0, 0.984313725490196, 0.7254901960784313)  # 黄色高亮
                else:
                    print("⚠️ 未提取到关键词，使用普通字幕")
                    keyword_color = None
                
                # 添加字幕到视频项目（带关键词高亮）
                self.add_captions(final_subtitles, track_name="内容字幕轨道", position="bottom",
                                keywords=keywords, 
                                base_color=(1.0, 1.0, 1.0),  # 白色
                                base_font_size=8.0,  # 8号
                                font_type=draft.FontType.俪金黑,  # 俪金黑
                                highlight_size=10.0,  # 高亮10号
                                highlight_color=(1.0, 0.7529411765, 0.2470588235),  # #ffc03f
                                scale=1.39)  # 缩放1.39
                
                # 为字幕添加背景色块（独立功能）
                self.add_caption_backgrounds(final_subtitles, position="bottom", 
                                           bottom_transform_y=-0.3, scale=1.39)
            else:
                print("[WARN] 音频转录失败，无法生成字幕")
                final_subtitles = []
        
        # 显示字幕添加结果
        if final_subtitles:
            print(f"\n已添加 {len(final_subtitles)} 段字幕到剪映项目")
            print("前3段预览:")
            for i, subtitle in enumerate(final_subtitles[:3], 1):
                start = subtitle['start']
                end = subtitle['end']
                text = subtitle['text']
                print(f"   {i}. [{start:.3f}s-{end:.3f}s] {text}")
            
            # 添加标题字幕（三行标题，第二行高亮）
            if title:
                title_duration = self.project_duration if self.project_duration > 0 else self.audio_duration
                print(f"添加三行标题: {title} (0s - {title_duration:.1f}s)")
                self.add_three_line_title(
                    title=title,
                    start=0.0,
                    duration=title_duration,
                    transform_y=0.72,
                    line_spacing=4,
                    highlight_color=(1.0, 0.7529411765, 0.2470588235),  # #ffc03f
                    track_name="标题字幕轨道"
                )
        else:
            print("[ERROR] 音频转录失败，无法生成字幕")
            raise ValueError("音频转录失败，请检查音频文件和API配置")
        
        # 6. 保存草稿
        self.script.save()
        
        return self.script.save_path
    
    def _remove_audio_pauses(self, original_audio_url: str, local_audio_path: str, min_pause_duration: float = 0.8, 
                           max_word_gap: float = 1.5) -> Optional[str]:
        """
        移除音频中的停顿
        
        Args:
            original_audio_url: 原始音频URL（用于ASR）
            local_audio_path: 本地音频文件路径（用于处理）
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
            
            # 使用ASR转录音频，直接使用原始URL
            print(f"[DEBUG] 使用原始音频URL进行ASR: {original_audio_url}")
            print(f"[DEBUG] original_audio_url type: {type(original_audio_url)}")
            print(f"[DEBUG] original_audio_url.startswith http: {original_audio_url.startswith('http')}")
            
            asr_result = self.volcengine_asr.transcribe_audio_for_silence_detection(original_audio_url)
            
            if not asr_result:
                print("⚠️  ASR转录失败，跳过停顿移除")
                return None
            
            # 创建临时输出文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                output_path = temp_file.name
            
            # 移除停顿
            result = self.silence_remover.remove_pauses_from_audio(
                local_audio_path, asr_result, output_path
            )
            
            if result['success']:
                pause_stats = result['pause_statistics']
                print(f"[OK] 停顿移除完成:")
                print(f"   - 移除停顿时长: {result['removed_duration']:.2f} 秒")
                print(f"   - 停顿次数: {pause_stats['pause_count']}")
                print(f"   - 平均停顿时长: {pause_stats['average_pause_duration']:.2f} 秒")
                print(f"   - 处理后音频时长: {result['processed_duration']:.2f} 秒")
                
                return output_path
            else:
                print("[ERROR] 停顿移除失败")
                # 清理临时文件
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
                
        except Exception as e:
            print(f"[ERROR] 停顿移除处理失败: {e}")
            return None
    
    def _remove_audio_video_pauses(self, original_audio_url: str, local_audio_path: str, video_path: str, 
                                 min_pause_duration: float = 0.8, max_word_gap: float = 1.5) -> Tuple[Optional[str], Optional[str]]:
        """
        同时移除音频和视频中的停顿
        
        Args:
            original_audio_url: 原始音频URL（用于ASR）
            local_audio_path: 本地音频文件路径（用于处理）
            video_path: 视频文件路径
            min_pause_duration: 最小停顿时长(秒)
            max_word_gap: 单词间最大间隔(秒)
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (处理后的音频路径, 处理后的视频路径)
        """
        if not self.volcengine_asr:
            print("⚠️  ASR未初始化，跳过音视频停顿移除")
            return None, None
        
        try:
            print("🔍 开始音视频停顿检测和移除...")
            
            # 初始化停顿移除器
            if not self.silence_remover:
                self.silence_remover = ASRBasedSilenceRemover(min_pause_duration, max_word_gap)
            
            # 使用ASR转录音频，直接使用原始URL
            print(f"[DEBUG] 使用原始音频URL进行ASR: {original_audio_url}")
            print(f"[DEBUG] original_audio_url type: {type(original_audio_url)}")
            print(f"[DEBUG] original_audio_url.startswith http: {original_audio_url.startswith('http')}")
            
            asr_result = self.volcengine_asr.transcribe_audio_for_silence_detection(original_audio_url)
            
            if not asr_result:
                print("⚠️  ASR转录失败，跳过音视频停顿移除")
                return None, None
            
            # 创建临时输出文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
                output_audio_path = temp_audio.name
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                output_video_path = temp_video.name
            
            # 同时移除音频和视频的停顿
            result = self.silence_remover.remove_pauses_from_audio_and_video(
                local_audio_path, video_path, asr_result, output_audio_path, output_video_path
            )
            
            if result['success']:
                pause_stats = result['pause_statistics']
                print(f"[OK] 音视频停顿移除完成:")
                print(f"   - 移除停顿时长: {result['removed_duration']:.2f} 秒")
                print(f"   - 停顿次数: {pause_stats['pause_count']}")
                print(f"   - 平均停顿时长: {pause_stats['average_pause_duration']:.2f} 秒")
                print(f"   - 处理后音频时长: {result['processed_duration']:.2f} 秒")
                
                return output_audio_path, output_video_path
            else:
                print("[ERROR] 音视频停顿移除失败")
                # 清理临时文件
                for path in [output_audio_path, output_video_path]:
                    if os.path.exists(path):
                        os.unlink(path)
                return None, None
                
        except Exception as e:
            print(f"[ERROR] 音视频停顿移除处理失败: {e}")
            return None, None
    
    def _process_audio_pauses_with_asr_result(self, local_audio_path: str, asr_result: Dict[str, Any], 
                                           pause_segments: List[Tuple[float, float]], 
                                           min_pause_duration: float = 0.2, 
                                           max_word_gap: float = 0.8) -> Optional[str]:
        """
        基于ASR结果处理音频停顿
        
        Args:
            local_audio_path: 本地音频文件路径
            asr_result: ASR识别结果
            pause_segments: 停顿段落列表
            min_pause_duration: 最小停顿时长
            max_word_gap: 最大单词间隔
            
        Returns:
            处理后的音频文件路径
        """
        try:
            print(f"[DEBUG] 开始基于ASR结果处理音频停顿")
            print(f"[DEBUG] 停顿段落数量: {len(pause_segments)}")
            
            # 计算有声段落
            total_duration = asr_result.get('duration', 0)
            speech_segments = []
            
            if pause_segments:
                # 构建有声段落
                current_time = 0.0
                
                for pause_start, pause_end in pause_segments:
                    if current_time < pause_start:
                        speech_segments.append((current_time, pause_start))
                    current_time = pause_end
                
                # 添加最后一段
                if current_time < total_duration:
                    speech_segments.append((current_time, total_duration))
            
            if not speech_segments:
                print("[DEBUG] 没有有声段落，返回原始音频")
                return local_audio_path
            
            print(f"[DEBUG] 有声段落数量: {len(speech_segments)}")
            
            # 使用FFmpeg提取有声段落
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                output_path = temp_file.name
            
            # 构建FFmpeg过滤图
            filter_complex = []
            
            for i, (start, end) in enumerate(speech_segments):
                duration = end - start
                filter_complex.append(f'[0:a]atrim=start={start}:duration={duration},asetpts=PTS-STARTPTS[a{i}]')
            
            # 拼接所有段落
            inputs = ''.join(f'[a{i}]' for i in range(len(speech_segments)))
            filter_complex.append(f'{inputs}concat=n={len(speech_segments)}:v=0:a=1[out]')
            
            cmd = [
                'ffmpeg',
                '-i', local_audio_path,
                '-filter_complex', ';'.join(filter_complex),
                '-map', '[out]',
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                # 计算移除的停顿时长
                removed_duration = sum(end - start for start, end in pause_segments)
                new_duration = sum(end - start for start, end in speech_segments)
                
                print(f"[DEBUG] 音频停顿处理完成:")
                print(f"   - 原始时长: {total_duration:.2f} 秒")
                print(f"   - 移除停顿: {removed_duration:.2f} 秒")
                print(f"   - 新时长: {new_duration:.2f} 秒")
                
                return output_path
            else:
                print(f"[DEBUG] FFmpeg处理失败: {result.stderr}")
                # 清理临时文件
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None
                
        except Exception as e:
            print(f"[DEBUG] 音频停顿处理失败: {e}")
            return None
    
    def _process_video_pauses_by_segmentation(self, input_video_path: str, output_video_path: str, pause_segments: List[Tuple[float, float]]) -> List[str]:
        """使用视频片段切割方式处理停顿（保持原始视频质量）
        
        按照用户建议的逻辑：切割掉不需要的中间片段，直接新增剩下的有效片段（不拼接）
        
        Args:
            input_video_path: 输入视频路径
            output_video_path: 输出视频路径（如果只有一个片段时使用）
            pause_segments: 需要移除的停顿时间段列表 [(start1, end1), (start2, end2), ...]
            
        Returns:
            List[str]: 切割后的有效视频片段路径列表
        """
        print(f"[DEBUG] 开始使用片段切割方式处理视频停顿")
        print(f"[DEBUG] 输入视频: {input_video_path}")
        print(f"[DEBUG] 需要移除的停顿段: {len(pause_segments)} 个")
        
        # 检查输入文件是否存在
        if not os.path.exists(input_video_path):
            print(f"[ERROR] 输入视频文件不存在: {input_video_path}")
            return []
        
        try:
            # 获取视频总时长
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', input_video_path
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            total_duration = float(result.stdout.strip())
            print(f"[DEBUG] 视频总时长: {total_duration:.3f} 秒")
            
            # 如果没有停顿段，直接返回原视频路径
            if not pause_segments:
                print("[DEBUG] 没有停顿段需要移除，返回原视频")
                return [input_video_path]
            
            # 第一步：处理和合并停顿片段（需要丢弃的）
            print(f"[DEBUG] 第一步：处理需要丢弃的停顿片段")
            sorted_pauses = sorted(pause_segments, key=lambda x: x[0])
            merged_pauses = []
            
            for pause_start, pause_end in sorted_pauses:
                if not merged_pauses:
                    merged_pauses.append([pause_start, pause_end])
                    print(f"[DEBUG] 添加停顿片段: [{pause_start:.3f}s-{pause_end:.3f}s]")
                else:
                    last_start, last_end = merged_pauses[-1]
                    if pause_start <= last_end:
                        # 重叠，合并停顿段
                        merged_pauses[-1][1] = max(last_end, pause_end)
                        print(f"[DEBUG] 合并重叠停顿: [{last_start:.3f}s-{last_end:.3f}s] + [{pause_start:.3f}s-{pause_end:.3f}s] -> [{merged_pauses[-1][0]:.3f}s-{merged_pauses[-1][1]:.3f}s]")
                    else:
                        merged_pauses.append([pause_start, pause_end])
                        print(f"[DEBUG] 添加停顿片段: [{pause_start:.3f}s-{pause_end:.3f}s]")
            
            print(f"[DEBUG] 合并后需要丢弃的停顿片段: {len(merged_pauses)} 个")
            for i, (start, end) in enumerate(merged_pauses):
                print(f"  停顿{i+1}: [{start:.3f}s-{end:.3f}s] (时长: {end-start:.3f}s)")
            
            # 第二步：自动生成需要保留的有效片段
            print(f"[DEBUG] 第二步：生成需要保留的有效片段")
            valid_segments = []
            current_time = 0.0
            
            for pause_start, pause_end in merged_pauses:
                if current_time < pause_start:
                    # 在停顿片段前的有效片段
                    valid_segments.append((current_time, pause_start))
                    print(f"[DEBUG] 生成有效片段: [{current_time:.3f}s-{pause_start:.3f}s] (时长: {pause_start-current_time:.3f}s)")
                # 跳过停顿片段，更新当前时间
                current_time = pause_end
            
            # 添加最后一段有效片段
            if current_time < total_duration:
                valid_segments.append((current_time, total_duration))
                print(f"[DEBUG] 生成最后有效片段: [{current_time:.3f}s-{total_duration:.3f}s] (时长: {total_duration-current_time:.3f}s)")
            
            print(f"[DEBUG] 总共生成 {len(valid_segments)} 个有效片段")
            
            # 第三步：检查是否需要处理
            if len(valid_segments) == 1 and valid_segments[0] == (0.0, total_duration):
                print("[DEBUG] 没有实际需要移除的内容，返回原视频")
                return [input_video_path]
            
            # 第四步：切割有效片段（不拼接，直接返回多个片段）
            print(f"[DEBUG] 第三步：切割有效片段（不拼接）")
            
            segment_files = []
            import uuid
            segment_id = str(uuid.uuid4())[:8]
            
            # 确保temp_materials目录存在
            temp_dir = "temp_materials"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # 切割每个有效片段
            for i, (start, end) in enumerate(valid_segments):
                duration = end - start
                segment_file = f"temp_materials/segment_{segment_id}_{i:03d}.mp4"
                
                print(f"[DEBUG] 切割有效片段 {i+1}: [{start:.3f}s-{end:.3f}s] (时长: {duration:.3f}s)")
                
                # 使用精确的时间切割，保持原始编码
                # 修复：将-ss参数放在-i之后以获得精确切割，虽然速度较慢但精度更高
                print(f"[DEBUG] FFmpeg切割命令:")
                print(f"[DEBUG]   输入视频: {input_video_path}")
                print(f"[DEBUG]   开始时间: {start:.6f}s")
                print(f"[DEBUG]   持续时长: {duration:.6f}s")
                print(f"[DEBUG]   输出文件: {segment_file}")
                
                try:
                    # 根据专业分析：直接使用重新编码确保精确切割
                    # 避免关键帧切割问题，使用-ss在-i之后进行精确切割
                    cmd = [
                        'ffmpeg', '-ss', f"{start:.6f}", '-to', f"{start + duration:.6f}",
                        '-i', input_video_path,
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                        '-c:a', 'aac', '-b:a', '128k',
                        '-map', '0',  # 确保映射所有流
                        '-avoid_negative_ts', 'make_zero',
                        '-fflags', '+genpts',  # 重新生成时间戳
                        '-g', '30',  # 设置合理的关键帧间隔
                        '-keyint_min', '15',  # 最小关键帧间隔
                        '-sc_threshold', '0',  # 禁用场景切割
                        '-pix_fmt', 'yuv420p',  # 确保像素格式兼容
                        segment_file, '-y'
                    ]
                    print(f"[DEBUG] 执行精确切割命令: {' '.join(cmd)}")
                    
                    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    if result.stderr:
                        print(f"[DEBUG] FFmpeg stderr: {result.stderr}")
                    print(f"[DEBUG] 精确切割完成")
                    
                    # 验证切割结果
                    verify_cmd = [
                        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', segment_file
                    ]
                    verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, check=True)
                    actual_duration = float(verify_result.stdout.strip())
                    
                    print(f"[DEBUG] 有效片段 {i+1}切割完成: {segment_file}")
                    print(f"[DEBUG]   计划时长: {duration:.3f}s")
                    print(f"[DEBUG]   实际时长: {actual_duration:.3f}s")
                    
                    # 检查时长是否正确（使用动态容差）
                    duration_diff = abs(actual_duration - duration)
                    tolerance = min(0.1, duration * 0.05)  # 动态容差：最小0.1秒或5%
                    
                    if duration_diff > tolerance:
                        print(f"[WARN] 片段 {i+1} 时长偏差较大: {duration_diff:.3f}s (容差: {tolerance:.3f}s)")
                    else:
                        print(f"[DEBUG] 片段 {i+1} 时长正确 (偏差: {duration_diff:.3f}s)")
                    
                    # 简单验证视频文件有效性
                    try:
                        # 检查视频流是否存在
                        video_check_cmd = [
                            'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                            '-show_entries', 'stream=codec_type',
                            '-of', 'csv=p=0', segment_file
                        ]
                        video_check_result = subprocess.run(video_check_cmd, capture_output=True, text=True, check=True)
                        if not video_check_result.stdout.strip():
                            raise Exception("切割后的文件没有视频流")
                        
                        print(f"[OK] 视频文件验证通过: {segment_file}")
                        segment_files.append(segment_file)
                        
                    except Exception as validation_error:
                        print(f"[ERROR] 视频文件验证失败: {validation_error}")
                        continue
                    
                except subprocess.CalledProcessError as e:
                    print(f"[ERROR] 切割片段 {i+1} 失败: {e}")
                    # 如果某个片段切割失败，尝试复制原视频
                    if i == 0 and len(valid_segments) == 1:
                        subprocess.run([
                            'ffmpeg', '-i', input_video_path, '-c', 'copy', segment_file, '-y'
                        ], check=True, capture_output=True)
                        segment_files.append(segment_file)
                        print(f"[DEBUG] 回退完成，使用原视频: {segment_file}")
            
            print(f"[OK] 视频有效片段切割完成，共生成 {len(segment_files)} 个片段")
            
            # 返回切割后的片段列表
            return segment_files
            
        except Exception as e:
            print(f"[ERROR] 视频片段切割处理失败: {e}")
            import traceback
            print(f"[ERROR] 错误堆栈: {traceback.format_exc()}")
            # 如果失败，返回原视频路径
            return [input_video_path]
    
    def _adjust_subtitle_timings(self, original_subtitles: List[Dict[str, Any]], 
                                pause_segments: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """
        根据移除的停顿调整字幕时间轴
        
        Args:
            original_subtitles: 原始字幕列表
            pause_segments: 被移除的停顿段落列表
            
        Returns:
            调整后的字幕列表
        """
        try:
            print(f"[DEBUG] 开始调整字幕时间轴")
            print(f"[DEBUG] 原始字幕数量: {len(original_subtitles)}")
            print(f"[DEBUG] 停顿段落数量: {len(pause_segments)}")
            
            adjusted_subtitles = []
            
            for subtitle in original_subtitles:
                original_start = subtitle['start']
                original_end = subtitle['end']
                
                # 计算在这个字幕之前被移除的停顿时长
                removed_time_before = 0.0
                
                for pause_start, pause_end in pause_segments:
                    if pause_end <= original_start:
                        # 完全在字幕之前的停顿
                        removed_time_before += (pause_end - pause_start)
                    elif pause_start < original_start and pause_end > original_start:
                        # 与字幕开始时间重叠的停顿
                        removed_time_before += (original_start - pause_start)
                
                # 调整时间
                new_start = original_start - removed_time_before
                new_end = original_end - removed_time_before
                
                # 确保时间不为负
                new_start = max(0, new_start)
                new_end = max(new_start, new_end)
                
                adjusted_subtitle = {
                    'text': subtitle['text'],
                    'start': new_start,
                    'end': new_end
                }
                
                adjusted_subtitles.append(adjusted_subtitle)
                
                print(f"[DEBUG] 字幕调整: {subtitle['text']}")
                print(f"   原始时间: {original_start:.3f}s - {original_end:.3f}s")
                print(f"   调整时间: {new_start:.3f}s - {new_end:.3f}s")
            
            print(f"[DEBUG] 字幕时间轴调整完成，共 {len(adjusted_subtitles)} 段字幕")
            return adjusted_subtitles
            
        except Exception as e:
            print(f"[DEBUG] 字幕时间轴调整失败: {e}")
            return original_subtitles  # 失败时返回原始字幕


def main():
    """主函数 - 音频转录智能字幕工作流"""
    # 配置剪映草稿文件夹路径（需要根据实际情况修改）
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    print("[INFO] 音频转录智能字幕工作流 + AI关键词高亮 + 背景音乐")
    print("=" * 60)
    print("自动转录音频并生成智能字幕，使用AI识别关键词进行高亮显示，并添加华尔兹背景音乐")
    
    # 创建工作流实例
    workflow = VideoEditingWorkflow(draft_folder_path, "audio_transcription_demo")
    
    # 配置华尔兹背景音乐路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    background_music_path = os.path.join(project_root, '华尔兹.mp3')
    
    # 配置输入参数
    inputs = {
        # 'digital_video_url': 'https://oss.oemi.jdword.com/prod/order/video/202509/V20250901153106001.mp4',
        # 'audio_url': 'https://oss.oemi.jdword.com/prod/temp/srt/V20250901152556001.wav',
        # 'title': '火山引擎ASR智能字幕演示',
        
        "audio_url": "https://oss.oemi.jdword.com/prod/temp/srt/V20250903210905001.wav",
        "content": "为什么女孩越漂亮越应该好好读书，有个作家说我美貌对于富人来说是锦上添花，对于中产来说是一笔财富，但对于穷人来说就是灾难。",
        "recordId": "",
        "tableId": "",
        "title": "漂亮女孩不读书美貌真是灾难吗",
        "digital_video_url": "https://oss.oemi.jdword.com/prod/order/video/202509/V20250903211536001.mp4",      

        
        # 🔥 火山引擎ASR配置（用于语音识别）
        'volcengine_appid': '6046310832',                # 火山引擎ASR AppID
        'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',  # 火山引擎ASR AccessToken
        
        # 🤖 豆包API配置（用于关键词提取）
        'doubao_token': 'adac0afb-5fd4-4c66-badb-370a7ff42df5',  # 请替换为您的豆包API token
        'doubao_model': 'doubao-1-5-pro-32k-250115',  # 豆包模型名称
        
        # [INFO] 背景音乐配置
        'background_music_path': background_music_path,  # 华尔兹.mp3路径
        'background_music_volume': 0.25,  # 背景音乐音量
    }
    
    try:
        print(f"\n[INFO] 开始处理工作流...")
        save_path = workflow.process_workflow(inputs)
        print(f"\n[OK] 音频转录工作流完成!")
        print(f"剪映项目已保存到: {save_path}")
        print("[INFO] 请打开剪映查看生成的智能字幕视频项目")
        
    except Exception as e:
        print(f"[ERROR] 工作流失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()