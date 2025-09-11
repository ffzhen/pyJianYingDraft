# -*- coding: utf-8 -*-
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
    
    def __init__(self, draft_folder_path: str, project_name: str = "flow_project", template_config: Dict[str, Any] = None):
        """初始化工作流
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            project_name: 项目名称
            template_config: 模板配置，包含标题和字幕的样式设置
        """
        self.draft_folder = draft.DraftFolder(draft_folder_path)
        self.project_name = project_name
        self.script = None
        self.audio_duration = 0  # 音频总时长（秒）
        self.video_duration = 0  # 视频总时长（秒）
        print(f"[VIDEO_DURATION] 初始化: {self.video_duration:.6f}s")
        self.project_duration = 0  # 项目总时长（秒），取音视频最长者
        self.volcengine_asr = None  # 火山引擎ASR客户端
        self.silence_remover = None  # 停顿移除器
        self.digital_video_path = None  # 数字人视频路径
        self.material_video_path = None  # 素材视频路径
        
        # 模板配置
        self.template_config = template_config or {}
        self._init_template_config()
        
        # 初始化字幕相关属性
        self.adjusted_subtitles = None  # 调整后的字幕（停顿移除后）
        self.original_subtitles = None  # 原始字幕（停顿移除前）
        self.secondary_asr_subtitles = None  # 二次ASR生成的字幕
        
        # 初始化封面相关属性
        self.cover_enabled = False  # 是否启用封面
        self.cover_duration = 0.0  # 封面时长（秒）
        self.cover_image_path = None  # 封面图片路径
        self.time_offset = 0.0  # 时间偏移量（秒）
        
        # 初始化日志系统
        self._init_logging()
    
    def _init_template_config(self):
        """初始化模板配置，设置默认值"""
        # 标题样式默认值
        self.title_config = {
            'color': self.template_config.get('title_color', '#FFFFFF'),
            'highlight_color': self.template_config.get('title_highlight_color', '#FFD700'),
            'bg_enabled': self.template_config.get('title_bg_enabled', True),
            'font': self.template_config.get('title_font', '俪金黑'),
            'font_size': float(self.template_config.get('title_font_size', '15')),
            'scale': float(self.template_config.get('title_scale', '1.0')),
            'line_spacing': float(self.template_config.get('title_line_spacing', '4')),
            'shadow_enabled': self.template_config.get('title_shadow_enabled', False)
        }
        
        # 字幕样式默认值
        self.subtitle_config = {
            'color': self.template_config.get('subtitle_color', '#FFFFFF'),
            'highlight_color': self.template_config.get('subtitle_highlight_color', '#00FFFF'),
            'bg_enabled': self.template_config.get('subtitle_bg_enabled', True),
            'font': self.template_config.get('subtitle_font', '俪金黑'),
            'font_size': float(self.template_config.get('subtitle_font_size', '18')),
            'scale': float(self.template_config.get('subtitle_scale', '1.0')),
            'shadow_enabled': self.template_config.get('subtitle_shadow_enabled', False)
        }
        
        # 封面样式默认值
        self.cover_config = {
            'background': self.template_config.get('cover_background', ''),
            'title_font': self.template_config.get('cover_title_font', '阳华体'),
            'title_color': self.template_config.get('cover_title_color', '#FFFFFF'),
            'title_size': float(self.template_config.get('cover_title_size', '24')),
            'subtitle_font': self.template_config.get('cover_subtitle_font', '俪金黑'),
            'subtitle_color': self.template_config.get('cover_subtitle_color', '#FFFFFF'),
            'subtitle_size': float(self.template_config.get('cover_subtitle_size', '18')),
            'title_shadow_enabled': self.template_config.get('cover_title_shadow_enabled', False),
            'subtitle_shadow_enabled': self.template_config.get('cover_subtitle_shadow_enabled', True)
        }
        
        # 字体映射 - 使用动态获取，支持任意字体名称
        self.font_mapping = {}
        
        print(f"[TEMPLATE] 标题样式: {self.title_config}")
        print(f"[TEMPLATE] 字幕样式: {self.subtitle_config}")
        print(f"[TEMPLATE] 封面样式: {self.cover_config}")
    
    def save_project(self) -> str:
        """保存项目并返回保存路径"""
        if not self.script:
            raise ValueError("请先创建草稿")
        
        # 获取草稿文件夹路径
        draft_path = self.draft_folder.folder_path
        project_path = os.path.join(draft_path, self.project_name)
        
        print(f"[SAVE] 项目已保存到: {project_path}")
        return project_path
    
    def _get_font_type(self, font_name: str) -> Any:
        """动态获取字体类型，支持任意字体名称"""
        try:
            # 直接通过字符串拼接获取字体类型
            return getattr(draft.FontType, font_name)
        except AttributeError:
            # 如果字体不存在，尝试一些常见的映射
            font_mappings = {
                '思源黑体': '思源黑体',
                '微软雅黑': '微软雅黑', 
                '宋体': '宋体',
                '黑体': '黑体',
                '楷体': '楷体',
                '仿宋': '仿宋',
                '阳华体': '阳华体',
                '俪金黑': '俪金黑'
            }
            
            # 尝试映射后的名称
            mapped_name = font_mappings.get(font_name, font_name)
            try:
                return getattr(draft.FontType, mapped_name)
            except AttributeError:
                # 如果还是找不到，返回默认字体
                print(f"[WARN] 字体 '{font_name}' 不存在，使用默认字体 '阳华体'")
                return draft.FontType.阳华体
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        """将十六进制颜色转换为RGB元组
        
        Args:
            hex_color: 十六进制颜色字符串，如 '#FFFFFF'
            
        Returns:
            RGB元组，取值范围[0, 1]
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return (1.0, 1.0, 1.0)  # 默认白色
        
        try:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return (r, g, b)
        except ValueError:
            return (1.0, 1.0, 1.0)  # 默认白色
        
    def _init_logging(self):
        """初始化日志系统"""
        import logging
        from datetime import datetime
        
        # 确保logs目录存在
        os.makedirs("workflow_logs", exist_ok=True)
        
        # 生成日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"workflow_logs/workflow_{timestamp}.log"
        
        # 设置日志格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # 创建logger
        self.logger = logging.getLogger(f'VideoEditingWorkflow_{timestamp}')
        self.logger.setLevel(logging.DEBUG)
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"🚀 视频编辑工作流开始 - 项目: {self.project_name}")
        self.logger.info(f"📝 日志保存至: {self.log_filename}")
    
    def _log(self, level: str, message: str):
        """统一的日志记录方法
        
        Args:
            level: 日志级别 (debug, info, warning, error)
            message: 日志消息
        """
        if hasattr(self, 'logger'):
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def _save_workflow_summary(self, inputs: Dict[str, Any], result_path: str, execution_time: float):
        """保存工作流执行摘要
        
        Args:
            inputs: 输入参数
            result_path: 结果路径
            execution_time: 执行时间（秒）
        """
        try:
            from datetime import datetime
            import json
            
            # 生成摘要报告
            summary = {
                "project_info": {
                    "project_name": self.project_name,
                    "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_seconds": round(execution_time, 2),
                    "result_path": result_path
                },
                "input_parameters": {
                    "audio_url": inputs.get('audio_url', 'N/A'),
                    "digital_video_url": inputs.get('digital_video_url', 'N/A'),
                    "material_video_url": inputs.get('material_video_url', 'N/A'),
                    "title": inputs.get('title', 'N/A'),
                    "background_music_path": inputs.get('background_music_path', 'N/A'),
                    "volcengine_configured": bool(inputs.get('volcengine_appid')),
                    "doubao_configured": bool(inputs.get('doubao_token'))
                },
                "processing_results": {
                    "audio_duration": round(self.audio_duration, 2) if self.audio_duration else 0,
                    "video_duration": round(self.video_duration, 2) if self.video_duration else 0,
                    "project_duration": round(self.project_duration, 2) if self.project_duration else 0,
                    "subtitles_count": len(self.adjusted_subtitles) if self.adjusted_subtitles else 0,
                    "original_subtitles_count": len(self.original_subtitles) if self.original_subtitles else 0
                },
                "technical_details": {
                    "non_destructive_editing": True,
                    "asr_provider": "VolcEngine",
                    "keyword_extraction": "Unlimited AI-Enhanced",
                    "subtitle_alignment": "Perfect MP4 Direct Processing"
                }
            }
            
            # 关键词信息
            if hasattr(self, 'volcengine_asr') and self.volcengine_asr and self.adjusted_subtitles:
                all_text = " ".join([sub['text'] for sub in self.adjusted_subtitles])
                keywords = self.volcengine_asr.extract_keywords_with_ai(all_text)
                summary["keyword_analysis"] = {
                    "total_keywords": len(keywords) if keywords else 0,
                    "keywords_list": keywords if keywords else [],
                    "high_value_keywords": [kw for kw in (keywords or []) if len(kw) >= 3],
                    "wealth_related": [kw for kw in (keywords or []) if any(x in kw for x in ['富', '钱', '财', '万', '元', '补偿', '收入'])],
                    "policy_related": [kw for kw in (keywords or []) if any(x in kw for x in ['政策', '国家', '改造', '拆迁', '安置'])]
                }
            
            # 保存摘要文件
            summary_filename = self.log_filename.replace('.log', '_summary.json')
            with open(summary_filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📊 工作流摘要已保存: {summary_filename}")
            
        except Exception as e:
            self.logger.error(f"保存工作流摘要时出错: {e}")
    
    def _log_subtitle_details(self, subtitles: List[Dict[str, Any]], subtitle_type: str = ""):
        """记录字幕详细信息到日志
        
        Args:
            subtitles: 字幕列表
            subtitle_type: 字幕类型描述
        """
        if not subtitles:
            return
            
        self.logger.info(f"📋 {subtitle_type}字幕详情 (共{len(subtitles)}段):")
        for i, subtitle in enumerate(subtitles, 1):
            start = subtitle.get('start', 0)
            end = subtitle.get('end', 0)
            text = subtitle.get('text', '')
            duration = end - start
            self.logger.info(f"  {i:2d}. [{start:7.3f}s-{end:7.3f}s] ({duration:5.2f}s) {text}")
        
        # 统计信息
        total_duration = sum(sub.get('end', 0) - sub.get('start', 0) for sub in subtitles)
        avg_duration = total_duration / len(subtitles) if subtitles else 0
        self.logger.info(f"📊 统计: 总时长{total_duration:.1f}秒, 平均{avg_duration:.1f}秒/段")
        
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
                            "你是文案排版助手。请把给定中文标题合理断句为3行，如果内容不够可以适当扩充，整体还是简明扼要，；例如：买房字\n到底该怎么买\n过来人说句真话" \
                            "每行尽量语义完整、有真人感、激发用户情绪。只返回三行内容，用\n分隔，不要额外说明。"
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
                        try:
                            self.logger.info("✂️ 标题拆分: 使用AI(豆包)")
                        except Exception:
                            print("[TITLE_SPLIT] 使用AI(豆包)")
                        return lines[:3]
        except Exception as _:
            try:
                self.logger.info("✂️ 标题拆分: AI失败，使用本地规则")
            except Exception:
                print("[TITLE_SPLIT] AI失败，使用本地规则")

        # 本地回退：优先按中文标点切分；不足三段时退化为按字符等分
        import re
        tokens = re.split(r'[，。！？、;；\s]+', title)
        tokens = [t for t in tokens if t]

        if len(tokens) >= 3:
            # 将分词尽量均衡地分配到三行
            target = [[], [], []]
            lengths = [0, 0, 0]
            for tok in tokens:
                i = lengths.index(min(lengths))
                target[i].append(tok)
                lengths[i] += len(tok)
            try:
                self.logger.info("✂️ 标题拆分: 本地规则(按标点分词均衡)")
            except Exception:
                print("[TITLE_SPLIT] 本地规则(按标点分词均衡)")
            return [''.join(x) for x in target]
        else:
            # 标题无标点或仅一两个连续词：按字符长度等分为三行
            n = len(title)
            if n <= 3:
                # 极短标题，保证三行存在
                try:
                    self.logger.info("✂️ 标题拆分: 本地规则(极短标题字符均分)")
                except Exception:
                    print("[TITLE_SPLIT] 本地规则(极短标题字符均分)")
                return [title[:1], title[1:2] if n > 1 else '', title[2:3] if n > 2 else '']
            a = (n + 2) // 3
            b = (n - a + 1) // 2
            c = n - a - b
            # 确保每段至少1个字符
            if a == 0: a = 1
            if b == 0: b = 1
            if c == 0:
                # 从前两段挪一个字符给第三段
                if a > 1:
                    a -= 1
                elif b > 1:
                    b -= 1
                c = n - a - b
            try:
                self.logger.info("✂️ 标题拆分: 本地规则(字符等分)")
            except Exception:
                print("[TITLE_SPLIT] 本地规则(字符等分)")
            return [title[:a], title[a:a+b], title[a+b:]]

    def add_three_line_title(self, title: str,
                             start: float = 0.0,
                             duration: Optional[float] = None,
                             *,
                             transform_y: float = 0.72,
                             line_spacing: int = 4,
                             highlight_color: Tuple[float, float, float] = None,
                             track_name: str = "标题字幕轨道") -> draft.TextSegment:
        """添加三行标题：中间一行高亮。
        - 字体：俪金黑；字号：15；左对齐；max_line_width=0.6；自动换行
        - transform_y=0.72；行间距可配
        """
        if not self.script:
            raise ValueError("请先创建草稿")

        # 使用模板配置或默认值
        if highlight_color is None:
            highlight_color = self._hex_to_rgb(self.title_config['highlight_color'])
        
        title_font = self._get_font_type(self.title_config['font'])
        title_color = self._hex_to_rgb(self.title_config['color'])
        title_size = self.title_config['font_size']
        title_scale = self.title_config['scale']
        title_line_spacing = int(self.title_config['line_spacing'])  # 转换为整数，默认4

        lines = self._split_title_to_three_lines(title)
        # 保障三行
        while len(lines) < 3:
            lines.append("")
        text = "\n".join(lines[:3])

        # 计算时间 - 使用有效视频时长（保留两位小数）
        if duration is None:
            effective_duration = self.get_effective_video_duration()
            duration = round(max(1.0, effective_duration) if effective_duration > 0 else 5.0, 2)

        style = draft.TextStyle(
            size=title_size,
            bold=True,
            align=0,  # 左对齐
            color=title_color,
            # auto_wrapping=True,
            max_line_width=0.7,
            line_spacing=title_line_spacing
        )

        # 阴影（按模板开关）
        title_shadow = None
        try:
            if hasattr(self, 'title_config') and self.title_config.get('shadow_enabled', False):
                title_shadow = draft.TextShadow(
                    alpha=0.8,
                    color=(0.0, 0.0, 0.0),
                    diffuse=20.0,
                    distance=10.0,
                    angle=-45.0
                )
        except Exception:
            title_shadow = None

        seg = draft.TextSegment(
            text,
            trange(tim(f"{start:.6f}s"), tim(f"{duration:.6f}s")),
            font=title_font,
            style=style,
            clip_settings=draft.ClipSettings(transform_y=transform_y, scale_x=title_scale, scale_y=title_scale),
            shadow=title_shadow
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
        # 使用更高精度避免帧数不匹配问题
        self.project_duration = round(self.video_duration, 6)
        if self.project_duration > 0:
            print(f"[INFO] 项目总时长更新为: {self.project_duration:.6f} 秒 ，视频: {self.video_duration:.6f}s)")
    
    def _get_video_duration(self, video_path: str) -> float:
        """获取视频文件时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            float: 视频时长（秒），失败返回0
        """
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', video_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
            else:
                print(f"[WARN] 无法获取视频时长: {result.stderr}")
                return 0.0
        except Exception as e:
            print(f"[WARN] 获取视频时长失败: {e}")
            return 0.0

    def _validate_duration_bounds(self, duration: float, context: str = "") -> float:
        """验证时长边界，确保不超过视频总时长
        
        Args:
            duration: 需要验证的时长（秒）
            context: 上下文信息，用于调试
            
        Returns:
            验证后的时长（秒），保留两位小数
        """
        # 获取最大允许时长（优先使用有效视频时长）
        max_allowed_duration = self.get_effective_video_duration()
        
        # 如果没有有效视频时长，使用项目时长
        if max_allowed_duration <= 0:
            max_allowed_duration = self.project_duration
            
        # 如果仍然没有，直接返回原时长
        if max_allowed_duration <= 0:
            print(f"[WARN] {context}无法验证时长边界，因为没有视频时长参考")
            return round(duration, 2)
            
        # 验证时长不超过最大允许时长
        if duration > max_allowed_duration:
            print(f"[WARN] {context}时长 {duration:.2f}s 超过最大允许时长 {max_allowed_duration:.2f}s，将被截取")
            return round(max_allowed_duration, 2)
        else:
            print(f"[DEBUG] {context}时长 {duration:.2f}s 在允许范围内 (最大: {max_allowed_duration:.2f}s)")
            return round(duration, 2)

    def get_effective_video_duration(self):
        """获取有效视频时长（去除停顿后的实际视频长度）
        
        在进行停顿移除处理后，实际视频长度会比原始长度短。
        所有组件的持续时间都不应超过这个有效时长。
        
        Returns:
            float: 有效视频时长（秒）
        """
        # 如果进行了停顿移除处理，video_duration 已经是处理后的时长
        # 否则使用项目总时长
        print(f"[VIDEO_DURATION] 获取有效时长: video={self.video_duration:.6f}s, audio={self.audio_duration:.6f}s, project={self.project_duration:.6f}s")
        
        if hasattr(self, 'adjusted_subtitles') and self.adjusted_subtitles and self.video_duration > 0:
            # 使用处理后的视频时长
            effective_duration = self.video_duration
            print(f"[VIDEO_DURATION] 使用处理后的视频时长: {effective_duration:.6f}s")
        elif self.video_duration > 0:
            # 使用原始视频时长
            effective_duration = self.video_duration
            print(f"[VIDEO_DURATION] 使用原始视频时长: {effective_duration:.6f}s")
        else:
            # 最后回退到项目时长
            effective_duration = self.project_duration
            print(f"[VIDEO_DURATION] 回退使用项目时长: {effective_duration:.6f}s")
            
        return effective_duration
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
        self.script.add_track(TrackType.audio, "音频轨道", relative_index=2)
        self.script.add_track(TrackType.audio, "背景音乐轨道", relative_index=3)
        # 文本类：字幕背景在对应字幕下方（层级更低，先创建）
        self.script.add_track(TrackType.text, "内容字幕背景", relative_index=4)  # 背景在下方
        self.script.add_track(TrackType.text, "内容字幕轨道", relative_index=5)
        self.script.add_track(TrackType.text, "标题字幕背景", relative_index=6)  # 背景在下方
        self.script.add_track(TrackType.text, "标题字幕轨道", relative_index=7)
        
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
                trange(tim(f"{start_time:.6f}s"), tim(f"{duration:.6f}s"))
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
        old_duration = self.video_duration
        self.video_duration = round(total_video_duration, 6)
        self._update_project_duration()
        print(f"[VIDEO_DURATION] 视频片段累计: {old_duration:.6f}s -> {self.video_duration:.6f}s (累计: {total_video_duration:.6f}s)")
            
        return video_segments
    
    def add_digital_human_video(self, digital_video_url: str, duration: int = None, remove_pauses: bool = False,
                               min_pause_duration: float = 0.2, max_word_gap: float = 0.8, time_offset: float = 0.0):
        """添加数字人视频
        
        Args:
            digital_video_url: 数字人视频URL
            duration: 持续时长(秒)，如果不指定则使用整个视频
            remove_pauses: 是否移除视频中的音频停顿，默认False
            min_pause_duration: 最小停顿时长(秒)，默认0.2秒
            max_word_gap: 单词间最大间隔(秒)，默认0.8秒
        """
        # 添加并发安全保护
        import threading
        if not hasattr(self, '_digital_video_lock'):
            self._digital_video_lock = threading.RLock()
        
        with self._digital_video_lock:
            # 检查是否已经手动处理过多片段
            if hasattr(self, 'skip_normal_processing') and self.skip_normal_processing:
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
            print("[INFO] 开始处理视频音频停顿移除...")
            
            # 1. 提取视频中的音频
            temp_audio_path = self._generate_unique_filename("video_audio", ".mp3")
            try:
                # 使用FFmpeg提取音频
                subprocess.run([
                    'ffmpeg', '-i', local_path, '-q:a', '0', '-map', 'a', temp_audio_path, '-y'
                ], check=True, capture_output=True)
                print(f"[OK] 音频提取完成")
                
                # 2. 使用ASR处理音频停顿
                asr_result = self.volcengine_asr.transcribe_audio_for_silence_detection(digital_video_url)
                print(f"[DEBUG] ASR识别结果: {asr_result}")
                if asr_result:
                    # 3. 分析停顿段落
                    pause_detector = ASRSilenceDetector(min_pause_duration, max_word_gap)
                    pause_segments = pause_detector.detect_pauses_from_asr(asr_result)
                    
                    # 4. 生成原始字幕
                    subtitle_objects = self.volcengine_asr.parse_result_to_subtitles(asr_result)
                    self.original_subtitles = subtitle_objects
                    print(f"[DEBUG] 原始字幕",subtitle_objects)
                    
                    if pause_segments:
                        print(f"[OK] 检测到 {len(pause_segments)} 个停顿段落")
                     
                        # 6. 调整字幕时间轴
                        adjusted_subtitles = self._adjust_subtitle_timings(
                            subtitle_objects, pause_segments
                        )
                        self.adjusted_subtitles = adjusted_subtitles
                        self.original_subtitles = subtitle_objects
                        
                        # 7. 使用非破坏性片段标记方式处理停顿（避免真实切割，完美保持原始质量）
                        success = self._process_video_pauses_by_segments_marking(
                            local_path, pause_segments, time_offset
                        )
                        
                        if success:
                            print(f"[OK] 非破坏性视频停顿标记完成，字幕与视频完全同步")
                            # 设置标志，表示已经手动添加了所有片段，需要跳过正常的 add_digital_human_video 逻辑
                            self.skip_normal_processing = True
                        else:
                            print(f"[WARN] 非破坏性视频停顿标记失败，跳过停顿移除")
                         
                        # 8. 添加调整后的字幕到视频
                        if adjusted_subtitles:
                            print(f"[OK] 添加调整后的字幕: {len(adjusted_subtitles)} 段")
                            
                            # 提取关键词用于高亮
                            all_text = " ".join([sub['text'] for sub in adjusted_subtitles])
                            keywords = self.volcengine_asr.extract_keywords_with_ai(all_text)
                            
                            if keywords:
                                print(f"[OK] 视频字幕提取到 {len(keywords)} 个关键词: {keywords}")
                            else:
                                print("[WARN] 视频字幕未提取到关键词")
                            
                            # # 清理现有的字幕轨道以避免重叠
                            # self._clear_caption_tracks()
                            
                            # 添加字幕（带关键词高亮）
                            print(f"[DEBUG] 添加字幕（带关键词高亮）",adjusted_subtitles)
                            self.add_captions(adjusted_subtitles, track_name="内容字幕轨道", position="bottom",
                                            keywords=keywords, 
                                            base_color=(1.0, 1.0, 1.0),  # 白色
                                            base_font_size=8.0,  # 8号
                                            font_type=draft.FontType.俪金黑,  # 俪金黑
                                            highlight_size=10.0,  # 高亮10号
                                            highlight_color=(1.0, 0.7529411765, 0.2470588235),  # #ffc03f
                                            scale=1.39,
                                            time_offset=time_offset)  # 缩放1.39
                            
                            print(f"[OK] 调整后的字幕已添加（含关键词高亮）")
                        # else:
                        #     print("[WARN] 音频停顿处理失败，使用原始视频")
                    else:
                        print("[DEBUG] 未检测到需要移除的停顿")
                else:
                    print("[WARN] ASR识别失败，跳过停顿移除")
                    
            except Exception as e:
                print(f"[WARN] 视频音频停顿处理失败: {e}")
        
        # 保存数字人视频路径
        self.digital_video_path = local_path
        
       
    
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
            print(f"[INFO] 开始集成方案：先ASR识别，再处理停顿")
            
            # 1. 先用原始URL进行ASR识别  
            asr_result = self.volcengine_asr.transcribe_audio_for_silence_detection(original_audio_url)
            
            if asr_result:
                print(f"[OK] ASR识别完成，开始分析停顿")
                
                # 2. 分析停顿段落
                pause_detector = ASRSilenceDetector(min_pause_duration, max_word_gap)
                pause_segments = pause_detector.detect_pauses_from_asr(asr_result)
                
                # 3. 生成原始字幕
                subtitle_objects = self.volcengine_asr.parse_result_to_subtitles(asr_result)
                
                print(f"[OK] 检测到 {len(pause_segments)} 个停顿段落，生成 {len(subtitle_objects)} 段字幕")
                
                # 4. 如果有停顿，下载音频并进行处理
                if pause_segments:
                    print(f"[INFO] 下载音频并移除停顿")
                    
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
                        
                        print(f"[OK] 音频下载成功，开始停顿处理")
                        
                        # 处理音频停顿
                        processed_audio_path = self._process_audio_pauses_with_asr_result(
                            local_path, asr_result, pause_segments, min_pause_duration, max_word_gap, enable_secondary_asr=True
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
                    actual_duration = self.video_duration
                else:
                    actual_duration = original_audio_duration
        else:
            # 如果有视频，检查指定时长是否超过视频时长
            if self.video_duration > 0 and duration > self.video_duration:
                actual_duration = self.video_duration
                print(f"[WARN] 指定音频时长({duration:.1f}s)超过视频时长({self.video_duration:.1f}s)，将截取至视频时长")
            else:
                actual_duration = duration
        
        duration_microseconds = tim(f"{actual_duration:.6f}s")
        self.audio_duration = round(actual_duration, 2)
        
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
        print(f"[INFO] 音频时长: {self.audio_duration:.2f} 秒")
        
        return audio_segment
    
    def _resolve_music_path(self, music_path: str) -> str:
        """解析音乐文件路径
        
        Args:
            music_path: 原始音乐文件路径
            
        Returns:
            解析后的绝对路径
        """
        # 如果已经是绝对路径，直接返回
        if os.path.isabs(music_path):
            return music_path
        
        # 如果是相对路径，尝试多个可能的根目录
        possible_roots = [
            os.getcwd(),  # 当前工作目录
            os.path.dirname(os.path.abspath(__file__)),  # 当前文件所在目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'),  # 项目根目录
        ]
        
        for root in possible_roots:
            full_path = os.path.join(root, music_path)
            if os.path.exists(full_path):
                print(f"[INFO] 找到背景音乐文件: {full_path}")
                return full_path
        
        # 如果都找不到，返回原始路径（让后续的错误处理来处理）
        print(f"[WARNING] 无法解析背景音乐路径: {music_path}")
        return music_path
    
    def add_background_music(self, music_path: str, target_duration: float = None, volume: float = 0.3, time_offset: float = 0.0):
        """添加背景音乐
        
        Args:
            music_path: 背景音乐文件路径（本地路径）
            target_duration: 目标时长（秒），如果None则使用项目总时长（音视频中最长者）
            volume: 音量(0-1)，默认0.3比较适合背景音乐
            time_offset: 时间偏移（秒），背景音乐开始播放的时间偏移
        """
        if not self.script:
            raise ValueError("请先创建草稿")
        
        # 解析音乐文件路径
        resolved_music_path = self._resolve_music_path(music_path)
            
        if not os.path.exists(resolved_music_path):
            raise ValueError(f"背景音乐文件不存在: {resolved_music_path}")
        
        # 获取背景音乐素材信息
        bg_music_material = draft.AudioMaterial(resolved_music_path)
        
        # 确定目标时长 - 优先使用有效视频时长确保不超过处理后视频长度（保留两位小数）
        if target_duration is None:
            effective_duration = self.get_effective_video_duration()
            if effective_duration > 0:
                target_duration = round(effective_duration, 6)
                print(f"[INFO] 背景音乐将使用有效视频时长: {target_duration:.6f}s (确保不超过处理后视频长度)")
            elif self.video_duration > 0:
                target_duration = round(self.video_duration, 6)
                print(f"[INFO] 背景音乐将使用视频时长: {target_duration:.6f}s")
            elif self.audio_duration > 0:
                target_duration = round(self.audio_duration, 6)
                print(f"[INFO] 背景音乐将使用音频时长: {target_duration:.6f}s")
            else:
                raise ValueError("无法确定目标时长，请先添加音频或视频，或指定target_duration")
        else:
            # 验证用户指定的目标时长
            target_duration = self._validate_duration_bounds(target_duration, "背景音乐")
        
        target_duration_microseconds = tim(f"{target_duration:.6f}s")
        bg_music_duration_microseconds = bg_music_material.duration
        
        # 计算是否需要循环播放
        bg_music_duration_seconds = bg_music_duration_microseconds / 1000000
        
        if bg_music_duration_seconds >= target_duration:
            # 背景音乐够长，直接截取
            bg_music_segment = draft.AudioSegment(
                bg_music_material,
                trange(tim(f"{time_offset:.6f}s"), tim(f"{target_duration:.6f}s")),
                volume=volume
            )
            # 添加淡入淡出已移除
            # 添加到背景音乐轨道
            self.script.add_segment(bg_music_segment, track_name="背景音乐轨道")
            print(f"[INFO] 背景音乐已添加: {os.path.basename(music_path)}，开始时间: {time_offset:.6f}s，截取时长: {target_duration:.6f}s，音量: {volume}")
        else:
            # 背景音乐太短，需要循环
            print(f"[INFO] 背景音乐时长 {bg_music_duration_seconds:.2f}s，目标时长 {target_duration:.2f}s，将循环播放")
            
            # 计算需要循环的次数
            loop_count = int(target_duration / bg_music_duration_seconds) + 1
            current_time = 0
            
            for i in range(loop_count):
                # 计算当前循环的持续时间
                remaining_time = target_duration - current_time
                if remaining_time <= 0:
                    break
                    
                current_duration = min(bg_music_duration_seconds, remaining_time)
                
                # 创建当前循环的音频片段，应用时间偏移
                loop_segment = draft.AudioSegment(
                    bg_music_material,
                    trange(tim(f"{time_offset + current_time:.6f}s"), tim(f"{current_duration:.6f}s")),
                    volume=volume
                )
                
                # 为第一个和最后一个片段添加淡入淡出
                # 第一个片段淡入已移除
                # 最后一个片段淡出已移除
                
                # 添加到背景音乐轨道
                self.script.add_segment(loop_segment, track_name="背景音乐轨道")
                
                current_time += current_duration
            
            print(f"[INFO] 背景音乐循环已添加: {os.path.basename(music_path)}，开始时间: {time_offset:.6f}s，{loop_count}次循环，总时长: {target_duration:.6f}s，音量: {volume}")
        
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
            trange(tim(f"{timerange_start:.6f}s"), tim(f"{timerange_duration:.6f}s")),
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
        
        # 确保目标轨道存在（若不存在则自动创建为文本轨道，背景轨道层级更低）
        try:
            _ = self.script.tracks[track_name]
        except KeyError:
            # 为字幕背景轨道设置正确的层级（在对应的字幕轨道之前）
            if "背景" in track_name:
                # 背景轨道应该在对应的字幕轨道之前创建，层级更低
                existing_text_tracks = [name for name in self.script.tracks.keys() 
                                      if self.script.tracks[name].track_type == TrackType.text]
                # 背景轨道使用较低的索引
                next_index = len(existing_text_tracks) + 1
            else:
                # 普通字幕轨道使用正常索引
                existing_text_tracks = [name for name in self.script.tracks.keys() 
                                      if self.script.tracks[name].track_type == TrackType.text]
                next_index = len(existing_text_tracks) + 2  # 留出空间给对应的背景轨道
            self.script.add_track(TrackType.text, track_name, relative_index=next_index)

        # 添加到轨道
        self.script.add_segment(text_segment, track_name=track_name)
        
        print(f"[OK] 带背景的文本已添加: '{text_content[:20]}...' 到 {track_name}")
        print(f"   背景: {background_style['color']} {background_style['alpha']*100:.0f}% 透明度")
        print(f"   位置: {position}, 时长: {timerange_duration:.6f}秒")
        
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
            print(f"[DEBUG] ASR识别源: 直接使用原始音频/视频URL -> {audio_url}")
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
            
            # 调整时间（保持两位小数精度）
            new_start = round(original_start / speed_factor + delay_seconds, 2)
            new_duration = round(original_duration / speed_factor, 2)
            new_end = round(new_start + new_duration, 2)
            
            # 确保时间不为负（保持两位小数）
            new_start = round(max(0, new_start), 2)
            new_end = round(max(new_start + 0.5, new_end), 2)  # 最少0.5秒显示时间
            
            adjusted_subtitle = {
                'text': subtitle['text'],
                'start': new_start,
                'end': new_end
            }
            adjusted_subtitles.append(adjusted_subtitle)
            
            print(f"   第{i+1}段: {original_start:.2f}s-{original_end:.2f}s → {new_start:.2f}s-{new_end:.2f}s")
        
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
                    base_font_size: float = None,
                    base_color: Tuple[float, float, float] = None,
                    font_type: Optional[draft.FontType] = None,
                    highlight_color: Tuple[float, float, float] = None,
                    highlight_size: float = None,
                    bottom_transform_y: float = -0.3,
                    scale: float = None,
                    time_offset: float = 0.0,
                    background_style: Dict[str, Any] = None):
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
        
        # 使用模板配置或默认值
        if base_font_size is None:
            base_font_size = self.subtitle_config['font_size']
        if base_color is None:
            base_color = self._hex_to_rgb(self.subtitle_config['color'])
        if font_type is None:
            font_type = self._get_font_type(self.subtitle_config['font'])
        if highlight_color is None:
            highlight_color = self._hex_to_rgb(self.subtitle_config['highlight_color'])
        if highlight_size is None:
            highlight_size = self.subtitle_config['font_size'] * 1.2
        if scale is None:
            scale = self.subtitle_config['scale'] * 1.39  # 保持原有的缩放倍数
            
        # 如果没有提供字幕数据，尝试使用调整后的字幕
        if caption_data is None:
            if hasattr(self, 'adjusted_subtitles') and self.adjusted_subtitles:
                caption_data = self.adjusted_subtitles
                print(f"[DEBUG] 使用调整后的字幕: {len(caption_data)} 段")
            else:
                print("[DEBUG] 没有可用的字幕数据")
                return
        
        # # 清理现有的字幕轨道以避免重叠
        # self._clear_caption_tracks()
            
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
                        
            # 应用时间偏移
            adjusted_start_time = start_time + time_offset
            adjusted_end_time = end_time + time_offset
            
            # 计算时间范围（提高精度，保留两位小数）
            start_time_str = f"{adjusted_start_time:.2f}s"  # 使用2位小数精度
            duration_str = f"{adjusted_end_time - adjusted_start_time:.2f}s"  # 使用2位小数精度
            
            # 调试：输出实际的时间参数（两位小数）
            print(f"[DEBUG] 字幕时间参数: '{text}' -> start={start_time_str}, duration={duration_str} (偏移: {time_offset:.6f}s)")
                        
            # 创建文本片段，只传入当前文本中存在的关键词
            # 阴影（按模板开关）
            subtitle_shadow = None
            try:
                if hasattr(self, 'subtitle_config') and self.subtitle_config.get('shadow_enabled', False):
                    subtitle_shadow = draft.TextShadow(
                        alpha=0.8,
                        color=(0.0, 0.0, 0.0),
                        diffuse=20.0,
                        distance=10.0,
                        angle=-45.0
                    )
            except Exception:
                subtitle_shadow = None

            text_segment = draft.TextSegment(
                text,
                trange(tim(start_time_str), tim(duration_str)),
                font=(font_type if font_type is not None else draft.FontType.俪金黑),
                style=draft.TextStyle(
                    color=text_color,
                    size=base_font_size,
                    auto_wrapping=True,
                    bold=True,
                    align=0,
                    max_line_width=0.82
                ),
                clip_settings=draft.ClipSettings(transform_y=transform_y, scale_x=scale, scale_y=scale),
                shadow=subtitle_shadow
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
        
        # 根据模板配置添加字幕背景
        if hasattr(self, 'subtitle_config') and self.subtitle_config.get('bg_enabled', False):
            try:
                self.add_caption_backgrounds(
                    caption_data=caption_data,
                    position=position,
                    bottom_transform_y=bottom_transform_y,
                    scale=scale,
                    background_style=background_style,
                    time_offset=time_offset
                )
                print(f"[TEMPLATE] 已添加字幕背景")
            except Exception as e:
                print(f"[ERROR] 添加字幕背景失败: {e}")
        else:
            print(f"[TEMPLATE] 字幕背景已禁用")
            
        return text_segments
    
    def add_caption_backgrounds(self, caption_data: List[Dict[str, Any]], 
                               position: str = "bottom",
                               bottom_transform_y: float = -0.3,
                               scale: float = 1.39,
                               background_style: Dict[str, Any] = None,
                               time_offset: float = 0.0):
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
        
        # 添加并发安全保护
        import threading
        if not hasattr(self, '_caption_background_lock'):
            self._caption_background_lock = threading.RLock()
        
        with self._caption_background_lock:
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
            
            # 计算字幕背景的总时长（使用有效视频时长，确保不超过处理后的视频长度，保留两位小数）
            start_time = 0.0 + time_offset  # 从项目开始，应用时间偏移
            
            # 使用有效视频时长作为背景持续时间
            effective_duration = self.get_effective_video_duration()
            if effective_duration > 0:
                total_duration = round(effective_duration, 6)
                print(f"[DEBUG] 字幕背景使用有效视频时长: {total_duration:.6f}s (确保不超过处理后视频)")
            else:
                # 回退方案：使用字幕时长
                caption_start = min(caption.get('start', 0) for caption in caption_data)
                caption_end = max(caption.get('end', 0) for caption in caption_data)
                total_duration = round(caption_end - caption_start, 6)
                print(f"[DEBUG] 字幕背景回退使用字幕时长: {total_duration:.6f}s")
            
            # 验证背景时长不超过视频总时长
            total_duration = self._validate_duration_bounds(total_duration, "字幕背景")
            
            print(f"[DEBUG] 字幕背景时长设置: {start_time:.6f}s - {start_time + total_duration:.6f}s")
            
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
    
    def process_workflow(self, inputs: Dict[str, Any], time_offset: float = 0.0, template_config: Dict[str, Any] = None) -> str:
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
            time_offset: 前置时间差（秒），主片段整体往后迁移的时间 (默认0.0)
            template_config: 模板配置，包含标题、字幕、封面等样式配置
                
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
        subtitle_speed = inputs.get('subtitle_speed', 1.0)  # 字幕速度系数
        background_music_path = inputs.get('background_music_path')  # 背景音乐路径
        background_music_volume = inputs.get('background_music_volume', 0.3)  # 背景音乐音量
        # # 验证必需参数
        # if not audio_url:
        #     raise ValueError("audio_url 是必需参数，用于音频转录")
        
        # 处理模板配置
        if template_config:
            self.template_config = template_config
            self._init_template_config()
            print(f"[TEMPLATE] 已应用模板配置")
        
        # 开始执行时间记录
        import time
        start_time = time.time()
        
        self.logger.info("🎬 开始处理视频编辑工作流")
        self.logger.info(f"📋 输入参数: {', '.join([f'{k}: {v}' if k not in ['volcengine_access_token', 'doubao_token'] else f'{k}: ***' for k, v in inputs.items()])}")
        
        print(f"[INFO] 音频转录字幕工作流 + AI关键词高亮")

        print(f"[INFO] 字幕速度: {subtitle_speed:.1f}x")
        print(f"[INFO] 火山引擎ASR (语音识别)")
        print(f"[INFO] 豆包API (关键词提取): {'已配置' if doubao_token else '未配置，将使用本地算法'}")
        
        # 同步到日志
        self.logger.info(f"🎵 音频URL: {audio_url}")
        # self.logger.info(f"⏱️ 字幕延迟: {subtitle_delay:.1f}秒")
        self.logger.info(f"🏃 字幕速度: {subtitle_speed:.1f}x")
        self.logger.info(f"🔥 火山引擎ASR (语音识别)")
        self.logger.info(f"🤖 豆包API (关键词提取): {'已配置' if doubao_token else '未配置，将使用本地算法'}")
        
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
        
        # 1. 创建草稿（如果还没有创建）
        if not self.script:
            self.create_draft()

        # 1.1 处理封面（如果提供了 cover_short_title/cover_image_path/cover_bottom_text）
        effective_offset = time_offset
        try:
            cover_short_title = inputs.get('cover_short_title')
            cover_image_path = inputs.get('cover_image_path')
            cover_bottom_text = inputs.get('cover_bottom_text')

            if cover_short_title or cover_image_path or cover_bottom_text:
                print(f"[INFO] 准备添加封面: top='{(cover_short_title or '')[:20]}', bottom='{(cover_bottom_text or '')[:20]}', image='{cover_image_path or ''}'")
                cover_result = self.add_cover(
                    cover_image_path=cover_image_path,
                    frames=2,
                    fps=30,
                    top_text=cover_short_title,
                    bottom_text=cover_bottom_text,
                )
                # 使用封面时长作为后续主轴偏移
                if isinstance(cover_result, dict) and 'cover_duration' in cover_result:
                    effective_offset = float(cover_result['cover_duration'])
                    print(f"[INFO] 封面已添加，应用主轴偏移: {effective_offset:.6f}s")
                else:
                    print("[WARN] 封面结果未包含 cover_duration，继续使用传入的 time_offset")
        except Exception as e:
            print(f"[ERROR] 添加封面失败: {e}")

        # 2. 添加数字人视频及字幕生成
        digital_video_url = inputs.get('digital_video_url')
        if digital_video_url:
            self.add_digital_human_video(
                    digital_video_url, 
                    remove_pauses=True, 
                    min_pause_duration=0.01, 
                    max_word_gap=0.1,
                    time_offset=effective_offset
                )
        
        # # 3. 添加素材视频（如果有）
        # material_video_url = inputs.get('material_video_url')
        # if material_video_url:
        #     # 模拟时间轴数据
        #     timelines = [{'start': 0, 'end': 10}]  # 可以根据实际需求调整
        #     self.add_videos([material_video_url], timelines, volume=0.3)
        
        # # 4.1. 视频音频停顿处理已完成，字幕已同步
        # video_subtitles_added = False
        # if hasattr(self, 'adjusted_subtitles') and self.adjusted_subtitles:
        #     print(f"[INFO] 视频音频停顿处理完成，字幕已同步")
        #     video_subtitles_added = True
        
        # 4.3. 添加背景音乐（如果提供）
        if background_music_path:
            print(f"[INFO] 准备添加背景音乐: {background_music_path}")
            try:
                self.add_background_music(background_music_path, volume=background_music_volume, time_offset=effective_offset)
                print(f"[OK] 背景音乐已成功添加: {background_music_path}")
            except Exception as e:
                print(f"[ERROR] 背景音乐添加失败: {e}")
                import traceback
                print(f"错误详情: {traceback.format_exc()}")
        else:
            print("📋 未提供背景音乐路径，跳过背景音乐添加")

        # 4.8 添加标题背景（根据模板配置）
        if hasattr(self, 'title_config') and self.title_config.get('bg_enabled', False):
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
                # 背景时长与标题一致：使用有效视频时长（确保不超过处理后视频长度，保留两位小数）
                effective_duration = self.get_effective_video_duration()
                display_duration = round(effective_duration if effective_duration > 0 else (self.audio_duration if self.audio_duration > 0 else 5.0), 6)
                
                # 验证背景时长不超过视频总时长
                display_duration = self._validate_duration_bounds(display_duration, "标题背景")
                self.add_styled_text_with_background(
                    text_content=multiline_text,
                    timerange_start=effective_offset,
                    timerange_duration=display_duration,
                    track_name="标题字幕背景",
                    position="center",
                    background_style=background_style,
                    text_transform_y=0.73,
                    line_spacing=4,
                    bg_height=0.48
                )
                print(f"[TEMPLATE] 已添加标题背景")
            except Exception as e:
                print(f"[ERROR] 添加标题背景失败: {e}")
        else:
            print(f"[TEMPLATE] 标题背景已禁用")
        
        # 5. 生成视频标题
        title = inputs.get('title', '')
        # 添加标题字幕（三行标题，第二行高亮）
        if title:
            effective_duration = self.get_effective_video_duration()
            title_duration = effective_duration if effective_duration > 0 else self.audio_duration
            print(f"添加三行标题: {title} (0s - {title_duration:.1f}s) [使用有效视频时长]")
            self.add_three_line_title(
                title=title,
                start=effective_offset,
                duration=title_duration,
                transform_y=0.72,
                line_spacing=4,
                track_name="标题字幕轨道"
            )
        
        
        # 6. 保存草稿
        self.script.save()
        
        # 计算执行时间并保存日志摘要
        # execution_time = time.time() - start_time
        # self.logger.info(f"🎉 工作流执行完成！耗时: {execution_time:.2f}秒")
        
        # # 记录字幕统计信息
        # if final_subtitles:
        #     self._log_subtitle_details(final_subtitles, "最终生成的")
        
        # 7. 轨道对齐处理：确保所有轨道都与主轴对齐且不得超过主轴
        # try:
        #     self._align_all_tracks_with_main_track(effective_offset)
        #     print(f"[OK] 所有轨道已与主轴对齐")
        # except Exception as e:
        #     print(f"[ERROR] 轨道对齐处理失败: {e}")
        
        # 保存工作流摘要
        try:
            execution_time = time.time() - start_time
            self._save_workflow_summary(inputs, self.script.save_path, execution_time)
        except Exception as e:
            self.logger.error(f"保存工作流摘要时出错: {e}")
        
        return self.script.save_path
    
    def _process_video_pauses_by_segments_marking(self, input_video_path: str, pause_segments: List[Tuple[float, float]], time_offset: float = 0.0) -> bool:
        """使用片段标记方式处理停顿（非破坏性编辑，不切割原视频）
        
        基于非破坏性编辑原理：
        1. 保持原视频文件完整不变
        2. 创建多个VideoSegment，每个标记不同的source_timerange
        3. 通过时间轴编排实现停顿移除效果
        
        Args:
            input_video_path: 输入视频路径
            pause_segments: 需要移除的停顿时间段列表 [(start1, end1), (start2, end2), ...]
            
        Returns:
            bool: 处理是否成功
        """
        print(f"[DEBUG] 开始使用非破坏性片段标记方式处理视频停顿")
        print(f"[DEBUG] 输入视频: {input_video_path}")
        print(f"[DEBUG] 需要移除的停顿段: {len(pause_segments)} 个")
        
        # 检查输入文件是否存在
        if not os.path.exists(input_video_path):
            print(f"[ERROR] 输入视频文件不存在: {input_video_path}")
            return False
        
        try:
            # 获取视频总时长
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', input_video_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"[ERROR] 无法获取视频时长: {result.stderr}")
                return False
                
            total_duration = float(result.stdout.strip())
            print(f"[DEBUG] 视频总时长: {total_duration:.3f} 秒")
            
            # 如果没有停顿段，直接添加完整视频
            if not pause_segments:
                print("[DEBUG] 没有停顿段需要移除，添加完整视频")
                self._add_single_video_segment(input_video_path, 0, total_duration, 0)
                return True
            
            # 第一步：处理和合并停顿片段
            print(f"[DEBUG] 第一步：处理需要移除的停顿片段")
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
            
            print(f"[DEBUG] 合并后需要移除的停顿片段: {len(merged_pauses)} 个")
            
            # 第二步：生成需要保留的有效片段
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
            
            # 处理最后一段
            if current_time < total_duration:
                valid_segments.append((current_time, total_duration))
                print(f"[DEBUG] 生成最后有效片段: [{current_time:.3f}s-{total_duration:.3f}s] (时长: {total_duration-current_time:.3f}s)")
            
            if not valid_segments:
                print("[DEBUG] 没有有效片段，视频将为空")
                return False
            
            print(f"[DEBUG] 共生成 {len(valid_segments)} 个有效片段")
            
            # 第三步：使用非破坏性片段标记方式添加到轨道
            print(f"[DEBUG] 第三步：使用非破坏性片段标记添加到轨道")
            
            current_timeline_offset = 0.0
            total_planned_duration = 0.0  # 记录计划总时长
            
            for i, (source_start, source_end) in enumerate(valid_segments):
                segment_duration = source_end - source_start
                
                print(f"[DEBUG] 添加片段 {i+1}: 源时间[{source_start:.3f}s-{source_end:.3f}s] -> 时间轴[{current_timeline_offset + time_offset:.3f}s-{current_timeline_offset + segment_duration + time_offset:.3f}s] (偏移: {time_offset:.6f}s)")
                
                # 创建VideoSegment，指定source_timerange和target_timerange
                success = self._add_video_segment_with_source_range(
                    video_path=input_video_path,
                    source_start=source_start,
                    source_duration=segment_duration,
                    target_start=current_timeline_offset,
                    segment_index=i,
                    time_offset=time_offset
                )
                
                if success:
                    print(f"[DEBUG] 片段 {i+1} 添加成功，时长: {segment_duration:.6f}s")
                    # 使用计划时长更新偏移和总时长（标记法不需要实际切割）
                    current_timeline_offset += segment_duration
                    total_planned_duration += segment_duration
                else:
                    print(f"[ERROR] 片段 {i+1} 添加失败")
                    return False
            
            print(f"[DEBUG] 所有片段添加完成，总时长: {total_planned_duration:.6f}s")
            
            # 更新视频和项目时长 - 使用计划总时长（标记法）
            old_duration = self.video_duration
            self.video_duration = total_planned_duration
            self._update_project_duration()
            print(f"[VIDEO_DURATION] 非破坏性标记: {old_duration:.6f}s -> {self.video_duration:.6f}s (计划: {total_planned_duration:.6f}s)")
            print(f"[DEBUG] 更新项目时长为: {self.project_duration:.6f}s")
            
            print(f"[OK] 非破坏性片段标记处理完成")
            return True
            
        except Exception as e:
            print(f"[ERROR] 非破坏性片段标记处理失败: {e}")
            import traceback
            traceback.print_exc()
            return False
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
            import time
            import threading
            
            # 使用更安全的唯一ID生成方式，避免并发冲突
            timestamp = int(time.time() * 1000000)  # 微秒时间戳
            thread_id = threading.get_ident() % 100000  # 线程ID后5位
            random_id = uuid.uuid4().hex[:8]
            segment_id = f"{timestamp}_{thread_id}_{random_id}"
            
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
                    # 提高精度到9位小数，确保帧级精度
                    cmd = [
                        'ffmpeg', '-ss', f"{start:.9f}", '-to', f"{start + duration:.9f}",
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
                        '-vsync', 'cfr',  # 强制恒定帧率，避免帧数不匹配
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
    
    def _add_video_segment_with_source_range(self, video_path: str, 
                                           source_start: float, source_duration: float, 
                                           target_start: float, segment_index: int, 
                                           time_offset: float = 0.0) -> bool:
        """使用VideoSegment添加指定源时间范围的视频片段（非破坏性编辑）
        
        Args:
            video_path: 视频文件路径
            source_start: 源视频开始时间（秒）
            source_duration: 源片段持续时间（秒）
            target_start: 目标时间轴开始时间（秒）
            segment_index: 片段索引（用于调试）
            
        Returns:
            bool: 是否成功添加
        """
        try:
            print(f"[DEBUG] 添加视频片段 {segment_index+1}: 源[{source_start:.3f}s+{source_duration:.3f}s] -> 目标[{target_start:.3f}s+{source_duration:.3f}s]")
            
            # 检查视频时长边界，避免超出素材时长
            video_material = draft.VideoMaterial(video_path)
            material_duration_seconds = video_material.duration / 1000000
            
            # 如果源片段结束时间超出视频时长，进行调整
            source_end = source_start + source_duration
            if source_end > material_duration_seconds:
                print(f"[WARN] 源片段结束时间 {source_end:.3f}s 超出视频时长 {material_duration_seconds:.3f}s，进行调整")
                # 调整源片段持续时间
                source_duration = material_duration_seconds - source_start
                if source_duration <= 0:
                    print(f"[ERROR] 调整后源片段持续时间 <= 0，跳过此片段")
                    return False
                print(f"[DEBUG] 调整后源片段: [{source_start:.3f}s+{source_duration:.3f}s]")
            
            # 应用时间偏移到目标时间
            adjusted_target_start = target_start + time_offset
            
            # 创建VideoSegment，指定源时间范围和目标时间范围
            # 使用更高精度避免帧数不匹配问题
            video_segment = draft.VideoSegment(
                video_path,
                # target_timerange: 在轨道上的位置（应用时间偏移）
                trange(tim(f"{adjusted_target_start:.9f}s"), tim(f"{source_duration:.9f}s")),
                # source_timerange: 从源视频中截取的范围
                source_timerange=trange(tim(f"{source_start:.9f}s"), tim(f"{source_duration:.9f}s"))
            )
            
            # 添加到主视频轨道（与数字人视频在同一轨道统一管理）
            self.script.add_segment(video_segment, track_name="主视频轨道")
            
            print(f"[DEBUG] 片段 {segment_index+1} 添加成功 (偏移: {time_offset:.6f}s)")
            return True
            
        except Exception as e:
            print(f"[ERROR] 添加视频片段 {segment_index+1} 失败: {e}")
            return False
    
    def _add_single_video_segment(self, video_path: str, start_time: float, 
                                duration: float, target_start: float) -> bool:
        """添加单个视频片段（完整视频或单一片段的情况）
        
        Args:
            video_path: 视频文件路径
            start_time: 开始时间（秒）
            duration: 持续时间（秒）
            target_start: 目标时间轴开始时间（秒）
            
        Returns:
            bool: 是否成功添加
        """
        try:
            print(f"[DEBUG] 添加单个视频片段: [{start_time:.3f}s-{start_time+duration:.3f}s] -> 目标[{target_start:.3f}s+{duration:.3f}s]")
            
            # 创建VideoSegment - 使用更高精度避免帧数不匹配
            video_segment = draft.VideoSegment(
                video_path,
                trange(tim(f"{target_start:.9f}s"), tim(f"{duration:.9f}s")),
                source_timerange=trange(tim(f"{start_time:.9f}s"), tim(f"{duration:.9f}s"))
            )
            
            # 添加到主视频轨道（与数字人视频在同一轨道统一管理）
            self.script.add_segment(video_segment, track_name="主视频轨道")
            
            print(f"[DEBUG] 单个视频片段添加成功")
            return True
            
        except Exception as e:
            print(f"[ERROR] 添加单个视频片段失败: {e}")
            return False
    
    def _adjust_subtitle_timings(self, original_subtitles: List[Dict[str, Any]], 
                                pause_segments: List[Tuple[float, float]], 
                                time_offset: float = 0.0) -> List[Dict[str, Any]]:
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

            # 1) 先排序，保证时间单调
            sorted_subs = sorted(original_subtitles, key=lambda s: (s.get('start', 0.0), s.get('end', 0.0)))

            # 2) 预处理停顿段，按开始时间排序，便于累计
            pauses = sorted([(float(ps), float(pe)) for ps, pe in pause_segments], key=lambda x: x[0])

            def map_time(t: float) -> float:
                """将原始时间映射到移除停顿后的时间轴。
                计算所有在 t 之前完全结束的停顿总时长；
                若 t 落在某个停顿内，则只减去该段中从开头到 t 的部分。"""
                removed = 0.0
                for ps, pe in pauses:
                    if pe <= t:
                        removed += (pe - ps)
                    elif ps < t < pe:
                        removed += (t - ps)
                        break
                    elif ps >= t:
                        break
                return t - removed

            adjusted_subtitles: List[Dict[str, Any]] = []
            prev_end = -0.01
            min_gap = 0.01  # 10ms 缝隙，避免重叠
            min_dur = 0.05  # 至少 50ms 避免 0 时长

            for sub in sorted_subs:
                original_start = float(sub['start'])
                original_end = float(sub['end'])

                # 3) 做时间映射并加偏移
                ns = map_time(original_start) + float(time_offset or 0.0)
                ne = map_time(original_end) + float(time_offset or 0.0)

                # 4) 归一化 & 非负
                ns = max(0.0, ns)
                ne = max(ns, ne)

                # 5) 防重叠裁剪（与前一段保持最小间隔）
                if ns < prev_end + min_gap:
                    ns = prev_end + min_gap
                if ne < ns + min_dur:
                    ne = ns + min_dur

                # 6) 保留两位小数（和上游一致），并再次保证不反转
                ns = round(ns, 2)
                ne = round(max(ns, ne), 2)

                adjusted_subtitles.append({'text': sub['text'], 'start': ns, 'end': ne})
                prev_end = ne

                print(f"[DEBUG] 字幕调整: {sub['text']}")
                print(f"   原始时间: {original_start:.2f}s - {original_end:.2f}s")
                print(f"   调整时间: {ns:.2f}s - {ne:.2f}s (偏移: {time_offset:.6f}s)")

            print(f"[DEBUG] 字幕时间轴调整完成，共 {len(adjusted_subtitles)} 段字幕")
            return adjusted_subtitles
            
        except Exception as e:
            print(f"[DEBUG] 字幕时间轴调整失败: {e}")
            return original_subtitles  # 失败时返回原始字幕

    def add_cover(self, cover_image_path: str = None, frames: int = 2, fps: int = 30, 
                  top_text: str = None, bottom_text: str = None):
        """完整的封面添加功能
        
        Args:
            cover_image_path: 封面图片路径，如果为None则使用默认路径
            frames: 封面帧数，默认2帧
            fps: 帧率，默认30fps
            top_text: 上方字幕文本
            bottom_text: 下方字幕文本
            
        Returns:
            dict: 封面处理结果
                {
                    'success': bool,          # 是否成功
                    'cover_duration': float,  # 封面时长（秒）
                    'time_offset': float,     # 时间偏移量（秒）
                    'cover_enabled': bool     # 封面是否启用
                }
        """
        result = {
            'success': False,
            'cover_duration': 0.0,
            'time_offset': 0.0,
            'cover_enabled': False
        }
        
        # 检查是否启用封面
        if not cover_image_path and not top_text and not bottom_text:
            print("[INFO] 未提供封面参数，跳过封面添加")
            result['success'] = True  # 未启用也算成功
            return result
        
        try:
            # 1. 启用封面功能
            self.enable_cover(cover_image_path, frames, fps)
            self.cover_enabled = True  # 确保启用封面
            result['cover_enabled'] = True
            result['cover_duration'] = self.cover_duration
            result['time_offset'] = self.cover_duration
            
            print(f"[INFO] 开始添加封面...")
            
            # 2. 添加封面图片（如果提供了图片路径）
            if cover_image_path:
                image_segment = self.add_cover_image()
                if image_segment is None:
                    print("[WARN] 封面图片添加失败，继续添加字幕")
                else:
                    print(f"[OK] 封面图片添加成功")
            
            # 3. 添加封面字幕（如果提供了字幕文本）
            if top_text or bottom_text:
                subtitle_segments = self.add_cover_subtitles(top_text, bottom_text)
                if subtitle_segments:
                    print(f"[OK] 封面字幕添加成功: {len(subtitle_segments)} 段")
                else:
                    print("[WARN] 封面字幕添加失败")
            
            # 4. 设置时间偏移，供后续内容使用
            self.time_offset = self.cover_duration

            
            result['success'] = True
            print(f"[OK] 封面添加完成")
            print(f"   - 封面时长: {self.cover_duration:.6f}秒")
            print(f"   - 后续内容时间偏移: {self.time_offset:.6f}秒")
            print(f"   - 封面图片: {'已添加' if cover_image_path else '未添加'}")
            print(f"   - 封面字幕: {'已添加' if (top_text or bottom_text) else '未添加'}")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 封面添加失败: {e}")
            import traceback
            print(f"[ERROR] 错误详情: {traceback.format_exc()}")
            return result

    def enable_cover(self, cover_image_path: str = None, frames: int = 2, fps: int = 30):
        """启用封面功能
        
        Args:
            cover_image_path: 封面图片路径，如果为None则使用默认路径
            frames: 封面帧数，默认2帧
            fps: 帧率，默认30fps
        """
        self.cover_enabled = True
        self.cover_duration = frames / fps  # 计算封面时长
        
        if cover_image_path is None:
            # 使用默认封面路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, '..', '..')
            self.cover_image_path = os.path.join(project_root, 'resource', '查封面.jpg')
        else:
            # 使用传入的封面路径
            if not os.path.isabs(cover_image_path):
                # 如果是相对路径，相对于项目根目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.join(current_dir, '..', '..')
                self.cover_image_path = os.path.join(project_root, cover_image_path)
            else:
                # 绝对路径直接使用
                self.cover_image_path = cover_image_path
        
        print(f"[INFO] 封面已启用: 时长{self.cover_duration:.3f}秒 ({frames}帧@{fps}fps)")
        print(f"[INFO] 封面图片路径: {self.cover_image_path}")
    
    def add_cover_image(self):
        """添加封面图片到主视频轨道"""
        if not self.cover_enabled or not self.cover_image_path:
            return None
        
        if not os.path.exists(self.cover_image_path):
            print(f"[ERROR] 封面图片不存在: {self.cover_image_path}")
            return None
        
        try:
            # 创建图片素材（使用VideoMaterial处理图片）
            image_material = draft.VideoMaterial(self.cover_image_path)
            
            # 创建图片片段，从0开始
            image_segment = draft.VideoSegment(
                image_material,
                draft.trange(draft.tim("0s"), draft.tim(f"{self.cover_duration:.6f}s"))
            )
            
            # 添加到主视频轨道
            self.script.add_segment(image_segment, track_name="主视频轨道")
            
            print(f"[OK] 封面图片已添加: {os.path.basename(self.cover_image_path)}")
            return image_segment
            
        except Exception as e:
            print(f"[ERROR] 添加封面图片失败: {e}")
            return None
    
    def add_cover_subtitles(self, top_text: str = None, bottom_text: str = None):
        """添加封面字幕
        
        Args:
            top_text: 上方字幕文本（添加到标题字幕轨道）
            bottom_text: 下方字幕文本（添加到内容字幕轨道）
        """
        if not self.cover_enabled:
            return []
        
        segments = []
        
        try:
            # 添加上方字幕到标题字幕轨道
            if top_text:
                # 按模板控制封面标题阴影
                cover_title_shadow = None
                try:
                    if hasattr(self, 'cover_config') and self.cover_config.get('title_shadow_enabled', False):
                        cover_title_shadow = draft.TextShadow(
                            alpha=0.8,
                            color=(0.0, 0.0, 0.0),
                            diffuse=20.0,
                            distance=10.0,
                            angle=-45.0
                        )
                except Exception:
                    cover_title_shadow = None

                top_segment = draft.TextSegment(
                    top_text,
                    draft.trange(draft.tim("0s"), draft.tim(f"{self.cover_duration:.6f}s")),
                    font=draft.FontType.阳华体,
                    style=draft.TextStyle(
                        size=15.0,
                        color=(1.0, 1.0, 1.0),  # 白色
                        bold=True,
                        align=0,  # 居中对齐
                       
                        max_line_width=0.9
                    ),
                    clip_settings=draft.ClipSettings(transform_y=0.55, scale_x=1.9, scale_y=1.9),  # 上方位置
                    shadow=cover_title_shadow
                )
                self.script.add_segment(top_segment, track_name="标题字幕轨道")
                segments.append(top_segment)
                print(f"[OK] 封面上方字幕已添加: {top_text}")
            
            # 添加下方字幕到内容字幕轨道（分两段：第一段黄色高亮，第二段白色）
            if bottom_text:
                # 将文本分为两段，用换行符分隔
                text_parts = bottom_text.split('\n', 1)  # 最多分割一次
                if len(text_parts) == 1:
                    # 如果没有换行符，默认第一段为前一半，第二段为后一半
                    mid_point = len(bottom_text) // 2
                    # 寻找合适的分割点（空格或标点）
                    for i in range(mid_point - 5, mid_point + 5):
                        if i < len(bottom_text) and bottom_text[i] in [' ', '，', '。', '！', '？', '、']:
                            mid_point = i + 1
                            break
                    text_parts = [bottom_text[:mid_point], bottom_text[mid_point:]]
                
                first_part = text_parts[0].strip()
                second_part = text_parts[1].strip() if len(text_parts) > 1 else ""
                
                # 组合文本：第一段 + 换行 + 第二段
                combined_text = first_part + "\n      " + second_part if second_part else first_part
                
                # 创建富文本样式
                highlight_ranges = []
                
                # 第一段：黄色高亮
                if first_part:
                    highlight_ranges.append(draft.TextStyleRange(
                        start=0,
                        end=len(first_part),
                        color=(1.0, 0.9372549019607843, 0.1725490196078431),  # #ffef2c 黄色高亮
                        size=14,
                        bold=True,
                        italic=False,
                        underline=False
                    ))
                
                # 第二段：白色（如果有的话）
                if second_part:
                    second_start = len(first_part) + 1  # +1 是换行符
                    highlight_ranges.append(draft.TextStyleRange(
                        start=second_start,
                        end=second_start + len(second_part),
                        color=(1.0, 1.0, 1.0),  # 白色
                        size=14,
                        bold=True,
                        italic=False,
                        underline=False
                    ))
                
                # 按模板控制封面副标题阴影
                cover_subtitle_shadow = None
                try:
                    if hasattr(self, 'cover_config') and self.cover_config.get('subtitle_shadow_enabled', False):
                        cover_subtitle_shadow = draft.TextShadow(
                            alpha=0.8,
                            color=(0.0, 0.0, 0.0),
                            diffuse=20.0,
                            distance=10.0,
                            angle=-45.0
                        )
                except Exception:
                    cover_subtitle_shadow = None

                bottom_segment = draft.TextSegment(
                    combined_text,
                    draft.trange(draft.tim("0s"), draft.tim(f"{self.cover_duration:.6f}s")),
                    font=draft.FontType.点宋体,
                    style=draft.TextStyle(
                        size=14,
                        color=(1.0, 1.0, 1.0),  # 默认白色
                        bold=True,
                        align=0,  # 左对齐
                        max_line_width=0.9,
                        line_spacing=4  # 行间距4
                    ),
                    clip_settings=draft.ClipSettings(transform_y=-0.48, scale_x=1.21, scale_y=1.21),  # 下方位置
                    shadow=cover_subtitle_shadow
                )
                
                # 手动设置高亮范围
                bottom_segment.highlight_ranges = highlight_ranges
                self.script.add_segment(bottom_segment, track_name="内容字幕轨道")
                segments.append(bottom_segment)
                print(f"[OK] 封面下方字幕已添加（分两段）: '{first_part}' + '{second_part}'")
            
            print(f"[INFO] 📝 封面字幕已添加: 上方='{top_text}', 下方='{bottom_text}'")
            
        except Exception as e:
            print(f"[ERROR] 添加封面字幕失败: {e}")
        
        return segments
    
   
    


def main():
    """主函数 - 音频转录智能字幕工作流"""
    # 配置剪映草稿文件夹路径（需要根据实际情况修改）
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 创建工作流实例
    workflow = VideoEditingWorkflow(draft_folder_path, "audio_transcription_demo")
    
    # 配置华尔兹背景音乐路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    background_music_path = os.path.join(project_root, 'resource\华尔兹.mp3')
    
    # 配置输入参数
    inputs = {
        # 'digital_video_url': 'https://oss.oemi.jdword.com/prod/order/video/202509/V20250901153106001.mp4',
        # 'audio_url': 'https://oss.oemi.jdword.com/prod/temp/srt/V20250901152556001.wav',
        # 'title': '火山引擎ASR智能字幕演示',
        # "audio_url": "https://oss.oemi.jdword.com/prod/temp/srt/V20250904223919001.wav",
        "content": "你们说现在大家都不敢买房，会不会就是最好的买房时候呀？然后大家都要买房的时候，反而房子不能买了吧。今年是十四五计划的最后一年，马上迎来十五五计划。我总觉得最近楼市这两个月有点过于风平浪静了，有没有可能再悄悄的憋大招呀？",

        "digital_video_url": "https://oss.oemi.jdword.com/prod/order/video/202509/V20250908011407003.mp4",     
        "title": "大家不买时买房大家买时不买对吗",




        
        # 🔥 火山引擎ASR配置（用于语音识别）
        'volcengine_appid': '6046310832',                # 火山引擎ASR AppID
        'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',  # 火山引擎ASR AccessToken
        
        # 🤖 豆包API配置（用于关键词提取）
        'doubao_token': 'adac0afb-5fd4-4c66-badb-370a7ff42df5',  # 请替换为您的豆包API token
        'doubao_model': 'doubao-1-5-pro-32k-250115',  # 豆包模型名称
        
        # [INFO] 背景音乐配置
        'background_music_path': background_music_path,  # 华尔兹.mp3路径
        'background_music_volume': 0.25,  # 背景音乐音量,

        # 1.1 处理封面（如果提供了 cover_short_title/cover_image_path/cover_bottom_text）
        'cover_short_title': '买房须知',
        'cover_image_path': 'resource/查封面.jpg',
        'cover_bottom_text': '买房子该怎么买\n     一定要牢记'
        
    }
    
    try:
        print(f"\n[INFO] 开始处理工作流...")
        
        # 先创建草稿
        workflow.create_draft()
        print(f"[OK] 草稿创建成功")
        
        # 添加封面
        # cover_result = workflow.add_cover(
        #     cover_image_path="resource/查封面.jpg",
        #     frames=2,
        #     fps=30,
        #     top_text="买房须知",
        #     bottom_text="买房子该怎么买\n     一定要牢记"
        # )
        # 计算封面时长作为时间偏移
        # cover_duration = cover_result['cover_duration']
        # 创建示例模板配置
        template_config = {
            'title_config': {
                'color': '#FF0000',
                'highlight_color': '#FFFF00',
                'bg_enabled': True,
                'font': '阳华体',
                'font_size': 24.0,
                'scale': 1.2,
                'line_spacing': 1.5
            },
            'subtitle_config': {
                'color': '#FFFFFF',
                'highlight_color': '#00FF00',
                'bg_enabled': False,
                'font': '俪金黑',
                'font_size': 18.0,
                'scale': 1.0
            },
            'cover_config': {
                'background': '',
                'title_font': '阳华体',
                'title_color': '#FFFFFF',
                'title_size': 28.0,
                'subtitle_font': '俪金黑',
                'subtitle_color': '#CCCCCC',
                'subtitle_size': 20.0
            }
        }
        
        save_path = workflow.process_workflow(inputs, template_config=template_config)
        print(f"\n[OK] 音频转录工作流完成!")
        print(f"剪映项目已保存到: {save_path}")
        print("[INFO] 请打开剪映查看生成的智能字幕视频项目")
        
    except Exception as e:
        print(f"[ERROR] 工作流失败: {e}")
        import traceback
        traceback.print_exc()

    def _align_all_tracks_with_main_track(self, time_offset: float = 0.0):
        """确保所有轨道都与主轴对齐且不得超过主轴
        
        Args:
            time_offset: 时间偏移（秒）
        """
        if not self.script:
            print("[WARN] 草稿不存在，跳过轨道对齐处理")
            return
        
        # 获取主轴（主视频轨道）的时长
        main_track_duration = self.get_effective_video_duration()
        if main_track_duration <= 0:
            print("[WARN] 主轴时长无效，跳过轨道对齐处理")
            return
        
        # 计算主轴的时间范围
        main_track_start = time_offset
        main_track_end = time_offset + main_track_duration
        
        print(f"[TRACK_ALIGNMENT] 主轴时间范围: {main_track_start:.6f}s - {main_track_end:.6f}s (时长: {main_track_duration:.6f}s)")
        
        # 需要检查的轨道列表
        tracks_to_check = [
            "音频轨道",
            "背景音乐轨道", 
            "内容字幕轨道",
            "标题字幕轨道",
            "内容字幕背景",
            "标题字幕背景"
        ]
        
        alignment_count = 0
        
        for track_name in tracks_to_check:
            try:
                if track_name in self.script.tracks:
                    track = self.script.tracks[track_name]
                    segments_adjusted = 0
                    
                    for segment in track.segments:
                        # 获取片段的当前时间范围
                        current_start = segment.time_range.start / 1000000  # 转换为秒
                        current_duration = segment.time_range.duration / 1000000  # 转换为秒
                        current_end = current_start + current_duration
                        
                        # 检查是否需要调整
                        needs_adjustment = False
                        new_start = current_start
                        new_end = current_end
                        
                        # 如果片段开始时间早于主轴开始时间，调整到主轴开始时间
                        if current_start < main_track_start:
                            new_start = main_track_start
                            needs_adjustment = True
                        
                        # 如果片段结束时间晚于主轴结束时间，调整到主轴结束时间
                        if current_end > main_track_end:
                            new_end = main_track_end
                            needs_adjustment = True
                        
                        # 如果片段完全在主轴范围外，跳过
                        if current_end <= main_track_start or current_start >= main_track_end:
                            print(f"[TRACK_ALIGNMENT] {track_name} 片段超出主轴范围，跳过")
                            continue
                        
                        # 应用调整
                        if needs_adjustment:
                            new_duration = new_end - new_start
                            if new_duration > 0:
                                # 更新片段的时间范围
                                segment.time_range = draft.trange(
                                    draft.tim(f"{new_start:.9f}s"),
                                    draft.tim(f"{new_duration:.9f}s")
                                )
                                segments_adjusted += 1
                                
                                print(f"[TRACK_ALIGNMENT] {track_name} 片段调整: {current_start:.6f}s-{current_end:.6f}s -> {new_start:.6f}s-{new_end:.6f}s")
                    
                    if segments_adjusted > 0:
                        alignment_count += 1
                        print(f"[TRACK_ALIGNMENT] {track_name}: 调整了 {segments_adjusted} 个片段")
                    else:
                        print(f"[TRACK_ALIGNMENT] {track_name}: 无需调整")
                        
                else:
                    print(f"[TRACK_ALIGNMENT] {track_name}: 轨道不存在，跳过")
                    
            except Exception as e:
                print(f"[ERROR] 调整轨道 {track_name} 时出错: {e}")
        
        print(f"[TRACK_ALIGNMENT] 轨道对齐处理完成，共调整了 {alignment_count} 个轨道")



def test_cover_function():
    """测试封面功能"""
    print("="*60)
    print("封面功能测试")
    print("="*60)
    
    # 配置剪映草稿文件夹路径
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 创建工作流实例
    workflow = VideoEditingWorkflow(draft_folder_path, "cover_test")
    
    try:
        # 1. 创建草稿
        workflow.create_draft()
        print("[OK] 草稿创建成功")
        
        # 2. 测试封面功能
        cover_result = workflow.add_cover(
            cover_image_path="resource/查封面.jpg",
            frames=2,
            fps=30,
            top_text="买房须知",
            bottom_text="买房子该怎么买\n     一定要牢记"
        )
        
        print(f"\n封面处理结果:")
        print(f"  - 成功: {cover_result['success']}")
        print(f"  - 封面时长: {cover_result['cover_duration']:.6f}秒")
        print(f"  - 时间偏移: {cover_result['time_offset']:.6f}秒")
        print(f"  - 封面启用: {cover_result['cover_enabled']}")
        
        # 3. 保存草稿
        workflow.script.save()
        print(f"\n[OK] 封面测试完成！")
        print("请打开剪映查看生成的封面项目")
        
    except Exception as e:
        print(f"[ERROR] 封面测试失败: {e}")
        import traceback
        traceback.print_exc()



if __name__ == "__main__":
    # 运行主工作流
    main()
    
    # 运行封面功能测试
    # test_cover_function()