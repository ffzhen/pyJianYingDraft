#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
封面处理器 - 专门处理剪映封面功能
包含封面图片和封面字幕的添加功能
"""

import os
import sys
import time
import tempfile

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

import pyJianYingDraft as draft
from pyJianYingDraft import (
    DraftFolder, VideoMaterial, VideoSegment, TextSegment,
    TextStyle, ClipSettings, FontType, TrackType, tim, trange
)

class CoverProcessor:
    def __init__(self, script=None, project_name="cover_test"):
        """初始化封面处理器
        
        Args:
            script: 现有的剪映草稿对象，如果提供则复用，否则创建新的
            project_name: 项目名称（仅在创建新草稿时使用）
        """
        self.project_name = project_name
        self.script = script  # 可以传入已存在的草稿
        self.draft_folder = None
        
        # 封面相关属性
        self.cover_enabled = False
        self.cover_image_path = None
        self.cover_duration = 0.0
        
    def create_draft(self, width: int = 1080, height: int = 1920):
        """创建剪映草稿（仅在没有传入现有草稿时使用）"""
        if self.script is not None:
            print(f"[INFO] 使用传入的现有草稿")
            return self.script
            
        # 创建临时目录作为草稿文件夹
        temp_dir = tempfile.mkdtemp(prefix=f"{self.project_name}_")
        self.draft_folder = DraftFolder(temp_dir)
        self.script = self.draft_folder.create_draft(
            self.project_name, width, height, fps=30, allow_replace=True
        )
        
        # 添加基础轨道
        self.script.add_track(TrackType.video, "主视频轨道", relative_index=1)
        # 字幕背景轨道在对应字幕轨道之前创建（层级更低）
        self.script.add_track(TrackType.text, "封面字幕背景", relative_index=2)
        self.script.add_track(TrackType.text, "封面字幕轨道", relative_index=3)
        self.script.add_track(TrackType.text, "封面下方字幕轨道", relative_index=4)
        
        print(f"[OK] 草稿已创建: {self.project_name}")
        return self.script
    
    def enable_cover(self, cover_image_path: str = None, frames: int = 2, fps: int = 30):
        """启用封面功能
        
        Args:
            cover_image_path: 封面图片路径，如果为None则使用默认路径
            frames: 封面帧数，默认2帧
            fps: 帧率，默认30fps
        """
        self.cover_enabled = True
        self.cover_duration = frames / fps  # 计算封面时长
        
        if cover_image_path is None:
            # 使用默认封面路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, '..', '..')
            self.cover_image_path = os.path.join(project_root, 'resource', '查封面.jpg')
        else:
            # 使用传入的封面路径
            if not os.path.isabs(cover_image_path):
                # 如果是相对路径，相对于项目根目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.join(current_dir, '..', '..')
                self.cover_image_path = os.path.join(project_root, cover_image_path)
            else:
                # 绝对路径直接使用
                self.cover_image_path = cover_image_path
        
        print(f"[INFO] 封面已启用: 时长{self.cover_duration:.3f}秒 ({frames}帧@{fps}fps)")
        print(f"[INFO] 封面图片路径: {self.cover_image_path}")
    
    def add_cover_image(self):
        """添加封面图片"""
        print(f"[DEBUG] add_cover_image called:")
        print(f"  - cover_enabled: {self.cover_enabled}")
        print(f"  - cover_image_path: {self.cover_image_path}")
        print(f"  - cover_duration: {self.cover_duration:.6f}s")
        
        if not self.cover_enabled or not self.cover_image_path:
            print(f"[DEBUG] 跳过封面图片添加: cover_enabled={self.cover_enabled}, cover_image_path={self.cover_image_path}")
            return None
        
        if not os.path.exists(self.cover_image_path):
            print(f"[ERROR] 封面图片不存在: {self.cover_image_path}")
            return None
        
        try:
            print(f"[DEBUG] 开始创建封面图片素材...")
            # 创建图片素材（使用VideoMaterial处理图片）
            image_material = VideoMaterial(self.cover_image_path)
            print(f"[DEBUG] 图片素材创建成功")
            
            # 创建图片片段，从0开始
            print(f"[DEBUG] 创建图片片段: 0s - {self.cover_duration:.6f}s")
            image_segment = VideoSegment(
                image_material,
                trange(tim("0s"), tim(f"{self.cover_duration:.6f}s"))
            )
            print(f"[DEBUG] 图片片段创建成功")
            
            # 添加到主视频轨道
            print(f"[DEBUG] 添加封面图片到主视频轨道...")
            self.script.add_segment(image_segment, track_name="主视频轨道")
            
            print(f"[OK] 封面图片已添加: {os.path.basename(self.cover_image_path)}")
            return image_segment
            
        except Exception as e:
            print(f"[ERROR] 添加封面图片失败: {e}")
            import traceback
            print(f"[ERROR] 错误详情: {traceback.format_exc()}")
            return None
    
    def add_cover_subtitles(self, top_text: str = None, bottom_text: str = None):
        """添加封面字幕
        
        Args:
            top_text: 上方字幕文本
            bottom_text: 下方字幕文本
        """
        print(f"[DEBUG] add_cover_subtitles called:")
        print(f"  - cover_enabled: {self.cover_enabled}")
        print(f"  - top_text: '{top_text}'")
        print(f"  - bottom_text: '{bottom_text}'")
        print(f"  - cover_duration: {self.cover_duration:.6f}s")
        
        if not self.cover_enabled:
            print(f"[DEBUG] 跳过封面字幕添加: cover_enabled={self.cover_enabled}")
            return []
        
        segments = []
        
        try:
            # 添加上方字幕
            if top_text:
                print(f"[DEBUG] 创建上方字幕: '{top_text}'")
                top_segment = TextSegment(
                    top_text,
                    trange(tim("0s"), tim(f"{self.cover_duration:.6f}s")),
                    font=FontType.俪金黑,
                    style=TextStyle(
                        size=24.0,
                        color=(1.0, 1.0, 1.0),  # 白色
                        bold=True,
                        align=0,  # 居中对齐
                        auto_wrapping=True,
                        max_line_width=0.8
                    ),
                    clip_settings=ClipSettings(transform_y=0.3, scale_x=1.2, scale_y=1.2)  # 上方位置
                )
                print(f"[DEBUG] 添加上方字幕到轨道: 封面字幕轨道")
                self.script.add_segment(top_segment, track_name="封面字幕轨道")
                segments.append(top_segment)
                print(f"[OK] 封面上方字幕已添加: {top_text}")
            
            # 添加下方字幕
            if bottom_text:
                print(f"[DEBUG] 创建下方字幕: '{bottom_text}'")
                bottom_segment = TextSegment(
                    bottom_text,
                    trange(tim("0s"), tim(f"{self.cover_duration:.6f}s")),
                    font=FontType.俪金黑,
                    style=TextStyle(
                        size=20.0,
                        color=(1.0, 0.7529411765, 0.2470588235),  # 黄色高亮
                        bold=True,
                        align=0,  # 居中对齐
                        auto_wrapping=True,
                        max_line_width=0.8
                    ),
                    clip_settings=ClipSettings(transform_y=-0.3, scale_x=1.1, scale_y=1.1)  # 下方位置
                )
                print(f"[DEBUG] 添加下方字幕到轨道: 封面下方字幕轨道")
                self.script.add_segment(bottom_segment, track_name="封面下方字幕轨道")
                segments.append(bottom_segment)
                print(f"[OK] 封面下方字幕已添加: {bottom_text}")
            
            print(f"[INFO] 📝 封面字幕已添加: 上方='{top_text}', 下方='{bottom_text}'")
            
        except Exception as e:
            print(f"[ERROR] 添加封面字幕失败: {e}")
            import traceback
            print(f"[ERROR] 错误详情: {traceback.format_exc()}")
        
        return segments
    
    def process_cover_and_get_timing(self, top_text: str = None, bottom_text: str = None):
        """处理封面并返回时间偏移信息
        
        Args:
            top_text: 上方字幕文本
            bottom_text: 下方字幕文本
            
        Returns:
            dict: 包含封面处理结果和时间信息的字典
                {
                    'success': bool,          # 是否成功
                    'cover_duration': float,  # 封面时长（秒）
                    'time_offset': float,     # 时间偏移量（秒）
                    'cover_enabled': bool     # 封面是否启用
                }
        """
        result = {
            'success': False,
            'cover_duration': 0.0,
            'time_offset': 0.0,
            'cover_enabled': self.cover_enabled
        }
        
        if not self.cover_enabled:
            print("[INFO] 封面未启用，跳过封面处理")
            result['success'] = True  # 未启用也算成功
            return result
        
        try:
            print(f"[INFO] 开始处理封面：图片 + 字幕")
            
            # 1. 添加封面图片
            image_segment = self.add_cover_image()
            if image_segment is None:
                print("[ERROR] 封面图片添加失败")
                return result
                
            # 2. 添加封面字幕
            subtitle_segments = self.add_cover_subtitles(top_text, bottom_text)
            
            # 3. 设置返回信息
            result['success'] = True
            result['cover_duration'] = self.cover_duration
            result['time_offset'] = self.cover_duration  # 封面时长即为后续内容的时间偏移
            result['cover_enabled'] = True
            
            print(f"[OK] 封面处理完成")
            print(f"   - 封面时长: {self.cover_duration:.6f}秒")
            print(f"   - 后续内容时间偏移: {result['time_offset']:.6f}秒")
            print(f"   - 封面图片: {'成功' if image_segment else '失败'}")
            print(f"   - 封面字幕: {len(subtitle_segments)}段")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 封面处理失败: {e}")
            import traceback
            print(f"[ERROR] 错误详情: {traceback.format_exc()}")
            return result
    
    def get_cover_timing_info(self):
        """获取封面时间信息（不添加任何内容，仅返回时间信息）
        
        Returns:
            dict: 封面时间信息
        """
        return {
            'cover_enabled': self.cover_enabled,
            'cover_duration': self.cover_duration if self.cover_enabled else 0.0,
            'time_offset': self.cover_duration if self.cover_enabled else 0.0,
            'cover_image_path': self.cover_image_path if self.cover_enabled else None
        }

    def save_draft(self):
        """保存草稿"""
        if self.script:
            self.script.save()
            print(f"[OK] 草稿已保存")
            return True
        return False


def main():
    """测试封面功能 - 演示独立使用和集成使用两种方式"""
    print("="*60)
    print("封面处理器测试")
    print("="*60)
    try:
        # 模拟主工作流中的使用方式
        # 1. 创建主草稿（模拟主工作流创建的草稿）
        temp_dir = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
        draft_folder = DraftFolder(temp_dir)
        main_script = draft_folder.create_draft("integration_test_" + str(int(time.time())), 1080, 1920, fps=30)
        
        # 添加基础轨道（模拟主工作流的轨道结构）
        main_script.add_track(TrackType.video, "主视频轨道", relative_index=1)
        main_script.add_track(TrackType.text, "封面字幕轨道", relative_index=2)
        main_script.add_track(TrackType.text, "封面下方字幕轨道", relative_index=3)
        
        # 2. 创建封面处理器并传入共享的草稿
        cover_processor = CoverProcessor(script=main_script)
        
        # 3. 启用封面
        cover_processor.enable_cover(
            cover_image_path="resource/查封面.jpg",
            frames=2,
            fps=30
        )
        
        # 4. 处理封面并获取时间偏移信息
        cover_timing = cover_processor.process_cover_and_get_timing(
            top_text="农村宅基地",
            bottom_text="农村还有宅基地的好好看这条视频"
        )
        
        print(f"\n封面时间偏移信息:")
        print(f"  - 后续内容需要偏移: {cover_timing['time_offset']:.6f}秒")
        timing_info = cover_processor.get_cover_timing_info()
        print(f"  - 封面图片路径: {timing_info['cover_image_path']}")
        
        # 5. 模拟主工作流根据封面时间偏移调整后续内容
        if cover_timing['success'] and cover_timing['time_offset'] > 0:
            print(f"\n[模拟] 主工作流将根据封面时长 {cover_timing['time_offset']:.6f}秒 调整所有后续内容时间")
            print("[模拟] 数字人视频、音频、字幕等都将从 {:.6f}秒 开始".format(cover_timing['time_offset']))
        
        # 6. 保存集成测试草稿
        main_script.save()
        
        print("\n[SUCCESS] 集成封面测试完成！")
        print("请打开剪映查看生成的集成测试项目")
        
    except Exception as e:
        print(f"[ERROR] 集成封面测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()