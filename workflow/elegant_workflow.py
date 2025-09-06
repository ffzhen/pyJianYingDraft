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
from pyJianYingDraft import TrackType

# 导入新的模块化组件
from .core import WorkflowContext, WorkflowLogger, WorkflowConfig
from .core.exceptions import WorkflowError, ValidationError, ProcessingError
from .managers import DurationManager, TrackManager, MaterialManager
from .processors import AudioProcessor, VideoProcessor, SubtitleProcessor


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
        
    def create_draft(self) -> draft.Script:
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
    
    def process_complete_workflow(self, inputs: Dict[str, Any]) -> str:
        """处理完整工作流
        
        Args:
            inputs: 输入参数字典，支持的参数：
                - audio_url: 音频URL
                - video_url: 主视频URL
                - digital_human_url: 数字人视频URL
                - background_music_path: 背景音乐路径
                - background_music_volume: 背景音乐音量(0-1)
                - title: 标题文本
                - title_duration: 标题显示时长(秒)
                - asr_result: ASR识别结果用于生成字幕
                - apply_pauses: 是否应用自然停顿
                - pause_intensity: 停顿强度(0-1)
            
        Returns:
            草稿保存路径
        """
        start_time = time.time()
        
        try:
            self.logger.info("🚀 开始处理完整工作流")
            self.logger.info(f"📋 输入参数: {self._format_inputs_for_log(inputs)}")
            
            # 1. 创建草稿
            self.create_draft()
            
            # 2. 添加主视频（如果有）
            video_url = inputs.get('video_url')
            if video_url:
                self.logger.info(f"🎬 添加主视频: {video_url}")
                self.add_video(video_url)
            
            # 3. 添加音频（如果有）
            audio_url = inputs.get('audio_url')
            if audio_url:
                self.logger.info(f"🎵 添加音频: {audio_url}")
                self.add_audio(audio_url)
            
            # 4. 添加数字人视频（如果有）
            digital_human_url = inputs.get('digital_human_url')
            if digital_human_url:
                self.logger.info(f"🤖 添加数字人视频: {digital_human_url}")
                self.add_digital_human_video(digital_human_url)
            
            # 5. 添加字幕（如果有ASR结果）
            asr_result = inputs.get('asr_result')
            if asr_result:
                self.logger.info(f"📝 添加字幕: {len(asr_result)} 个段落")
                self.add_subtitle_from_asr(asr_result)
            
            # 6. 添加标题字幕（如果有）
            title = inputs.get('title')
            if title:
                title_duration = inputs.get('title_duration', 3.0)
                self.logger.info(f"🏷️ 添加标题字幕: {title}")
                self.add_title_subtitle(title, duration=title_duration)
            
            # 7. 应用自然停顿（如果启用且有ASR结果）
            if inputs.get('apply_pauses', False) and asr_result:
                pause_intensity = inputs.get('pause_intensity', 0.5)
                self.logger.info(f"⏸️ 应用自然停顿，强度: {pause_intensity}")
                self.apply_natural_pauses(asr_result, pause_intensity=pause_intensity)
            
            # 8. 添加背景音乐（如果有）
            background_music_path = inputs.get('background_music_path')
            if background_music_path and os.path.exists(background_music_path):
                volume = inputs.get('background_music_volume', 0.3)
                self.logger.info(f"🎼 添加背景音乐: {background_music_path}")
                self.add_background_music(background_music_path, volume=volume)
            
            # 9. 字幕时间优化（如果有字幕）
            if asr_result:
                self.logger.info("⚡ 优化字幕时间")
                self.subtitle_processor.process_subtitle_timing_optimization()
            
            # 10. 保存草稿
            self.context.script.save()
            
            # 11. 记录执行时间
            execution_time = time.time() - start_time
            self.logger.info(f"✅ 完整工作流完成！耗时: {execution_time:.2f}秒")
            
            # 12. 保存详细摘要
            self._save_complete_workflow_summary(inputs, self.context.script.save_path, execution_time)
            
            return self.context.script.save_path
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ 工作流失败: {e}")
            self.logger.error(f"⏱️ 失败前耗时: {execution_time:.2f}秒")
            raise WorkflowError(f"完整工作流处理失败: {e}") from e
    
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
        
        # 配置完整工作流参数
        complete_inputs = {
            "audio_url": "https://example.com/audio.mp3",
            "video_url": "https://example.com/video.mp4", 
            "digital_human_url": "https://example.com/digital_human.mp4",
            "background_music_path": background_music_path,
            "background_music_volume": 0.25,
            "title": "优雅工作流v2.0演示",
            "title_duration": 3.0,
            "asr_result": mock_asr_result,
            "apply_pauses": True,
            "pause_intensity": 0.6
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