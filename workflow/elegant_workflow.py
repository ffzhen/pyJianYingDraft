"""
优雅的视频编辑工作流

重构后的主工作流，采用模块化设计
"""

import os
import sys
import time
from typing import Dict, Any, Optional

# 添加本地 pyJianYingDraft 模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

import pyJianYingDraft as draft
from pyJianYingDraft import TrackType, FontType
from typing import Dict, Any, List, Tuple

# 导入新的模块化组件
try:
    # 相对导入（当作为包使用时）
    from .core import WorkflowContext, WorkflowLogger, WorkflowConfig
    from .core.exceptions import WorkflowError, ValidationError, ProcessingError
    from .managers import DurationManager, TrackManager, MaterialManager
    from .processors import AudioProcessor, VideoProcessor, SubtitleProcessor, PauseProcessor
except ImportError:
    # 绝对导入（当直接运行时）
    from workflow.core import WorkflowContext, WorkflowLogger, WorkflowConfig
    from workflow.core.exceptions import WorkflowError, ValidationError, ProcessingError
    from workflow.managers import DurationManager, TrackManager, MaterialManager
    from workflow.processors import AudioProcessor, VideoProcessor, SubtitleProcessor, PauseProcessor


class ElegantVideoWorkflow:
    """优雅的视频编辑工作流
    
    采用模块化设计，职责分离，易于扩展和测试
    """
    
    def __init__(self, config: WorkflowConfig):
        """初始化工作流
        
        Args:
            config: 工作流配置
        """
        # 验证配置
        config.validate()
        
        self.config = config
        self.context = WorkflowContext()
        self.logger = WorkflowLogger(config.project_name)
        
        # 初始化管理器
        self.duration_manager = DurationManager(self.context, self.logger)
        self.track_manager = TrackManager(self.context, self.logger)
        self.material_manager = MaterialManager(self.context, self.logger)
        
        # 初始化处理器
        self.audio_processor = AudioProcessor(self.context, self.logger)
        self.video_processor = VideoProcessor(self.context, self.logger)
        self.subtitle_processor = SubtitleProcessor(self.context, self.logger)
        self.pause_processor = PauseProcessor(self.context, self.logger)
        
        # 初始化草稿文件夹
        self.draft_folder = draft.DraftFolder(config.draft_folder_path)
        
        self.logger.info(f"🏗️ 优雅工作流已初始化 - 项目: {config.project_name}")
        
    def create_draft(self) -> Any:
        """创建剪映草稿"""
        try:
            self.context.script = self.draft_folder.create_draft(
                self.config.project_name, 
                self.config.video_width, 
                self.config.video_height, 
                allow_replace=True
            )
        except PermissionError:
            # 可能存在 .locked 文件或草稿被占用；回退为时间戳新名称避免冲突
            from datetime import datetime
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fallback_name = f"{self.config.project_name}_{ts}"
            self.logger.warning(f"发现锁定文件或占用，切换到新项目名称: {fallback_name}")
            self.config.project_name = fallback_name
            self.context.script = self.draft_folder.create_draft(
                self.config.project_name, 
                self.config.video_width, 
                self.config.video_height, 
                allow_replace=False
            )
        except Exception as e:
            # 其他异常也尝试使用时间戳新名称
            from datetime import datetime
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fallback_name = f"{self.config.project_name}_{ts}"
            self.logger.warning(f"创建草稿失败({e})，改用新项目名称: {fallback_name}")
            self.config.project_name = fallback_name
            self.context.script = self.draft_folder.create_draft(
                self.config.project_name, 
                self.config.video_width, 
                self.config.video_height, 
                allow_replace=False
            )
        
        # 创建基础轨道
        self.track_manager.create_basic_tracks()
        
        self.logger.info("📋 草稿创建完成")
        return self.context.script
    
    def add_audio(self, audio_url: str, **kwargs) -> Any:
        """添加音频"""
        return self.audio_processor.add_audio(audio_url, **kwargs)
        
    def add_background_music(self, music_path: str, **kwargs) -> Any:
        """添加背景音乐"""
        return self.audio_processor.add_background_music(music_path, **kwargs)
        
    def add_video(self, video_url: str, **kwargs) -> Any:
        """添加主视频"""
        return self.video_processor.add_video(video_url, **kwargs)
        
    def add_digital_human_video(self, digital_human_url: str, **kwargs) -> Any:
        """添加数字人视频"""
        return self.video_processor.add_digital_human_video(digital_human_url, **kwargs)
        
    def add_subtitle_from_asr(self, asr_result: List[Dict[str, Any]], **kwargs) -> Any:
        """从ASR结果添加字幕"""
        return self.subtitle_processor.add_subtitle_from_asr(asr_result, **kwargs)
        
    def add_title_subtitle(self, title: str, **kwargs) -> Any:
        """添加标题字幕"""
        return self.subtitle_processor.add_title_subtitle(title, **kwargs)
        
    def apply_natural_pauses(self, asr_result: List[Dict[str, Any]], **kwargs) -> Any:
        """应用自然停顿"""
        return self.pause_processor.apply_natural_pauses(asr_result, **kwargs)
    
    def initialize_asr(self, volcengine_appid: str, volcengine_access_token: str,
                       doubao_token: str = None, doubao_model: str = "doubao-1-5-pro-32k-250115"):
        """初始化ASR功能"""
        self.audio_processor.initialize_asr(volcengine_appid, volcengine_access_token, doubao_token, doubao_model)
        self.logger.info(f"🔥 火山引擎ASR已在优雅工作流中初始化")
    
    def transcribe_audio_and_generate_subtitles(self, audio_url: str) -> List[Dict[str, Any]]:
        """音频转录并生成字幕"""
        return self.audio_processor.transcribe_audio(audio_url)
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        return self.audio_processor.extract_keywords(text)
    
    def add_captions_with_highlights(self, caption_data: List[Dict[str, Any]], **kwargs):
        """添加带高亮的字幕"""
        return self.subtitle_processor.add_captions_with_highlights(caption_data, **kwargs)
    
    def add_caption_backgrounds(self, caption_data: List[Dict[str, Any]], **kwargs):
        """添加字幕背景"""
        return self.subtitle_processor.add_caption_backgrounds(caption_data, **kwargs)
    
    def add_three_line_title_subtitle(self, title: str, **kwargs):
        """添加三行标题字幕"""
        return self.subtitle_processor.add_three_line_title(title, **kwargs)
    
    def process_complete_workflow(self, inputs: Dict[str, Any]) -> str:
        """处理完整工作流 - 集成ASR转录、关键词高亮、停顿移除等功能
        
        Args:
            inputs: 输入参数字典，支持的参数：
                - audio_url: 音频URL（必需）
                - digital_human_url: 数字人视频URL
                - video_url: 主视频URL
                - background_music_path: 背景音乐路径
                - background_music_volume: 背景音乐音量(0-1)
                - title: 标题文本
                - title_duration: 标题显示时长(秒)
                - volcengine_appid: 火山引擎ASR AppID（必需）
                - volcengine_access_token: 火山引擎ASR AccessToken（必需）
                - doubao_token: 豆包API Token（用于关键词提取）
                - doubao_model: 豆包模型名称
                - subtitle_delay: 字幕延迟（秒），正值延后，负值提前
                - subtitle_speed: 字幕速度系数，>1加快，<1减慢
                - remove_pauses: 是否移除音频停顿
                - pause_intensity: 停顿强度(0-1)
            
        Returns:
            草稿保存路径
        """
        start_time = time.time()
        
        try:
            self.logger.info("🚀 开始处理完整优雅工作流（集成ASR转录、关键词高亮）")
            self.logger.info(f"📋 输入参数: {self._format_inputs_for_log(inputs)}")
            
            # 验证必需参数
            audio_url = inputs.get('audio_url')
            volcengine_appid = inputs.get('volcengine_appid')
            volcengine_access_token = inputs.get('volcengine_access_token')
            
            if not audio_url:
                raise WorkflowError("audio_url 是必需参数，用于音频转录")
            
            if not volcengine_appid or not volcengine_access_token:
                raise WorkflowError("必须提供 volcengine_appid 和 volcengine_access_token 参数")
            
            # 初始化ASR
            doubao_token = inputs.get('doubao_token')
            doubao_model = inputs.get('doubao_model', 'doubao-1-5-pro-32k-250115')
            
            self.initialize_asr(volcengine_appid, volcengine_access_token, doubao_token, doubao_model)
            
            # 1. 创建草稿
            self.create_draft()
            
            # 2. 添加数字人视频（如果有）
            digital_human_url = inputs.get('digital_human_url')
            if digital_human_url:
                self.logger.info(f"🤖 添加数字人视频: {digital_human_url}")
                self.add_digital_human_video(digital_human_url)
            
            # 3. 添加主视频（如果有）
            video_url = inputs.get('video_url')
            if video_url:
                self.logger.info(f"🎬 添加主视频: {video_url}")
                self.add_video(video_url)
            
            # 4. 进行音频转录生成字幕
            self.logger.info("🎤 开始音频转录生成字幕")
            subtitle_objects = self.transcribe_audio_and_generate_subtitles(audio_url)
            
            if not subtitle_objects:
                raise WorkflowError("音频转录失败，无法生成字幕")
            
            self.logger.info(f"✅ 音频转录成功，生成 {len(subtitle_objects)} 段字幕")
            
            # 5. 调整字幕时间（如果需要）
            subtitle_delay = inputs.get('subtitle_delay', 0.0)
            subtitle_speed = inputs.get('subtitle_speed', 1.0)
            
            final_subtitles = subtitle_objects
            if subtitle_delay != 0.0 or subtitle_speed != 1.0:
                self.logger.info(f"⏰ 调整字幕时间: 延迟{subtitle_delay:.1f}s, 速度{subtitle_speed:.1f}x")
                final_subtitles = self._adjust_subtitle_timing(final_subtitles, subtitle_delay, subtitle_speed)
            
            # 6. 提取关键词用于高亮
            self.logger.info("🤖 开始AI关键词提取...")
            all_text = " ".join([sub['text'] for sub in final_subtitles])
            keywords = self.extract_keywords(all_text)
            
            if keywords:
                self.logger.info(f"✅ AI提取到 {len(keywords)} 个关键词: {keywords}")
            else:
                self.logger.warning("⚠️ 未提取到关键词，使用普通字幕")
            
            # 7. 添加带关键词高亮的字幕
            self.logger.info("📝 添加带关键词高亮的字幕")
            self.add_captions_with_highlights(
                caption_data=final_subtitles,
                track_name="内容字幕轨道",
                position="bottom",
                keywords=keywords,
                base_color=(1.0, 1.0, 1.0),  # 白色
                base_font_size=8.0,  # 8号
                font_type=draft.FontType.俪金黑,  # 俪金黑
                highlight_size=10.0,  # 高亮10号
                highlight_color=(1.0, 0.7529411765, 0.2470588235),  # #ffc03f
                scale=1.39
            )
            
            # 8. 为字幕添加背景色块
            self.logger.info("🎨 添加字幕背景")
            self.add_caption_backgrounds(
                caption_data=final_subtitles,
                position="bottom",
                bottom_transform_y=-0.3,
                scale=1.39
            )
            
            # 9. 添加标题字幕（如果有）
            title = inputs.get('title')
            if title:
                title_duration = inputs.get('title_duration', None)  # 使用有效视频时长
                self.logger.info(f"🏷️ 添加三行标题字幕: {title}")
                self.add_three_line_title_subtitle(
                    title=title,
                    start=0.0,
                    duration=title_duration,
                    transform_y=0.72,
                    line_spacing=4,
                    highlight_color=(1.0, 0.7529411765, 0.2470588235)  # #ffc03f
                )
            
            # 10. 添加背景音乐（如果有）
            background_music_path = inputs.get('background_music_path')
            if background_music_path and os.path.exists(background_music_path):
                volume = inputs.get('background_music_volume', 0.3)
                self.logger.info(f"🎼 添加背景音乐: {background_music_path}")
                self.add_background_music(background_music_path, volume=volume)
            
            # 11. 添加音频（用于同步）
            self.logger.info(f"🎵 添加音频: {audio_url}")
            remove_pauses = inputs.get('remove_pauses', False)
            if remove_pauses:
                # 如果要移除停顿，使用音频处理器的停顿移除功能
                processed_audio_path = self.audio_processor.remove_audio_pauses(audio_url)
                if processed_audio_path:
                    self.add_audio(processed_audio_path)
                else:
                    self.logger.warning("停顿移除失败，使用原始音频")
                    self.add_audio(audio_url)
            else:
                self.add_audio(audio_url)
            
            # 12. 字幕时间优化
            self.logger.info("⚡ 优化字幕时间")
            self.subtitle_processor.process_subtitle_timing_optimization()
            
            # 13. 保存草稿
            self.context.script.save()
            
            # 14. 记录执行时间
            execution_time = time.time() - start_time
            self.logger.info(f"✅ 完整优雅工作流完成！耗时: {execution_time:.2f}秒")
            
            # 15. 保存详细摘要
            self._save_complete_workflow_summary(inputs, self.context.script.save_path, execution_time)
            
            return self.context.script.save_path
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ 优雅工作流失败: {e}")
            self.logger.error(f"⏱️ 失败前耗时: {execution_time:.2f}秒")
            raise WorkflowError(f"完整优雅工作流处理失败: {e}") from e
    
    def _adjust_subtitle_timing(self, subtitles: List[Dict[str, Any]], delay_seconds: float = 0.0, 
                               speed_factor: float = 1.0) -> List[Dict[str, Any]]:
        """调整字幕时间 - 添加延迟和调整语速"""
        if not subtitles:
            return []
        
        self.logger.info(f"⏰ 调整字幕时间: 延迟={delay_seconds:.1f}s, 速度系数={speed_factor:.2f}")
        
        adjusted_subtitles = []
        
        for i, subtitle in enumerate(subtitles):
            # 应用速度系数
            original_start = subtitle.get('start', 0)
            original_end = subtitle.get('end', original_start + 1)
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
        
        self.logger.info(f"✅ 字幕时间调整完成")
        return adjusted_subtitles
    
    def process_simple_workflow(self, inputs: Dict[str, Any]) -> str:
        """处理简化工作流
        
        Args:
            inputs: 输入参数字典
            
        Returns:
            草稿保存路径
        """
        start_time = time.time()
        
        try:
            self.logger.info("🚀 开始处理简化工作流")
            self.logger.info(f"📋 输入参数: {self._format_inputs_for_log(inputs)}")
            
            # 1. 创建草稿
            self.create_draft()
            
            # 2. 添加音频（如果有）
            audio_url = inputs.get('audio_url')
            if audio_url:
                self.logger.info(f"🎵 添加音频: {audio_url}")
                self.add_audio(audio_url)
            
            # 3. 添加背景音乐（如果有）
            background_music_path = inputs.get('background_music_path')
            if background_music_path and os.path.exists(background_music_path):
                volume = inputs.get('background_music_volume', 0.3)
                self.logger.info(f"🎼 添加背景音乐: {background_music_path}")
                self.add_background_music(background_music_path, volume=volume)
            
            # 4. 保存草稿
            self.context.script.save()
            
            # 5. 记录执行时间
            execution_time = time.time() - start_time
            self.logger.info(f"✅ 简化工作流完成！耗时: {execution_time:.2f}秒")
            
            # 6. 保存摘要
            self._save_workflow_summary(inputs, self.context.script.save_path, execution_time)
            
            return self.context.script.save_path
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ 工作流失败: {e}")
            self.logger.error(f"⏱️ 失败前耗时: {execution_time:.2f}秒")
            raise WorkflowError(f"工作流处理失败: {e}") from e
    
    def _format_inputs_for_log(self, inputs: Dict[str, Any]) -> str:
        """格式化输入参数用于日志记录，隐藏敏感信息"""
        safe_inputs = {}
        sensitive_keys = ['volcengine_access_token', 'doubao_token', 'access_token', 'token']
        
        for k, v in inputs.items():
            if any(sensitive in k.lower() for sensitive in sensitive_keys):
                safe_inputs[k] = '***'
            else:
                safe_inputs[k] = v
                
        return ', '.join([f'{k}: {v}' for k, v in safe_inputs.items()])
    
    def _save_workflow_summary(self, inputs: Dict[str, Any], result_path: str, execution_time: float):
        """保存工作流执行摘要"""
        try:
            from datetime import datetime
            
            summary = {
                "project_info": {
                    "project_name": self.config.project_name,
                    "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_seconds": round(execution_time, 2),
                    "result_path": result_path
                },
                "input_parameters": self._format_inputs_for_summary(inputs),
                "processing_results": {
                    "audio_duration": round(self.context.audio_duration, 2),
                    "video_duration": round(self.context.video_duration, 2),
                    "project_duration": round(self.context.project_duration, 2),
                },
                "technical_details": {
                    "architecture": "Modular Elegant Design",
                    "version": "2.0",
                    "non_destructive_editing": True
                }
            }
            
            self.logger.save_summary(summary)
            
        except Exception as e:
            self.logger.error(f"保存工作流摘要时出错: {e}")
    
    def _save_complete_workflow_summary(self, inputs: Dict[str, Any], result_path: str, execution_time: float):
        """保存完整工作流执行摘要"""
        try:
            from datetime import datetime
            
            # 获取统计信息
            subtitle_stats = self.subtitle_processor.get_subtitle_statistics()
            pause_stats = self.pause_processor.get_pause_statistics()
            
            summary = {
                "project_info": {
                    "project_name": self.config.project_name,
                    "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_seconds": round(execution_time, 2),
                    "result_path": result_path,
                    "workflow_type": "Complete Elegant Workflow"
                },
                "input_parameters": self._format_inputs_for_summary(inputs),
                "processing_results": {
                    "audio_duration": round(self.context.audio_duration, 2),
                    "video_duration": round(self.context.video_duration, 2),
                    "project_duration": round(self.context.project_duration, 2),
                    "subtitle_statistics": subtitle_stats,
                    "pause_statistics": pause_stats
                },
                "technical_details": {
                    "architecture": "Modular Elegant Design v2.0",
                    "version": "2.0",
                    "non_destructive_editing": True,
                    "modules_used": [
                        "DurationManager",
                        "TrackManager", 
                        "MaterialManager",
                        "AudioProcessor",
                        "VideoProcessor",
                        "SubtitleProcessor",
                        "PauseProcessor"
                    ]
                },
                "quality_metrics": {
                    "duration_precision": "2 decimal places",
                    "timing_validation": "Enabled",
                    "bounds_checking": "Enabled",
                    "modular_design": "Fully Implemented"
                }
            }
            
            self.logger.save_summary(summary)
            
        except Exception as e:
            self.logger.error(f"保存完整工作流摘要时出错: {e}")
    
    def _save_workflow_summary(self, inputs: Dict[str, Any], result_path: str, execution_time: float):
        """保存工作流执行摘要"""
        try:
            from datetime import datetime
            
            summary = {
                "project_info": {
                    "project_name": self.config.project_name,
                    "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_seconds": round(execution_time, 2),
                    "result_path": result_path
                },
                "input_parameters": self._format_inputs_for_summary(inputs),
                "processing_results": {
                    "audio_duration": round(self.context.audio_duration, 2),
                    "video_duration": round(self.context.video_duration, 2),
                    "project_duration": round(self.context.project_duration, 2),
                },
                "technical_details": {
                    "architecture": "Modular Elegant Design",
                    "version": "2.0",
                    "non_destructive_editing": True
                }
            }
            
            self.logger.save_summary(summary)
            
        except Exception as e:
            self.logger.error(f"保存工作流摘要时出错: {e}")
    
    def _format_inputs_for_summary(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """格式化输入参数用于摘要"""
        return {
            "audio_url": inputs.get('audio_url', 'N/A'),
            "video_url": inputs.get('video_url', 'N/A'),
            "digital_human_url": inputs.get('digital_human_url', 'N/A'),
            "background_music_path": inputs.get('background_music_path', 'N/A'),
            "background_music_volume": inputs.get('background_music_volume', 0.3),
            "title": inputs.get('title', 'N/A'),
            "title_duration": inputs.get('title_duration', 3.0),
            "apply_pauses": inputs.get('apply_pauses', False),
            "pause_intensity": inputs.get('pause_intensity', 0.5),
            "asr_segments": len(inputs.get('asr_result', [])),
        }


# 向后兼容的工厂函数
def create_elegant_workflow(draft_folder_path: str, project_name: str = "elegant_project") -> ElegantVideoWorkflow:
    """创建优雅工作流实例
    
    Args:
        draft_folder_path: 剪映草稿文件夹路径
        project_name: 项目名称
        
    Returns:
        ElegantVideoWorkflow实例
    """
    config = WorkflowConfig(
        project_name=project_name,
        draft_folder_path=draft_folder_path
    )
    
    return ElegantVideoWorkflow(config)


def main():
    """演示优雅工作流的使用"""
    # 配置剪映草稿文件夹路径（需要根据实际情况修改）
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 配置背景音乐路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..')
    background_music_path = os.path.join(project_root, '华尔兹.mp3')
    
    print("🎼 优雅视频工作流演示 v2.0")
    print("=" * 50)
    
    try:
        # 创建工作流
        workflow = create_elegant_workflow(draft_folder_path, "elegant_demo_v2")
        
        # 演示完整工作流
        print("\n🚀 演示完整工作流...")
        
        # 模拟ASR结果
        mock_asr_result = [
            {"text": "大家好，欢迎来到优雅工作流演示", "start_time": 0.0, "end_time": 3.0},
            {"text": "这是一个全新的模块化架构", "start_time": 3.5, "end_time": 6.0},
            {"text": "支持音频、视频、字幕和停顿处理", "start_time": 6.5, "end_time": 10.0},
            {"text": "让视频编辑变得更加优雅", "start_time": 10.5, "end_time": 13.0}
        ]
        
        # 配置完整工作流参数 - 使用真实ASR参数
        complete_inputs = {
            "audio_url": "https://oss.oemi.jdword.com/prod/temp/srt/V20250904223919001.wav",
            "digital_human_url": "https://oss.oemi.jdword.com/prod/order/video/202509/V20250904224537001.mp4",
            "background_music_path": background_music_path,
            "background_music_volume": 0.25,
            "title": "买房子该怎么买，一定要牢记",
            "volcengine_appid": "6046310832",
            "volcengine_access_token": "M1I3MjFhNzQ5YjQ5NDQ2YmFjNjFhMjcwM2Y0ZTczOTEa",
            "doubao_token": "pt-a8ab5e4e-5e81-46c2-b30a-bf66a77ba0d2",
            "doubao_model": "doubao-1-5-pro-32k-250115",
            "subtitle_delay": 0.0,
            "subtitle_speed": 1.0,
            "remove_pauses": False  # 设置为True可测试停顿移除
        }
        
        # 处理完整工作流
        save_path = workflow.process_complete_workflow(complete_inputs)
        
        print(f"\n✅ 完整工作流完成!")
        print(f"📁 剪映项目已保存到: {save_path}")
        
        # 演示简化工作流
        print("\n🎵 演示简化工作流...")
        
        # 配置简化工作流参数
        simple_inputs = {
            "audio_url": "https://example.com/simple_audio.mp3",
            "background_music_path": background_music_path,
            "background_music_volume": 0.3,
            "title": "简化工作流演示"
        }
        
        # 创建新的工作流实例用于简化演示
        simple_workflow = create_elegant_workflow(draft_folder_path, "simple_demo_v2")
        simple_save_path = simple_workflow.process_simple_workflow(simple_inputs)
        
        print(f"\n✅ 简化工作流完成!")
        print(f"📁 剪映项目已保存到: {simple_save_path}")
        
        print(f"\n🎬 请打开剪映查看生成的项目")
        print("\n📊 新架构特性:")
        print("  • 模块化设计，职责分离")
        print("  • 2位小数精度，时长验证")
        print("  • 非破坏性编辑")
        print("  • 完整的错误处理")
        print("  • 详细的执行日志")
        print("  • 统计信息跟踪")
        
    except Exception as e:
        print(f"❌ 工作流失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()