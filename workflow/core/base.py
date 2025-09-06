"""
基础类和接口

定义所有处理器的基类和工作流上下文
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import pyJianYingDraft as draft

@dataclass
class WorkflowContext:
    """工作流上下文，存储共享状态"""
    script: Optional[draft.ScriptFile] = None
    audio_duration: float = 0.0
    video_duration: float = 0.0 
    project_duration: float = 0.0
    
    # 字幕相关
    original_subtitles: Optional[list] = None
    adjusted_subtitles: Optional[list] = None
    
    # ASR相关
    volcengine_asr: Optional[Any] = None
    
    # 路径相关
    digital_video_path: Optional[str] = None
    material_video_path: Optional[str] = None
    
    def get_effective_video_duration(self) -> float:
        """获取有效视频时长"""
        if hasattr(self, 'adjusted_subtitles') and self.adjusted_subtitles and self.video_duration > 0:
            return self.video_duration
        elif self.video_duration > 0:
            return self.video_duration
        elif self.audio_duration > 0:
            return self.audio_duration
        else:
            return self.project_duration

class BaseProcessor(ABC):
    """所有处理器的基类"""
    
    def __init__(self, context: WorkflowContext, logger: Any = None):
        self.context = context
        self.logger = logger
        
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """处理方法，子类必须实现"""
        pass
        
    def _log(self, level: str, message: str):
        """统一的日志记录方法"""
        if self.logger:
            getattr(self.logger, level.lower())(message)
        else:
            print(f"[{level.upper()}] {message}")
            
    def _format_duration(self, duration: float, precision: int = 2) -> str:
        """格式化时长显示"""
        return f"{duration:.{precision}f}s"