"""
视频模板样式配置系统

定义各种视频模板的样式配置，包括字幕、标题、背景等样式
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional
import json


@dataclass
class TextStyleConfig:
    """文本样式配置"""
    font_type: str = "俪金黑"
    size: float = 15.0
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)  # RGB 0-1
    bold: bool = True
    align: int = 0  # 0=左对齐, 1=居中, 2=右对齐
    auto_wrapping: bool = True
    max_line_width: float = 0.7
    line_spacing: int = 0
    scale_x: float = 1.0
    scale_y: float = 1.0


@dataclass
class HighlightStyleConfig:
    """高亮样式配置"""
    color: Tuple[float, float, float] = (1.0, 0.7529411765, 0.2470588235)  # 黄色
    size: float = 10.0
    bold: bool = True


@dataclass
class TextShadowConfig:
    """文本阴影配置"""
    alpha: float = 0.8
    color: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # 黑色
    diffuse: float = 20.0
    distance: float = 10.0
    angle: float = -45.0


@dataclass
class TextBackgroundConfig:
    """文本背景配置"""
    color: str = "#000000"  # 黑色
    alpha: float = 0.67  # 67% 不透明度
    height: float = 0.31  # 31% 高度
    width: float = 0.14  # 14% 宽度
    horizontal_offset: float = 0.5  # 50% 左右间隙
    vertical_offset: float = 0.5  # 50% 上下间隙
    round_radius: float = 0.0  # 圆角半径
    style: int = 1  # 背景样式


@dataclass
class CaptionStyleConfig:
    """字幕样式配置"""
    # 基础样式
    base_style: TextStyleConfig = field(default_factory=TextStyleConfig)
    # 高亮样式
    highlight_style: HighlightStyleConfig = field(default_factory=HighlightStyleConfig)
    # 阴影样式
    shadow_style: TextShadowConfig = field(default_factory=TextShadowConfig)
    # 背景样式
    background_style: Optional[TextBackgroundConfig] = None
    # 位置配置
    position: str = "bottom"  # top, center, bottom
    transform_y: float = -0.3  # 垂直位置 -1.0 ~ 1.0


@dataclass
class TitleStyleConfig:
    """标题样式配置"""
    # 基础样式
    base_style: TextStyleConfig = field(default_factory=lambda: TextStyleConfig(
        font_type="俪金黑",
        size=15.0,
        color=(1.0, 1.0, 1.0),
        bold=True,
        align=0,
        auto_wrapping=True,
        max_line_width=0.7,
        line_spacing=4
    ))
    # 高亮样式（第二行高亮）
    highlight_style: HighlightStyleConfig = field(default_factory=HighlightStyleConfig)
    # 阴影样式
    shadow_style: TextShadowConfig = field(default_factory=TextShadowConfig)
    # 背景样式
    background_style: Optional[TextBackgroundConfig] = None
    # 位置配置
    transform_y: float = 0.72  # 垂直位置
    # 三行标题配置
    line_count: int = 3  # 分成几行显示


@dataclass
class VideoStyleConfig:
    """视频整体样式配置"""
    # 视频尺寸
    width: int = 1080
    height: int = 1920
    fps: int = 30
    
    # 字幕样式
    caption_style: CaptionStyleConfig = field(default_factory=CaptionStyleConfig)
    
    # 标题样式
    title_style: TitleStyleConfig = field(default_factory=TitleStyleConfig)
    
    # 背景音乐配置
    background_music_volume: float = 0.3
    
    # 音频配置
    audio_volume: float = 0.8
    
    # 转场效果
    enable_transitions: bool = True
    
    # 模板描述
    description: str = ""
    
    # 模板标签
    tags: List[str] = field(default_factory=list)


class StyleConfigManager:
    """样式配置管理器"""
    
    def __init__(self):
        self.configs: Dict[str, VideoStyleConfig] = {}
        self._load_default_configs()
    
    def _load_default_configs(self):
        """加载默认配置"""
        # 科技风格模板
        self.configs["tech"] = VideoStyleConfig(
            description="科技风格模板",
            tags=["科技", "现代", "简洁"],
            caption_style=CaptionStyleConfig(
                base_style=TextStyleConfig(
                    font_type="俪金黑",
                    size=8.0,
                    color=(0.0, 1.0, 1.0),  # 青色
                    bold=True,
                    align=0,
                    auto_wrapping=True,
                    max_line_width=0.82,
                    line_spacing=0,
                    scale_x=1.39,
                    scale_y=1.39
                ),
                highlight_style=HighlightStyleConfig(
                    color=(0.0, 1.0, 0.5),  # 绿色
                    size=10.0,
                    bold=True
                ),
                background_style=TextBackgroundConfig(
                    color="#000000",
                    alpha=0.8,
                    height=0.25,
                    width=0.14,
                    horizontal_offset=0.5,
                    vertical_offset=0.5,
                    round_radius=0.0,
                    style=1
                ),
                position="bottom",
                transform_y=-0.3
            ),
            title_style=TitleStyleConfig(
                base_style=TextStyleConfig(
                    font_type="俪金黑",
                    size=15.0,
                    color=(0.0, 1.0, 1.0),  # 青色
                    bold=True,
                    align=0,
                    auto_wrapping=True,
                    max_line_width=0.7,
                    line_spacing=4
                ),
                highlight_style=HighlightStyleConfig(
                    color=(0.0, 1.0, 0.5),  # 绿色
                    size=15.0,
                    bold=True
                ),
                background_style=TextBackgroundConfig(
                    color="#000080",  # 深蓝色
                    alpha=0.7,
                    height=0.48,
                    width=1.0,
                    horizontal_offset=0.5,
                    vertical_offset=0.5,
                    round_radius=0.0,
                    style=1
                ),
                transform_y=0.72,
                line_count=3
            )
        )
        
        # 温馨风格模板
        self.configs["warm"] = VideoStyleConfig(
            description="温馨风格模板",
            tags=["温馨", "柔和", "暖色调"],
            caption_style=CaptionStyleConfig(
                base_style=TextStyleConfig(
                    font_type="文轩体",
                    size=9.0,
                    color=(1.0, 0.8, 0.6),  # 暖白色
                    bold=False,
                    align=0,
                    auto_wrapping=True,
                    max_line_width=0.82,
                    line_spacing=2,
                    scale_x=1.2,
                    scale_y=1.2
                ),
                highlight_style=HighlightStyleConfig(
                    color=(1.0, 0.4, 0.4),  # 粉红色
                    size=11.0,
                    bold=True
                ),
                background_style=TextBackgroundConfig(
                    color="#8B4513",  # 棕色
                    alpha=0.6,
                    height=0.25,
                    width=0.14,
                    horizontal_offset=0.5,
                    vertical_offset=0.5,
                    round_radius=10.0,
                    style=1
                ),
                position="bottom",
                transform_y=-0.25
            ),
            title_style=TitleStyleConfig(
                base_style=TextStyleConfig(
                    font_type="文轩体",
                    size=16.0,
                    color=(1.0, 0.9, 0.7),  # 暖黄色
                    bold=False,
                    align=1,  # 居中
                    auto_wrapping=True,
                    max_line_width=0.8,
                    line_spacing=6
                ),
                highlight_style=HighlightStyleConfig(
                    color=(1.0, 0.3, 0.3),  # 红色
                    size=18.0,
                    bold=True
                ),
                background_style=TextBackgroundConfig(
                    color="#FFE4B5",  # 暖色背景
                    alpha=0.5,
                    height=0.48,
                    width=1.0,
                    horizontal_offset=0.5,
                    vertical_offset=0.5,
                    round_radius=15.0,
                    style=1
                ),
                transform_y=0.75,
                line_count=3
            )
        )
        
        # 商务风格模板
        self.configs["business"] = VideoStyleConfig(
            description="商务风格模板",
            tags=["商务", "正式", "专业"],
            caption_style=CaptionStyleConfig(
                base_style=TextStyleConfig(
                    font_type="宋体",
                    size=10.0,
                    color=(0.0, 0.0, 0.0),  # 黑色
                    bold=True,
                    align=0,
                    auto_wrapping=True,
                    max_line_width=0.82,
                    line_spacing=1,
                    scale_x=1.0,
                    scale_y=1.0
                ),
                highlight_style=HighlightStyleConfig(
                    color=(0.0, 0.0, 1.0),  # 蓝色
                    size=12.0,
                    bold=True
                ),
                background_style=TextBackgroundConfig(
                    color="#F0F0F0",  # 浅灰色
                    alpha=0.9,
                    height=0.25,
                    width=0.14,
                    horizontal_offset=0.5,
                    vertical_offset=0.5,
                    round_radius=0.0,
                    style=1
                ),
                position="bottom",
                transform_y=-0.35
            ),
            title_style=TitleStyleConfig(
                base_style=TextStyleConfig(
                    font_type="黑体",
                    size=18.0,
                    color=(0.0, 0.0, 0.0),  # 黑色
                    bold=True,
                    align=1,  # 居中
                    auto_wrapping=True,
                    max_line_width=0.8,
                    line_spacing=3
                ),
                highlight_style=HighlightStyleConfig(
                    color=(0.0, 0.0, 1.0),  # 蓝色
                    size=20.0,
                    bold=True
                ),
                background_style=TextBackgroundConfig(
                    color="#FFFFFF",  # 白色
                    alpha=0.95,
                    height=0.48,
                    width=1.0,
                    horizontal_offset=0.5,
                    vertical_offset=0.5,
                    round_radius=0.0,
                    style=1
                ),
                transform_y=0.7,
                line_count=3
            )
        )
        
        # 原有风格模板（保持现有样式）
        self.configs["original"] = VideoStyleConfig(
            description="原有风格模板",
            tags=["原有", "经典"],
            caption_style=CaptionStyleConfig(
                base_style=TextStyleConfig(
                    font_type="俪金黑",
                    size=8.0,
                    color=(1.0, 1.0, 1.0),  # 白色
                    bold=True,
                    align=0,
                    auto_wrapping=True,
                    max_line_width=0.82,
                    line_spacing=0,
                    scale_x=1.39,
                    scale_y=1.39
                ),
                highlight_style=HighlightStyleConfig(
                    color=(1.0, 0.7529411765, 0.2470588235),  # 黄色
                    size=10.0,
                    bold=True
                ),
                background_style=TextBackgroundConfig(
                    color="#000000",
                    alpha=0.67,
                    height=0.25,
                    width=0.14,
                    horizontal_offset=0.5,
                    vertical_offset=0.5,
                    round_radius=0.0,
                    style=1
                ),
                position="bottom",
                transform_y=-0.3
            ),
            title_style=TitleStyleConfig(
                base_style=TextStyleConfig(
                    font_type="俪金黑",
                    size=15.0,
                    color=(1.0, 1.0, 1.0),  # 白色
                    bold=True,
                    align=0,
                    auto_wrapping=True,
                    max_line_width=0.7,
                    line_spacing=4
                ),
                highlight_style=HighlightStyleConfig(
                    color=(1.0, 0.7529411765, 0.2470588235),  # 黄色
                    size=15.0,
                    bold=True
                ),
                background_style=TextBackgroundConfig(
                    color="#000000",
                    alpha=0.67,
                    height=0.48,
                    width=1.0,
                    horizontal_offset=0.5,
                    vertical_offset=0.5,
                    round_radius=0.0,
                    style=1
                ),
                transform_y=0.72,
                line_count=3
            )
        )
    
    def get_config(self, template_name: str) -> Optional[VideoStyleConfig]:
        """获取指定模板的配置"""
        return self.configs.get(template_name)
    
    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return list(self.configs.keys())
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """获取模板信息"""
        config = self.configs.get(template_name)
        if not config:
            return {}
        
        return {
            "name": template_name,
            "description": config.description,
            "tags": config.tags,
            "caption_font": config.caption_style.base_style.font_type,
            "caption_color": config.caption_style.base_style.color,
            "title_font": config.title_style.base_style.font_type,
            "title_color": config.title_style.base_style.color,
            "has_background": config.caption_style.background_style is not None
        }
    
    def add_custom_config(self, template_name: str, config: VideoStyleConfig):
        """添加自定义配置"""
        self.configs[template_name] = config
    
    def save_config(self, template_name: str, file_path: str):
        """保存配置到文件"""
        config = self.configs.get(template_name)
        if not config:
            raise ValueError(f"Template '{template_name}' not found")
        
        # 转换为可序列化的字典
        config_dict = self._config_to_dict(config)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
    
    def load_config(self, template_name: str, file_path: str):
        """从文件加载配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        config = self._dict_to_config(config_dict)
        self.configs[template_name] = config
    
    def _config_to_dict(self, config: VideoStyleConfig) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        def serialize_color(color):
            return list(color)
        
        def serialize_style(style):
            if hasattr(style, '__dict__'):
                result = {}
                for key, value in style.__dict__.items():
                    if isinstance(value, tuple):
                        result[key] = serialize_color(value)
                    elif hasattr(value, '__dict__'):
                        result[key] = serialize_style(value)
                    else:
                        result[key] = value
                return result
            return {}
        
        return serialize_style(config)
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> VideoStyleConfig:
        """将字典转换为配置对象"""
        def deserialize_color(color_list):
            return tuple(color_list)
        
        # 递归转换字典为对象
        def dict_to_obj(obj_class, data):
            if isinstance(data, dict):
                return obj_class(**{
                    k: dict_to_obj(getattr(obj_class, k).field_type if hasattr(getattr(obj_class, k), 'field_type') else type(None), v)
                    for k, v in data.items()
                })
            return data
        
        # 简化版本，直接创建对象
        return VideoStyleConfig(
            width=config_dict.get('width', 1080),
            height=config_dict.get('height', 1920),
            fps=config_dict.get('fps', 30),
            description=config_dict.get('description', ''),
            tags=config_dict.get('tags', [])
        )


# 全局样式配置管理器实例
style_config_manager = StyleConfigManager()