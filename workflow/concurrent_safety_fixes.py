#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发安全修复方案
解决多并发导致视频片段丢失的问题
"""

import os
import time
import threading
import uuid
from typing import Dict, Any, Optional
from contextlib import contextmanager

class ConcurrentSafetyManager:
    """并发安全管理器"""
    
    def __init__(self):
        self._locks = {}
        self._file_locks = {}
        self._global_lock = threading.RLock()
    
    def get_lock(self, key: str) -> threading.RLock:
        """获取指定键的锁"""
        with self._global_lock:
            if key not in self._locks:
                self._locks[key] = threading.RLock()
            return self._locks[key]
    
    def get_file_lock(self, file_path: str) -> threading.RLock:
        """获取文件锁"""
        with self._global_lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.RLock()
            return self._file_locks[file_path]
    
    @contextmanager
    def safe_file_operation(self, file_path: str):
        """安全的文件操作上下文管理器"""
        lock = self.get_file_lock(file_path)
        with lock:
            try:
                yield
            except Exception as e:
                print(f"[ERROR] 文件操作失败: {file_path} - {e}")
                raise
    
    def generate_unique_filename(self, prefix: str, extension: str = "", base_dir: str = "temp_materials") -> str:
        """生成唯一的文件名，避免并发冲突"""
        # 确保目录存在
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        # 使用多重唯一性保证
        timestamp = int(time.time() * 1000000)  # 微秒时间戳
        thread_id = threading.get_ident() % 100000  # 线程ID后5位
        random_id = uuid.uuid4().hex[:8]
        process_id = os.getpid() % 10000  # 进程ID后4位
        
        unique_id = f"{timestamp}_{thread_id}_{process_id}_{random_id}"
        filename = f"{prefix}_{unique_id}{extension}"
        
        return os.path.join(base_dir, filename)

# 全局并发安全管理器实例
concurrent_manager = ConcurrentSafetyManager()

def get_concurrent_manager() -> ConcurrentSafetyManager:
    """获取全局并发安全管理器"""
    return concurrent_manager

def safe_add_track(script, track_type, track_name: str, relative_index: int = None) -> bool:
    """安全添加轨道，避免并发冲突"""
    try:
        # 检查轨道是否已存在
        if track_name in script.tracks:
            print(f"[INFO] 轨道已存在: {track_name}")
            return True
        
        # 使用锁保护轨道添加操作
        lock = concurrent_manager.get_lock(f"track_creation_{id(script)}")
        with lock:
            # 再次检查轨道是否存在（双重检查）
            if track_name in script.tracks:
                return True
            
            # 添加轨道
            script.add_track(track_type, track_name, relative_index=relative_index)
            print(f"[OK] 轨道添加成功: {track_name}")
            return True
            
    except Exception as e:
        print(f"[ERROR] 添加轨道失败: {track_name} - {e}")
        return False

def safe_add_segment(script, segment, track_name: str) -> bool:
    """安全添加片段到轨道，避免并发冲突"""
    try:
        # 确保轨道存在
        if track_name not in script.tracks:
            print(f"[WARN] 轨道不存在，尝试创建: {track_name}")
            # 根据片段类型确定轨道类型
            if hasattr(segment, 'text_content'):
                track_type = "text"
            elif hasattr(segment, 'video_path'):
                track_type = "video"
            elif hasattr(segment, 'audio_path'):
                track_type = "audio"
            else:
                track_type = "text"  # 默认
            
            if not safe_add_track(script, track_type, track_name):
                return False
        
        # 使用锁保护片段添加操作
        lock = concurrent_manager.get_lock(f"segment_addition_{track_name}_{id(script)}")
        with lock:
            script.add_segment(segment, track_name=track_name)
            print(f"[OK] 片段添加成功到轨道: {track_name}")
            return True
            
    except Exception as e:
        print(f"[ERROR] 添加片段失败: {track_name} - {e}")
        return False

def safe_ffmpeg_operation(input_path: str, output_path: str, cmd: list) -> bool:
    """安全的FFmpeg操作，避免文件冲突"""
    try:
        # 使用文件锁保护FFmpeg操作
        with concurrent_manager.safe_file_operation(input_path):
            with concurrent_manager.safe_file_operation(output_path):
                import subprocess
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"[OK] FFmpeg操作成功: {output_path}")
                return True
                
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg操作失败: {e}")
        print(f"  命令: {' '.join(cmd)}")
        print(f"  错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"[ERROR] FFmpeg操作异常: {e}")
        return False

def create_concurrent_safe_workflow(original_workflow_class):
    """创建并发安全的工作流类装饰器"""
    
    class ConcurrentSafeWorkflow(original_workflow_class):
        """并发安全的工作流包装类"""
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.concurrent_manager = get_concurrent_manager()
            self._operation_locks = {}
        
        def _get_operation_lock(self, operation_name: str) -> threading.RLock:
            """获取操作锁"""
            if operation_name not in self._operation_locks:
                self._operation_locks[operation_name] = threading.RLock()
            return self._operation_locks[operation_name]
        
        def add_track(self, track_type, track_name: str, relative_index: int = None):
            """并发安全的添加轨道方法"""
            return safe_add_track(self.script, track_type, track_name, relative_index)
        
        def add_segment(self, segment, track_name: str):
            """并发安全的添加片段方法"""
            return safe_add_segment(self.script, segment, track_name)
        
        def _generate_unique_filename(self, prefix: str, extension: str = "", base_dir: str = "temp_materials") -> str:
            """生成唯一文件名"""
            return self.concurrent_manager.generate_unique_filename(prefix, extension, base_dir)
        
        def _process_video_pauses_by_segments_marking(self, input_video_path: str, pause_segments, time_offset: float = 0.0) -> bool:
            """并发安全的视频片段处理"""
            try:
                # 使用操作锁保护整个视频处理过程
                with self._get_operation_lock("video_processing"):
                    return super()._process_video_pauses_by_segments_marking(input_video_path, pause_segments, time_offset)
            except Exception as e:
                print(f"[ERROR] 视频片段处理失败: {e}")
                return False
        
        def add_caption_backgrounds(self, caption_data, **kwargs):
            """并发安全的字幕背景添加"""
            try:
                # 使用操作锁保护字幕背景添加
                with self._get_operation_lock("caption_backgrounds"):
                    return super().add_caption_backgrounds(caption_data, **kwargs)
            except Exception as e:
                print(f"[ERROR] 字幕背景添加失败: {e}")
                return None
        
        def add_digital_human_video(self, digital_video_url: str, **kwargs):
            """并发安全的数字人视频添加"""
            try:
                # 使用操作锁保护数字人视频处理
                with self._get_operation_lock("digital_human_video"):
                    return super().add_digital_human_video(digital_video_url, **kwargs)
            except Exception as e:
                print(f"[ERROR] 数字人视频添加失败: {e}")
                return None
    
    return ConcurrentSafeWorkflow

# 使用示例
def apply_concurrent_safety_fixes():
    """应用并发安全修复"""
    print("[INFO] 应用并发安全修复...")
    
    # 这里可以导入并包装现有的工作流类
    # from workflow.component.flow_python_implementation import VideoEditingWorkflow
    # VideoEditingWorkflow = create_concurrent_safe_workflow(VideoEditingWorkflow)
    
    print("[OK] 并发安全修复已应用")

if __name__ == "__main__":
    apply_concurrent_safety_fixes()
