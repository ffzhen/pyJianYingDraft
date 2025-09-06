"""
停顿处理器

负责音频停顿相关的处理功能
"""

import pyJianYingDraft as draft
from pyJianYingDraft import tim, trange
from typing import Optional, List, Dict, Any, Tuple
from ..core.base import BaseProcessor, WorkflowContext
from ..core.exceptions import ProcessingError

class PauseProcessor(BaseProcessor):
    """停顿处理器"""
    
    def process(self, *args, **kwargs):
        """占位方法"""
        pass
        
    def add_audio_pause(self, start_time: float, pause_duration: float, track_name: str = "音频轨道"):
        """在指定位置添加音频停顿
        
        Args:
            start_time: 停顿开始时间(秒)
            pause_duration: 停顿时长(秒)
            track_name: 音频轨道名称
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        # 验证时长边界
        from ..managers.duration_manager import DurationManager
        duration_manager = DurationManager(self.context, self.logger)
        pause_duration = duration_manager.validate_duration_bounds(pause_duration, "音频停顿")
        
        # 验证开始时间
        effective_duration = self.context.get_effective_video_duration()
        if effective_duration > 0 and start_time >= effective_duration:
            self._log("warning", f"停顿开始时间({start_time:.2f}s)超出有效时长({effective_duration:.2f}s)，跳过")
            return
        
        # 确保停顿不会超出边界
        if effective_duration > 0:
            available_duration = effective_duration - start_time
            pause_duration = min(pause_duration, available_duration)
        
        self._log("info", f"在 {start_time:.2f}s 处添加 {pause_duration:.2f}s 的音频停顿")
        
        # 这里可以实现具体的停顿逻辑
        # 例如：分割现有音频段，插入静音段等
        # 由于pyJianYingDraft的具体API限制，这里提供接口设计
        
        return {
            "start_time": start_time,
            "duration": pause_duration,
            "track_name": track_name
        }
        
    def add_video_pause(self, start_time: float, pause_duration: float, 
                       freeze_frame: bool = True, track_name: str = "主视频轨道"):
        """在指定位置添加视频停顿
        
        Args:
            start_time: 停顿开始时间(秒)
            pause_duration: 停顿时长(秒)  
            freeze_frame: 是否冻结帧（True）还是黑屏（False）
            track_name: 视频轨道名称
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        # 验证时长边界
        from ..managers.duration_manager import DurationManager
        duration_manager = DurationManager(self.context, self.logger)
        pause_duration = duration_manager.validate_duration_bounds(pause_duration, "视频停顿")
        
        # 验证开始时间
        effective_duration = self.context.get_effective_video_duration()
        if effective_duration > 0 and start_time >= effective_duration:
            self._log("warning", f"停顿开始时间({start_time:.2f}s)超出有效时长({effective_duration:.2f}s)，跳过")
            return
            
        freeze_type = "冻结帧" if freeze_frame else "黑屏"
        self._log("info", f"在 {start_time:.2f}s 处添加 {pause_duration:.2f}s 的视频停顿({freeze_type})")
        
        # 这里可以实现具体的视频停顿逻辑
        # 例如：分割视频段，插入冻结帧或黑屏段等
        
        return {
            "start_time": start_time,
            "duration": pause_duration,
            "freeze_frame": freeze_frame,
            "track_name": track_name
        }
        
    def add_synchronized_pause(self, start_time: float, pause_duration: float, 
                              audio_track: str = "音频轨道", 
                              video_track: str = "主视频轨道",
                              freeze_frame: bool = True):
        """添加同步的音视频停顿
        
        Args:
            start_time: 停顿开始时间(秒)
            pause_duration: 停顿时长(秒)
            audio_track: 音频轨道名称
            video_track: 视频轨道名称  
            freeze_frame: 视频是否冻结帧
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        self._log("info", f"添加同步停顿: {start_time:.2f}s 开始，持续 {pause_duration:.2f}s")
        
        # 添加音频停顿
        audio_result = self.add_audio_pause(start_time, pause_duration, audio_track)
        
        # 添加视频停顿  
        video_result = self.add_video_pause(start_time, pause_duration, freeze_frame, video_track)
        
        return {
            "audio_pause": audio_result,
            "video_pause": video_result,
            "synchronized": True
        }
        
    def detect_natural_pauses(self, asr_result: List[Dict[str, Any]], 
                             min_gap: float = 0.5, min_pause_duration: float = 0.3) -> List[Dict[str, float]]:
        """从ASR结果检测自然停顿点
        
        Args:
            asr_result: ASR识别结果列表，每个元素包含start_time, end_time
            min_gap: 最小间隙时长(秒)，小于此值的间隙不被认为是停顿
            min_pause_duration: 最小停顿时长(秒)
            
        Returns:
            停顿点列表，每个元素包含start_time, duration
        """
        if not asr_result or len(asr_result) < 2:
            self._log("warning", "ASR结果不足，无法检测自然停顿")
            return []
            
        pauses = []
        
        # 按开始时间排序
        sorted_segments = sorted(asr_result, key=lambda x: float(x.get('start_time', 0)))
        
        for i in range(len(sorted_segments) - 1):
            current_segment = sorted_segments[i]
            next_segment = sorted_segments[i + 1]
            
            try:
                current_end = float(current_segment.get('end_time', 0))
                next_start = float(next_segment.get('start_time', 0))
                
                # 计算间隙时长
                gap_duration = next_start - current_end
                
                if gap_duration >= min_gap:
                    # 计算建议的停顿时长（不超过原间隙）
                    pause_duration = max(min_pause_duration, min(gap_duration * 0.8, 2.0))
                    
                    # 验证时长边界
                    from ..managers.duration_manager import DurationManager
                    duration_manager = DurationManager(self.context, self.logger)
                    pause_duration = duration_manager.validate_duration_bounds(pause_duration, "自然停顿")
                    
                    pauses.append({
                        "start_time": round(current_end, 2),
                        "duration": round(pause_duration, 2),
                        "gap_duration": round(gap_duration, 2),
                        "natural": True
                    })
                    
            except (ValueError, KeyError) as e:
                self._log("warning", f"处理停顿检测时出错: {e}, 段落: {current_segment}, {next_segment}")
                continue
        
        self._log("info", f"检测到 {len(pauses)} 个自然停顿点")
        
        return pauses
        
    def apply_natural_pauses(self, asr_result: List[Dict[str, Any]], 
                            pause_intensity: float = 0.5,
                            audio_track: str = "音频轨道",
                            video_track: str = "主视频轨道"):
        """应用自然停顿到轨道
        
        Args:
            asr_result: ASR识别结果
            pause_intensity: 停顿强度(0-1)，影响停顿的时长
            audio_track: 音频轨道名称
            video_track: 视频轨道名称
        """
        if not self.context.script:
            raise ProcessingError("请先创建草稿")
            
        # 检测自然停顿点
        natural_pauses = self.detect_natural_pauses(asr_result)
        
        if not natural_pauses:
            self._log("info", "未检测到自然停顿点")
            return []
            
        applied_pauses = []
        
        for pause_info in natural_pauses:
            try:
                start_time = pause_info["start_time"]
                base_duration = pause_info["duration"]
                
                # 根据停顿强度调整时长
                adjusted_duration = base_duration * pause_intensity
                adjusted_duration = max(0.2, min(adjusted_duration, 3.0))  # 限制在0.2-3秒之间
                
                # 应用同步停顿
                result = self.add_synchronized_pause(
                    start_time, 
                    adjusted_duration,
                    audio_track,
                    video_track,
                    freeze_frame=True
                )
                
                applied_pauses.append({
                    **pause_info,
                    "applied_duration": round(adjusted_duration, 2),
                    "result": result
                })
                
            except Exception as e:
                self._log("warning", f"应用停顿时出错: {e}, 停顿信息: {pause_info}")
                continue
        
        self._log("info", f"成功应用 {len(applied_pauses)} 个自然停顿")
        
        return applied_pauses
        
    def get_pause_statistics(self) -> Dict[str, Any]:
        """获取停顿统计信息
        
        Returns:
            包含停顿统计信息的字典
        """
        # 这里可以统计项目中的停顿信息
        # 由于具体实现依赖于pyJianYingDraft的API，这里提供接口设计
        
        stats = {
            "total_audio_pauses": 0,
            "total_video_pauses": 0, 
            "total_pause_duration": 0.0,
            "avg_pause_duration": 0.0,
            "pause_density": 0.0  # 停顿密度（停顿数/总时长）
        }
        
        # 计算停顿密度
        if self.context.project_duration > 0:
            total_pauses = stats["total_audio_pauses"] + stats["total_video_pauses"]
            stats["pause_density"] = total_pauses / self.context.project_duration
            
        return stats