"""
时长管理器

负责所有时长相关的计算、验证和格式化
"""

from typing import Optional
from ..core.base import BaseProcessor, WorkflowContext
from ..core.exceptions import DurationError

class DurationManager(BaseProcessor):
    """时长管理器"""
    
    def process(self, *args, **kwargs):
        """占位方法"""
        pass
        
    def validate_duration_bounds(self, duration: float, context: str = "") -> float:
        """验证时长边界，确保不超过视频总时长
        
        Args:
            duration: 需要验证的时长（秒）
            context: 上下文信息，用于调试
            
        Returns:
            验证后的时长（秒），保留两位小数
        """
        # 获取最大允许时长（优先使用有效视频时长）
        max_allowed_duration = self.context.get_effective_video_duration()
        
        # 如果没有有效视频时长，使用项目时长
        if max_allowed_duration <= 0:
            max_allowed_duration = self.context.project_duration
            
        # 如果仍然没有，直接返回原时长
        if max_allowed_duration <= 0:
            self._log("warning", f"{context}无法验证时长边界，因为没有视频时长参考")
            return round(duration, 2)
            
        # 验证时长不超过最大允许时长
        if duration > max_allowed_duration:
            self._log("warning", f"{context}时长 {duration:.2f}s 超过最大允许时长 {max_allowed_duration:.2f}s，将被截取")
            return round(max_allowed_duration, 2)
        else:
            self._log("debug", f"{context}时长 {duration:.2f}s 在允许范围内 (最大: {max_allowed_duration:.2f}s)")
            return round(duration, 2)
            
    def update_project_duration(self):
        """更新项目总时长，取音视频中的最长者"""
        self.context.project_duration = round(max(self.context.audio_duration, self.context.video_duration), 6)
        if self.context.project_duration > 0:
            self._log("info", f"项目总时长更新为: {self.context.project_duration:.6f} 秒 (音频: {self.context.audio_duration:.6f}s, 视频: {self.context.video_duration:.6f}s)")
            
    def format_duration_for_display(self, duration: float) -> str:
        """格式化时长用于显示（2位小数）"""
        return f"{duration:.2f}s"
        
    def format_duration_for_calculation(self, duration: float) -> str:
        """格式化时长用于计算（6位小数）"""
        return f"{duration:.6f}s"
        
    def calculate_effective_duration(self, audio_duration: float, video_duration: float, 
                                   adjusted_subtitles: Optional[list] = None) -> float:
        """计算有效时长"""
        if adjusted_subtitles and video_duration > 0:
            return video_duration
        elif video_duration > 0:
            return video_duration
        elif audio_duration > 0:
            return audio_duration
        else:
            return 0.0