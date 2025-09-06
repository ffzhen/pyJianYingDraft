"""
配置管理

管理工作流的配置参数
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class WorkflowConfig:
    """工作流配置"""
    
    # 项目设置
    project_name: str = "video_workflow"
    draft_folder_path: str = ""
    
    # 视频设置
    video_width: int = 1080
    video_height: int = 1920
    video_fps: int = 30
    
    # 音频设置
    default_volume: float = 1.0
    background_music_volume: float = 0.3
    
    # 字幕设置
    subtitle_delay: float = 0.0
    subtitle_speed: float = 1.0
    font_size: float = 8.0
    highlight_size: float = 10.0
    
    # 停顿处理设置
    min_pause_duration: float = 0.2
    max_word_gap: float = 0.8
    
    # ASR设置
    volcengine_appid: Optional[str] = None
    volcengine_access_token: Optional[str] = None
    doubao_token: Optional[str] = None
    doubao_model: str = "doubao-1-5-pro-32k-250115"
    
    # 时长设置
    duration_precision: int = 2  # 时长显示精度
    internal_precision: int = 6  # 内部计算精度
    
    # 颜色设置
    base_color: tuple = (1.0, 1.0, 1.0)  # 白色
    highlight_color: tuple = (1.0, 0.7529411765, 0.2470588235)  # #ffc03f
    
    # 其他设置
    temp_dir: str = "temp_materials"
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'WorkflowConfig':
        """从字典创建配置"""
        return cls(**config_dict)
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        import dataclasses
        return dataclasses.asdict(self)
        
    def validate(self) -> bool:
        """验证配置的有效性"""
        if not self.draft_folder_path:
            raise ValueError("draft_folder_path 不能为空")
            
        if self.video_width <= 0 or self.video_height <= 0:
            raise ValueError("视频尺寸必须大于0")
            
        if not (0 <= self.default_volume <= 1):
            raise ValueError("音量必须在0-1之间")
            
        return True