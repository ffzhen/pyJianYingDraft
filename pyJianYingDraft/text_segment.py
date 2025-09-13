"""定义文本片段及其相关类"""

import json
import uuid
from copy import deepcopy

from typing import Dict, Tuple, Any, List
from typing import Union, Optional, Literal

from .time_util import Timerange, tim
from .segment import ClipSettings, VisualSegment
from .animation import SegmentAnimations, Text_animation

from .metadata import FontType, EffectMeta
from .metadata import TextIntro, TextOutro, TextLoopAnim

class TextStyle:
    """字体样式类"""

    size: float
    """字体大小"""

    bold: bool
    """是否加粗"""
    italic: bool
    """是否斜体"""
    underline: bool
    """是否加下划线"""

    color: Tuple[float, float, float]
    """字体颜色, RGB三元组, 取值范围为[0, 1]"""
    alpha: float
    """字体不透明度"""

    align: Literal[0, 1, 2]
    """对齐方式"""
    vertical: bool
    """是否为竖排文本"""

    letter_spacing: int
    """字符间距"""
    line_spacing: int
    """行间距"""

    auto_wrapping: bool
    """是否自动换行"""
    max_line_width: float
    """最大行宽, 取值范围为[0, 1]"""

    def __init__(self, *, size: float = 8.0, bold: bool = False, italic: bool = False, underline: bool = False,
                 color: Tuple[float, float, float] = (1.0, 1.0, 1.0), alpha: float = 1.0,
                 align: Literal[0, 1, 2] = 0, vertical: bool = False,
                 letter_spacing: int = 0, line_spacing: int = 0,
                 auto_wrapping: bool = False, max_line_width: float = 0.82):
        """
        Args:
            size (`float`, optional): 字体大小, 默认为8.0
            bold (`bool`, optional): 是否加粗, 默认为否
            italic (`bool`, optional): 是否斜体, 默认为否
            underline (`bool`, optional): 是否加下划线, 默认为否
            color (`Tuple[float, float, float]`, optional): 字体颜色, RGB三元组, 取值范围为[0, 1], 默认为白色
            alpha (`float`, optional): 字体不透明度, 取值范围[0, 1], 默认不透明
            align (`int`, optional): 对齐方式, 0: 左对齐, 1: 居中, 2: 右对齐, 默认为左对齐
            vertical (`bool`, optional): 是否为竖排文本, 默认为否
            letter_spacing (`int`, optional): 字符间距, 定义与剪映中一致, 默认为0
            line_spacing (`int`, optional): 行间距, 定义与剪映中一致, 默认为0
            auto_wrapping (`bool`, optional): 是否自动换行, 默认关闭
            max_line_width (`float`, optional): 每行最大行宽占屏幕宽度比例, 取值范围为[0, 1], 默认为0.82
        """
        self.size = size
        self.bold = bold
        self.italic = italic
        self.underline = underline

        self.color = color
        self.alpha = alpha

        self.align = align
        self.vertical = vertical

        self.letter_spacing = letter_spacing
        self.line_spacing = line_spacing

        self.auto_wrapping = auto_wrapping
        self.max_line_width = max_line_width

class TextBorder:
    """文本描边的参数"""

    alpha: float
    """描边不透明度"""
    color: Tuple[float, float, float]
    """描边颜色, RGB三元组, 取值范围为[0, 1]"""
    width: float
    """描边宽度"""

    def __init__(self, *, alpha: float = 1.0, color: Tuple[float, float, float] = (0.0, 0.0, 0.0), width: float = 40.0):
        """
        Args:
            alpha (`float`, optional): 描边不透明度, 取值范围[0, 1], 默认为1.0
            color (`Tuple[float, float, float]`, optional): 描边颜色, RGB三元组, 取值范围为[0, 1], 默认为黑色
            width (`float`, optional): 描边宽度, 与剪映中一致, 取值范围为[0, 100], 默认为40.0
        """
        self.alpha = alpha
        self.color = color
        self.width = width / 100.0 * 0.2  # 此映射可能不完全正确

    def export_json(self) -> Dict[str, Any]:
        """导出JSON数据, 放置在素材content的styles中"""
        return {
            "content": {
                "solid": {
                    "alpha": self.alpha,
                    "color": list(self.color),
                }
            },
            "width": self.width
        }

class TextBackground:
    """文本背景参数"""

    style: Literal[1, 2]
    """背景样式"""

    alpha: float
    """背景不透明度"""
    color: str
    """背景颜色, 格式为'#RRGGBB'"""
    round_radius: float
    """背景圆角半径"""
    height: float
    """背景高度"""
    width: float
    """背景宽度"""
    horizontal_offset: float
    """背景水平偏移"""
    vertical_offset: float
    """背景竖直偏移"""

    def __init__(self, *, color: str, style: Literal[1, 2] = 1, alpha: float = 1.0, round_radius: float = 0.0,
                 height: float = 0.14, width: float = 0.14,
                 horizontal_offset: float = 0.5, vertical_offset: float = 0.5):
        """
        Args:
            color (`str`): 背景颜色, 格式为'#RRGGBB'
            style (`int`, optional): 背景样式, 1和2分别对应剪映中的两种样式, 默认为1
            alpha (`float`, optional): 背景不透明度, 与剪映中一致, 取值范围[0, 1], 默认为1.0
            round_radius (`float`, optional): 背景圆角半径, 与剪映中一致, 取值范围[0, 1], 默认为0.0
            height (`float`, optional): 背景高度, 与剪映中一致, 取值范围为[0, 1], 默认为0.14
            width (`float`, optional): 背景宽度, 与剪映中一致, 取值范围为[0, 1], 默认为0.14
            horizontal_offset (`float`, optional): 背景水平偏移, 与剪映中一致, 取值范围为[0, 1], 默认为0.5
            vertical_offset (`float`, optional): 背景竖直偏移, 与剪映中一致, 取值范围为[0, 1], 默认为0.5
        """
        self.style = style

        self.alpha = alpha
        self.color = color
        self.round_radius = round_radius
        self.height = height
        self.width = width
        self.horizontal_offset = horizontal_offset * 2 - 1
        self.vertical_offset = vertical_offset * 2 - 1

    def export_json(self) -> Dict[str, Any]:
        """生成子JSON数据, 在TextSegment导出时合并到其中"""
        return {
            "background_style": self.style,
            "background_color": self.color,
            "background_alpha": self.alpha,
            "background_round_radius": self.round_radius,
            "background_height": self.height,
            "background_width": self.width,
            "background_horizontal_offset": self.horizontal_offset,
            "background_vertical_offset": self.vertical_offset,
        }

class TextBubble:
    """文本气泡素材, 与滤镜素材本质上一致"""

    global_id: str
    """气泡全局id, 由程序自动生成"""

    effect_id: str
    resource_id: str

    def __init__(self, effect_id: str, resource_id: str):
        self.global_id = uuid.uuid4().hex
        self.effect_id = effect_id
        self.resource_id = resource_id

    def export_json(self) -> Dict[str, Any]:
        return {
            "apply_target_type": 0,
            "effect_id": self.effect_id,
            "id": self.global_id,
            "resource_id": self.resource_id,
            "type": "text_shape",
            "value": 1.0,
            # 不导出path和request_id
        }

class TextEffect(TextBubble):
    """文本花字素材, 与滤镜素材本质上也一致"""

    def export_json(self) -> Dict[str, Any]:
        ret = super().export_json()
        ret["type"] = "text_effect"
        ret["source_platform"] = 1
        return ret

class TextShadow:
    """文本阴影参数"""

    alpha: float
    """阴影不透明度, 取值范围为[0, 1]"""
    color: Tuple[float, float, float]
    """阴影颜色, RGB三元组, 取值范围为[0, 1]"""
    diffuse: float
    """阴影扩散程度, 此处定义与剪映中一致, 取值范围为[0, 100]"""
    distance: float
    """阴影距离, 取值范围为[0, 100]"""
    angle: float
    """阴影角度, 取值范围为[-180, 180]"""

    def __init__(self, *, alpha: float = 1.0, color: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                 diffuse: float = 15.0, distance: float = 5.0, angle: float = -45.0):
        """
        Args:
            alpha (`float`, optional): 阴影不透明度, 取值范围为[0, 1], 默认为1.0
            color (`Tuple[float, float, float]`, optional): 阴影颜色, RGB三元组, 取值范围为[0, 1], 默认为黑色
            diffuse (`float`, optional): 阴影扩散程度, 此处定义与剪映中一致, 取值范围为[0, 100], 默认为15.0
            distance (`float`, optional): 阴影距离, 取值范围为[0, 100], 默认为5.0
            angle (`float`, optional): 阴影角度, 取值范围为[-180, 180], 默认为-45.0
        """
        self.alpha = alpha
        self.color = color
        self.diffuse = diffuse
        self.distance = distance
        self.angle = angle

    def export_json(self) -> Dict[str, Any]:
        return {
            "diffuse": self.diffuse / 100.0 / 6,  # /6是剪映自带的映射
            "alpha": self.alpha,
            "distance": self.distance,
            "content": {
                "solid": {
                    "color": list(self.color),
                }
            },
            "angle": self.angle
        }

class TextStyleRange:
    """文本样式范围类，用于富文本高亮"""
    
    def __init__(self, start: int, end: int, color: Optional[Tuple[float, float, float]] = None, 
                 size: Optional[float] = None, bold: Optional[bool] = None, 
                 italic: Optional[bool] = None, underline: Optional[bool] = None,
                 font: Optional[EffectMeta] = None, scale: Optional[float] = None,
                 shadow: Optional[TextShadow] = None):
        """
        创建文本样式范围
        
        Args:
            start (int): 起始字符索引
            end (int): 结束字符索引
            color (Tuple[float, float, float], optional): 文字颜色，RGB三元组，取值范围为[0, 1]
            size (float, optional): 字体大小
            bold (bool, optional): 是否加粗
            italic (bool, optional): 是否斜体
            underline (bool, optional): 是否下划线
        """
        self.start = start
        self.end = end
        self.color = color
        self.size = size
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.font = font
        self.scale = scale
        self.shadow = shadow

class TextSegment(VisualSegment):
    """文本片段类, 目前仅支持设置基本的字体样式"""

    text: str
    """文本内容"""
    font: Optional[EffectMeta]
    """字体类型"""
    style: TextStyle
    """字体样式"""

    border: Optional[TextBorder]
    """文本描边参数, None表示无描边"""
    background: Optional[TextBackground]
    """文本背景参数, None表示无背景"""
    shadow: Optional[TextShadow]
    """文本阴影参数, None表示无阴影"""

    bubble: Optional[TextBubble]
    """文本气泡效果, 在放入轨道时加入素材列表中"""
    effect: Optional[TextEffect]
    """文本花字效果, 在放入轨道时加入素材列表中, 目前仅支持一部分花字效果"""
    
    highlight_ranges: List[TextStyleRange]
    """富文本高亮范围列表"""

    def __init__(self, text: str, timerange: Timerange, *,
                 font: Optional[FontType] = None,
                 style: Optional[TextStyle] = None, clip_settings: Optional[ClipSettings] = None,
                 border: Optional[TextBorder] = None, background: Optional[TextBackground] = None,
                 shadow: Optional[TextShadow] = None,
                 keywords: Optional[List[str]] = None,
                 keyword_color: Optional[Tuple[float, float, float]] = None):
        """创建文本片段, 并指定其时间信息、字体样式及图像调节设置

        片段创建完成后, 可通过`ScriptFile.add_segment`方法将其添加到轨道中

        Args:
            text (`str`): 文本内容
            timerange (`Timerange`): 片段在轨道上的时间范围
            font (`Font_type`, optional): 字体类型, 默认为系统字体
            style (`TextStyle`, optional): 字体样式, 包含大小/颜色/对齐/透明度等.
            clip_settings (`ClipSettings`, optional): 图像调节设置, 默认不做任何变换
            border (`TextBorder`, optional): 文本描边参数, 默认无描边
            background (`TextBackground`, optional): 文本背景参数, 默认无背景
            shadow (`TextShadow`, optional): 文本阴影参数, 默认无阴影
            keywords (`List[str]`, optional): 需要高亮的关键词列表, 如['年轻', '享受', '生活']
            keyword_color (`Tuple[float, float, float]`, optional): 关键词高亮颜色, RGB三元组, 默认为黄色
        """
        super().__init__(uuid.uuid4().hex, None, timerange, 1.0, 1.0, False, clip_settings=clip_settings)

        self.text = text
        self.font = font.value if font else None
        self.style = style or TextStyle()
        self.border = border
        self.background = background
        self.shadow = shadow

        self.bubble = None
        self.effect = None
        self.highlight_ranges = []
        
        # 自动处理关键词高亮
        if keywords:
            self._add_keyword_highlights(keywords, keyword_color)

    @classmethod
    def create_from_template(cls, text: str, timerange: Timerange, template: "TextSegment", 
                           keywords: Optional[List[str]] = None,
                           keyword_color: Optional[Tuple[float, float, float]] = None) -> "TextSegment":
        """根据模板创建新的文本片段, 并指定其文本内容"""
        new_segment = cls(text, timerange, style=deepcopy(template.style), clip_settings=deepcopy(template.clip_settings),
                          border=deepcopy(template.border), background=deepcopy(template.background),
                          shadow=deepcopy(template.shadow), keywords=keywords, keyword_color=keyword_color)
        new_segment.font = deepcopy(template.font)
        new_segment.highlight_ranges = deepcopy(template.highlight_ranges)

        # 处理动画等
        if template.animations_instance:
            new_segment.animations_instance = deepcopy(template.animations_instance)
            new_segment.animations_instance.animation_id = uuid.uuid4().hex
            new_segment.extra_material_refs.append(new_segment.animations_instance.animation_id)
        if template.bubble:
            new_segment.add_bubble(template.bubble.effect_id, template.bubble.resource_id)
        if template.effect:
            new_segment.add_effect(template.effect.effect_id)

        return new_segment

    def add_animation(self, animation_type: Union[TextIntro, TextOutro, TextLoopAnim],
                      duration: Union[str, float, None] = None) -> "TextSegment":
        """将给定的入场/出场/循环动画添加到此片段的动画列表中, 出入场动画的持续时间可以自行设置, 循环动画则会自动填满其余无动画部分

        注意: 若希望同时使用循环动画和入出场动画, 请**先添加出入场动画再添加循环动画**

        Args:
            animation_type (`TextIntro`, `TextOutro` or `TextLoopAnim`): 文本动画类型.
            duration (`str` or `float`, optional): 动画持续时间, 单位为微秒, 仅对入场/出场动画有效.
                若传入字符串则会调用`tim()`函数进行解析. 默认使用动画的时长
        """
        if duration is None:
            duration = animation_type.value.duration
        duration = min(tim(duration), self.target_timerange.duration)

        if isinstance(animation_type, TextIntro):
            start = 0
        elif isinstance(animation_type, TextOutro):
            start = self.target_timerange.duration - duration
        elif isinstance(animation_type, TextLoopAnim):
            intro_trange = self.animations_instance and self.animations_instance.get_animation_trange("in")
            outro_trange = self.animations_instance and self.animations_instance.get_animation_trange("out")
            start = intro_trange.start if intro_trange else 0
            duration = self.target_timerange.duration - start - (outro_trange.duration if outro_trange else 0)
        else:
            raise TypeError("Invalid animation type %s" % type(animation_type))

        if self.animations_instance is None:
            self.animations_instance = SegmentAnimations()
            self.extra_material_refs.append(self.animations_instance.animation_id)

        self.animations_instance.add_animation(Text_animation(animation_type, start, duration))

        return self

    def _add_keyword_highlights(self, keywords: List[str], keyword_color: Optional[Tuple[float, float, float]] = None):
        """自动为关键词添加高亮
        
        Args:
            keywords (List[str]): 关键词列表
            keyword_color (Tuple[float, float, float], optional): 关键词颜色，默认为黄色
        """
        # 默认黄色高亮
        if keyword_color is None:
            keyword_color = (1.0, 0.984313725490196, 0.7254901960784313)
        
        # 为每个关键词查找所有出现位置并添加高亮
        for keyword in keywords:
            if not keyword.strip():  # 跳过空关键词
                continue
                
            # 查找关键词的所有出现位置
            start = 0
            while True:
                pos = self.text.find(keyword, start)
                if pos == -1:
                    break
                
                # 添加高亮范围
                end_pos = pos + len(keyword)
                self.add_highlight(pos, end_pos, color=keyword_color)
                
                # 继续查找下一个出现位置
                start = pos + 1

    def add_highlight(self, start: int, end: int, color: Optional[Tuple[float, float, float]] = None,
                     size: Optional[float] = None, bold: Optional[bool] = None,
                     italic: Optional[bool] = None, underline: Optional[bool] = None,
                     font: Optional[FontType] = None, scale: Optional[float] = None,
                     shadow: Optional[TextShadow] = None) -> "TextSegment":
        """添加高亮范围到文本中
        
        Args:
            start (int): 起始字符索引
            end (int): 结束字符索引
            color (Tuple[float, float, float], optional): 高亮颜色，RGB三元组，取值范围为[0, 1]
            size (float, optional): 字体大小
            bold (bool, optional): 是否加粗
            italic (bool, optional): 是否斜体
            underline (bool, optional): 是否下划线
            font (FontType, optional): 字体类型
            scale (float, optional): 在基础字号上的比例系数
            shadow (TextShadow, optional): 高亮阴影效果
        
        Returns:
            TextSegment: 返回自身以支持链式调用
        """
        print(f"add_highlight: {start}, {end}, {color}, {size}, {bold}, {italic}, {underline}, {font}, {scale}, {shadow}")
        if start < 0 or end > len(self.text) or start >= end:
            raise ValueError(f"Invalid range [{start}, {end}] for text length {len(self.text)}")
        
        # FontType -> EffectMeta
        _font_meta = font.value if font else None
        highlight_range = TextStyleRange(start, end, color, size, bold, italic, underline, _font_meta, scale, shadow)
        self.highlight_ranges.append(highlight_range)
        print(f"highlight_ranges: {self.highlight_ranges}")
        return self

    def add_bubble(self, effect_id: str, resource_id: str) -> "TextSegment":
        """根据素材信息添加气泡效果, 相应素材信息可通过`ScriptFile.inspect_material`从模板中获取

        Args:
            effect_id (`str`): 气泡效果的effect_id
            resource_id (`str`): 气泡效果的resource_id
        """
        self.bubble = TextBubble(effect_id, resource_id)
        self.extra_material_refs.append(self.bubble.global_id)
        return self

    def add_effect(self, effect_id: str) -> "TextSegment":
        """根据素材信息添加花字效果, 相应素材信息可通过`ScriptFile.inspect_material`从模板中获取

        Args:
            effect_id (`str`): 花字效果的effect_id, 也同时是其resource_id
        """
        self.effect = TextEffect(effect_id, effect_id)
        self.extra_material_refs.append(self.effect.global_id)
        return self

    def _create_style_ranges(self) -> List[Dict[str, Any]]:
        """创建样式范围列表，处理富文本高亮"""
        if not self.highlight_ranges:
            # 没有高亮范围，返回默认样式
            return [self._create_base_style(0, len(self.text))]
        
        # 按起始位置排序高亮范围
        sorted_ranges = sorted(self.highlight_ranges, key=lambda x: x.start)
        
        styles = []
        current_pos = 0
        
        for highlight_range in sorted_ranges:
            # 在高亮范围之前添加默认样式
            if current_pos < highlight_range.start:
                styles.append(self._create_base_style(current_pos, highlight_range.start))
            
            # 添加高亮样式
            styles.append(self._create_highlight_style(highlight_range))
            current_pos = highlight_range.end
        
        # 在最后一个高亮范围之后添加默认样式
        if current_pos < len(self.text):
            styles.append(self._create_base_style(current_pos, len(self.text)))
        
        return styles

    def _create_base_style(self, start: int, end: int) -> Dict[str, Any]:
        """创建基础样式"""
        style = {
            "fill": {
                "alpha": 1.0,
                "content": {
                    "render_type": "solid",
                    "solid": {
                        "alpha": 1.0,
                        "color": list(self.style.color)
                    }
                }
            },
            "range": [start, end],
            "size": self.style.size,
            "bold": self.style.bold,
            "italic": self.style.italic,
            "underline": self.style.underline,
            "strokes": [self.border.export_json()] if self.border else []
        }
        
        if self.font:
            style["font"] = {
                "id": self.font.resource_id,
                "path": "D:"  # 并不会真正在此处放置字体文件
            }
        if self.effect:
            style["effectStyle"] = {
                "id": self.effect.effect_id,
                "path": "C:"  # 并不会真正在此处放置素材文件
            }
        if self.shadow:
            style["shadows"] = [self.shadow.export_json()]
            
        return style

    def _create_highlight_style(self, highlight_range: TextStyleRange) -> Dict[str, Any]:
        """创建高亮样式"""
        # 使用高亮范围的属性，如果没有指定则使用默认样式
        color = highlight_range.color if highlight_range.color is not None else self.style.color
        size = highlight_range.size if highlight_range.size is not None else self.style.size
        # scale是文本的独立属性，不需要用来缩放字号
        # 字号直接使用配置的值
        bold = highlight_range.bold if highlight_range.bold is not None else self.style.bold
        italic = highlight_range.italic if highlight_range.italic is not None else self.style.italic
        underline = highlight_range.underline if highlight_range.underline is not None else self.style.underline
        
        style = {
            "fill": {
                "content": {
                    "solid": {
                        "color": list(color)
                    }
                }
            },
            "range": [highlight_range.start, highlight_range.end],
            "size": size,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "strokes": [self.border.export_json()] if self.border else []
        }
        
        # 添加scale属性（如果指定了的话）
        if highlight_range.scale is not None:
            style["scale"] = highlight_range.scale
        
        # 添加useLetterColor标志以启用高亮颜色
        if highlight_range.color is not None:
            style["useLetterColor"] = True
        
        # 优先使用高亮范围内指定的字体
        if highlight_range.font is not None:
            style["font"] = {
                "id": highlight_range.font.resource_id,
                "path": "D:"  # 并不会真正在此处放置字体文件
            }
        elif self.font:
            style["font"] = {
                "id": self.font.resource_id,
                "path": "D:"  # 并不会真正在此处放置字体文件
            }
        if self.effect:
            style["effectStyle"] = {
                "id": self.effect.effect_id,
                "path": "C:"  # 并不会真正在此处放置素材文件
            }
        
        # 阴影：优先使用高亮范围的阴影，否则使用段落默认阴影
        if getattr(highlight_range, 'shadow', None) is not None:
            style["shadows"] = [highlight_range.shadow.export_json()]
        elif self.shadow:
            style["shadows"] = [self.shadow.export_json()]
            
        return style

    def export_material(self) -> Dict[str, Any]:
        """与此文本片段联系的素材, 以此不再单独定义Text_material类"""
        # 叠加各类效果的flag
        check_flag: int = 7
        if self.border:
            check_flag |= 8
        if self.background:
            check_flag |= 16
        if self.shadow:
            check_flag |= 32

        content_json = {
            "styles": self._create_style_ranges(),
            "text": self.text
        }

        ret = {
            "id": self.material_id,
            "content": json.dumps(content_json, ensure_ascii=False),

            "typesetting": int(self.style.vertical),
            "alignment": self.style.align,
            "letter_spacing": self.style.letter_spacing * 0.05,
            "line_spacing": 0.02 + self.style.line_spacing * 0.05,

            "line_feed": 1,
            "line_max_width": self.style.max_line_width,
            "force_apply_line_max_width": False,

            "check_flag": check_flag,

            "type": "subtitle" if self.style.auto_wrapping else "text",

            # 混合 (+4)
            "global_alpha": self.style.alpha,

            # 发光 (+64)，属性由extra_material_refs记录
        }

        if self.background:
            ret.update(self.background.export_json())

        return ret
