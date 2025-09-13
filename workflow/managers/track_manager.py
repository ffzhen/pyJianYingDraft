"""
轨道管理器

负责轨道的创建和管理
"""

import pyJianYingDraft as draft
from pyJianYingDraft import TrackType
from ..core.base import BaseProcessor, WorkflowContext

class TrackManager(BaseProcessor):
    """轨道管理器"""
    
    def process(self, *args, **kwargs):
        """占位方法"""
        pass
        
    def create_basic_tracks(self):
        """创建基础轨道"""
        if not self.context.script:
            raise ValueError("请先创建草稿")
            
        # 添加基础轨道（通过调用顺序控制层级，索引递增）
        self.context.script.add_track(TrackType.video, "主视频轨道", relative_index=1)
        self.context.script.add_track(TrackType.video, "数字人视频轨道", relative_index=2)  
        self.context.script.add_track(TrackType.audio, "音频轨道", relative_index=3)
        self.context.script.add_track(TrackType.audio, "背景音乐轨道", relative_index=4)
        # 文本类：按调用顺序设置层级
        self.context.script.add_track(TrackType.text, "内容字幕轨道", relative_index=5)
        self.context.script.add_track(TrackType.text, "标题字幕轨道", relative_index=6)
        self.context.script.add_track(TrackType.text, "English Subtitles Track", relative_index=7)
        
        self._log("info", "基础轨道创建完成")
        
    def ensure_track_exists(self, track_type: TrackType, track_name: str) -> bool:
        """确保轨道存在，如果不存在则创建"""
        if not self.context.script:
            return False
            
        try:
            _ = self.context.script.tracks[track_name]
            return True
        except KeyError:
            # 计算下一个可用的相对索引
            existing_tracks = [name for name in self.context.script.tracks.keys() 
                             if self.context.script.tracks[name].track_type == track_type]
            next_index = len(existing_tracks) + 1
            self.context.script.add_track(track_type, track_name, relative_index=next_index)
            self._log("info", f"创建新轨道: {track_name}")
            return True
            
    def clear_track_segments(self, track_name: str):
        """清理轨道中的段"""
        if not self.context.script:
            return
            
        try:
            track = self.context.script.tracks[track_name]
            if hasattr(track, 'segments') and track.segments:
                self._log("debug", f"清理轨道 '{track_name}' 中的 {len(track.segments)} 个段")
                track.segments.clear()
                self._log("info", f"轨道 '{track_name}' 已清理")
        except Exception as e:
            self._log("warning", f"清理轨道 '{track_name}' 时出错: {e}")
            
    def clear_caption_tracks(self):
        """清理现有的字幕轨道以避免重叠"""
        if not self.context.script:
            return
            
        try:
            # 查找所有字幕轨道
            caption_track_names = []
            for track_name, track in self.context.script.tracks.items():
                if hasattr(track, 'track_type') and track.track_type == TrackType.text:
                    caption_track_names.append(track_name)
            
            self._log("debug", f"找到 {len(caption_track_names)} 个字幕轨道需要清理: {caption_track_names}")
            
            # 清理每个字幕轨道中的段
            for track_name in caption_track_names:
                self.clear_track_segments(track_name)
                
        except Exception as e:
            self._log("warning", f"清理字幕轨道时出错: {e}")