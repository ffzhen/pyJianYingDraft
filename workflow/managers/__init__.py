"""
管理器模块

提供时长、轨道、素材等管理功能
"""

from .duration_manager import DurationManager
from .track_manager import TrackManager  
from .material_manager import MaterialManager

__all__ = [
    'DurationManager',
    'TrackManager',
    'MaterialManager'
]