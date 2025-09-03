"""
基于火山ASR的音频停顿检测和处理模块

利用火山ASR的逐字时间戳信息来精确检测和移除音频中的停顿
"""

import os
import subprocess
import json
import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class ASRSilenceDetector:
    """基于ASR的停顿检测器"""
    
    def __init__(self, min_pause_duration: float = 0.8, max_word_gap: float = 1.5):
        """
        初始化ASR停顿检测器
        
        Args:
            min_pause_duration: 最小停顿时长(秒)，默认0.8秒
            max_word_gap: 单词间最大间隔(秒)，默认1.5秒
        """
        self.min_pause_duration = min_pause_duration
        self.max_word_gap = max_word_gap
        
    def detect_pauses_from_asr(self, asr_result: Dict[str, Any]) -> List[Tuple[float, float]]:
        """
        从ASR结果中检测停顿段落
        
        Args:
            asr_result: 火山ASR识别结果
            
        Returns:
            List[Tuple[float, float]]: 停顿段落列表，每个元素为(开始时间, 结束时间)
        """
        pause_segments = []
        
        try:
            utterances = asr_result.get('utterances', [])
            print(f"[DEBUG] 检测到 {len(utterances)} 个utterances")
            
            for i, utterance in enumerate(utterances):
                words = utterance.get('words', [])
                utterance_text = utterance.get('text', '')
                print(f"[DEBUG] Utterance {i+1}: '{utterance_text}' ({len(words)} 个单词)")
                
                if not words:
                    continue
                    
                # 检查utterance之间的停顿
                if i > 0:
                    prev_utterance = utterances[i-1]
                    prev_end = prev_utterance.get('end_time', 0) / 1000  # 转换为秒
                    curr_start = utterance.get('start_time', 0) / 1000
                    
                    pause_duration = curr_start - prev_end
                    print(f"[DEBUG] Utterance间停顿: {prev_end:.3f}s - {curr_start:.3f}s (时长: {pause_duration:.3f}s)")
                    
                    if pause_duration >= self.min_pause_duration:
                        pause_segments.append((prev_end, curr_start))
                        print(f"[DEBUG] ✓ 添加utterance间停顿: {prev_end:.3f}s - {curr_start:.3f}s")
                
                # 检查单词之间的停顿
                for j in range(len(words) - 1):
                    current_word = words[j]
                    next_word = words[j + 1]
                    
                    current_end = current_word.get('end_time', 0) / 1000
                    next_start = next_word.get('start_time', 0) / 1000
                    
                    word_gap = next_start - current_end
                    
                    if word_gap >= self.max_word_gap:
                        pause_segments.append((current_end, next_start))
            
            # 检查音频开始和结束的停顿
            if utterances:
                first_utterance = utterances[0]
                last_utterance = utterances[-1]
                total_duration = asr_result.get('duration', 0)
                
                # 音频开始的停顿
                first_word_start = first_utterance.get('start_time', 0) / 1000
                print(f"[DEBUG] 音频开始停顿: 0.000s - {first_word_start:.3f}s (时长: {first_word_start:.3f}s)")
                
                if first_word_start >= self.min_pause_duration:
                    pause_segments.append((0.0, first_word_start))
                    print(f"[DEBUG] ✓ 添加音频开始停顿: 0.000s - {first_word_start:.3f}s")
                else:
                    print(f"[DEBUG] ✗ 音频开始停顿太短 ({first_word_start:.3f}s < {self.min_pause_duration}s)，不添加")
                
                # 音频结束的停顿
                last_word_end = last_utterance.get('end_time', 0) / 1000
                end_pause_duration = total_duration - last_word_end
                print(f"[DEBUG] 音频结束停顿: {last_word_end:.3f}s - {total_duration:.3f}s (时长: {end_pause_duration:.3f}s)")
                
                if end_pause_duration >= self.min_pause_duration:
                    pause_segments.append((last_word_end, total_duration))
                    print(f"[DEBUG] ✓ 添加音频结束停顿: {last_word_end:.3f}s - {total_duration:.3f}s")
                else:
                    print(f"[DEBUG] ✗ 音频结束停顿太短 ({end_pause_duration:.3f}s < {self.min_pause_duration}s)，不添加")
            
            # 合并相邻或重叠的停顿段落
            pause_segments = self._merge_overlapping_segments(pause_segments)
            
            print(f"[DEBUG] 最终检测到 {len(pause_segments)} 个停顿段落:")
            for i, (start, end) in enumerate(pause_segments):
                print(f"[DEBUG]   停顿 {i+1}: {start:.3f}s - {end:.3f}s (时长: {end-start:.3f}s)")
            
        except Exception as e:
            logger.error(f"从ASR结果检测停顿失败: {e}")
            
        return pause_segments
    
    def _merge_overlapping_segments(self, segments: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """合并相邻或重叠的时间段落"""
        if not segments:
            return []
        
        # 按开始时间排序
        segments.sort(key=lambda x: x[0])
        
        merged = [segments[0]]
        
        for current_start, current_end in segments[1:]:
            last_start, last_end = merged[-1]
            
            if current_start <= last_end + 0.1:  # 允许0.1秒的重叠或间隔
                # 合并段落
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))
        
        return merged
    
    def get_speech_segments(self, asr_result: Dict[str, Any]) -> List[Tuple[float, float]]:
        """
        获取有声段落（非停顿段落）
        
        Args:
            asr_result: 火山ASR识别结果
            
        Returns:
            List[Tuple[float, float]]: 有声段落列表
        """
        pause_segments = self.detect_pauses_from_asr(asr_result)
        total_duration = asr_result.get('duration', 0)
        
        if not pause_segments:
            return [(0.0, total_duration)]
        
        # 构建有声段落
        speech_segments = []
        
        # 音频开始到第一个停顿段落
        first_pause_start = pause_segments[0][0]
        if first_pause_start > 0:
            speech_segments.append((0.0, first_pause_start))
        
        # 停顿段落之间的有声部分
        for i in range(len(pause_segments) - 1):
            prev_end = pause_segments[i][1]
            next_start = pause_segments[i + 1][0]
            if next_start > prev_end:
                speech_segments.append((prev_end, next_start))
        
        # 最后一个停顿段落到音频结束
        last_pause_end = pause_segments[-1][1]
        if last_pause_end < total_duration:
            speech_segments.append((last_pause_end, total_duration))
        
        return speech_segments
    
    def calculate_pause_statistics(self, pause_segments: List[Tuple[float, float]]) -> Dict[str, float]:
        """计算停顿统计信息"""
        if not pause_segments:
            return {
                'total_pause_duration': 0.0,
                'pause_count': 0,
                'average_pause_duration': 0.0,
                'max_pause_duration': 0.0,
                'min_pause_duration': 0.0
            }
        
        durations = [end - start for start, end in pause_segments]
        
        return {
            'total_pause_duration': sum(durations),
            'pause_count': len(pause_segments),
            'average_pause_duration': np.mean(durations),
            'max_pause_duration': max(durations),
            'min_pause_duration': min(durations)
        }


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self):
        """初始化音频处理器"""
        pass
    
    def extract_audio_segments(self, input_audio_path: str, segments: List[Tuple[float, float]], 
                              output_audio_path: str) -> bool:
        """
        从音频中提取指定段落
        
        Args:
            input_audio_path: 输入音频路径
            segments: 要提取的时间段落列表
            output_audio_path: 输出音频路径
            
        Returns:
            bool: 是否成功
        """
        try:
            if not segments:
                logger.warning("没有要提取的段落")
                return False
            
            # 构建ffmpeg过滤图
            filter_complex = []
            
            for i, (start, end) in enumerate(segments):
                duration = end - start
                filter_complex.append(f'[0:a]atrim=start={start}:duration={duration},asetpts=PTS-STARTPTS[a{i}]')
            
            # 拼接所有段落
            inputs = ''.join(f'[a{i}]' for i in range(len(segments)))
            filter_complex.append(f'{inputs}concat=n={len(segments)}:v=0:a=1[out]')
            
            cmd = [
                'ffmpeg',
                '-i', input_audio_path,
                '-filter_complex', ';'.join(filter_complex),
                '-map', '[out]',
                '-y',  # 覆盖输出文件
                output_audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                logger.info(f"音频段落提取成功: {output_audio_path}")
                return True
            else:
                logger.error(f"音频段落提取失败: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg执行失败: {e}")
            return False
        except FileNotFoundError:
            logger.error("ffmpeg未找到，请确保ffmpeg已安装并添加到PATH")
            return False
        except Exception as e:
            logger.error(f"音频处理失败: {e}")
            return False


class VideoProcessor:
    """视频处理器"""
    
    def __init__(self):
        """初始化视频处理器"""
        pass
    
    def extract_video_segments(self, input_video_path: str, segments: List[Tuple[float, float]], 
                              output_video_path: str) -> bool:
        """
        从视频中提取指定段落
        
        Args:
            input_video_path: 输入视频路径
            segments: 要提取的时间段落列表
            output_video_path: 输出视频路径
            
        Returns:
            bool: 是否成功
        """
        try:
            if not segments:
                logger.warning("没有要提取的视频段落")
                return False
            
            # 构建ffmpeg过滤图
            filter_complex = []
            
            for i, (start, end) in enumerate(segments):
                duration = end - start
                filter_complex.append(f'[0:v]atrim=start={start}:duration={duration},setpts=PTS-STARTPTS[v{i}]')
                filter_complex.append(f'[0:a]atrim=start={start}:duration={duration},asetpts=PTS-STARTPTS[a{i}]')
            
            # 拼接所有段落
            video_inputs = ''.join(f'[v{i}]' for i in range(len(segments)))
            audio_inputs = ''.join(f'[a{i}]' for i in range(len(segments)))
            filter_complex.append(f'{video_inputs}concat=n={len(segments)}:v=1:a=0[outv]')
            filter_complex.append(f'{audio_inputs}concat=n={len(segments)}:v=0:a=1[outa]')
            
            cmd = [
                'ffmpeg',
                '-i', input_video_path,
                '-filter_complex', ';'.join(filter_complex),
                '-map', '[outv]',
                '-map', '[outa]',
                '-y',  # 覆盖输出文件
                output_video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                logger.info(f"视频段落提取成功: {output_video_path}")
                return True
            else:
                logger.error(f"视频段落提取失败: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg执行失败: {e}")
            return False
        except FileNotFoundError:
            logger.error("ffmpeg未找到，请确保ffmpeg已安装并添加到PATH")
            return False
        except Exception as e:
            logger.error(f"视频处理失败: {e}")
            return False


class ASRBasedSilenceRemover:
    """基于ASR的停顿移除器"""
    
    def __init__(self, min_pause_duration: float = 0.8, max_word_gap: float = 1.5):
        """
        初始化停顿移除器
        
        Args:
            min_pause_duration: 最小停顿时长(秒)
            max_word_gap: 单词间最大间隔(秒)
        """
        self.pause_detector = ASRSilenceDetector(min_pause_duration, max_word_gap)
        self.audio_processor = AudioProcessor()
        self.video_processor = VideoProcessor()
    
    def remove_pauses_from_audio(self, audio_path: str, asr_result: Dict[str, Any], 
                               output_audio_path: str) -> Dict[str, Any]:
        """
        从音频中移除停顿
        
        Args:
            audio_path: 原始音频路径
            asr_result: 火山ASR识别结果
            output_audio_path: 输出音频路径
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        result = {
            'success': False,
            'pause_segments': [],
            'speech_segments': [],
            'original_duration': 0,
            'processed_duration': 0,
            'removed_duration': 0,
            'pause_statistics': {},
            'output_audio_path': output_audio_path
        }
        
        try:
            original_duration = asr_result.get('duration', 0)
            result['original_duration'] = original_duration
            
            # 检测停顿段落
            pause_segments = self.pause_detector.detect_pauses_from_asr(asr_result)
            result['pause_segments'] = pause_segments
            
            # 获取有声段落
            speech_segments = self.pause_detector.get_speech_segments(asr_result)
            result['speech_segments'] = speech_segments
            
            # 计算统计信息
            pause_stats = self.pause_detector.calculate_pause_statistics(pause_segments)
            result['pause_statistics'] = pause_stats
            
            # 计算处理的时长
            processed_duration = sum(end - start for start, end in speech_segments)
            removed_duration = original_duration - processed_duration
            result['processed_duration'] = processed_duration
            result['removed_duration'] = removed_duration
            
            # 提取有声段落
            if speech_segments and speech_segments != [(0.0, original_duration)]:
                success = self.audio_processor.extract_audio_segments(
                    audio_path, speech_segments, output_audio_path
                )
                
                if success:
                    result['success'] = True
                    logger.info(f"停顿移除完成，移除 {removed_duration:.2f} 秒停顿")
                    logger.info(f"停顿统计: 总停顿时长 {pause_stats['total_pause_duration']:.2f} 秒，"
                               f"停顿次数 {pause_stats['pause_count']} 次")
                else:
                    logger.error("停顿移除失败")
            else:
                result['success'] = True
                logger.info("未检测到需要移除的停顿")
                
        except Exception as e:
            logger.error(f"停顿移除处理失败: {e}")
            
        return result
    
    def remove_pauses_from_audio_and_video(self, audio_path: str, video_path: str, 
                                         asr_result: Dict[str, Any], 
                                         output_audio_path: str, 
                                         output_video_path: str) -> Dict[str, Any]:
        """
        同时从音频和视频中移除停顿段落
        
        Args:
            audio_path: 原始音频路径
            video_path: 原始视频路径
            asr_result: 火山ASR识别结果
            output_audio_path: 输出音频路径
            output_video_path: 输出视频路径
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        result = {
            'success': False,
            'pause_segments': [],
            'speech_segments': [],
            'original_duration': 0,
            'processed_duration': 0,
            'removed_duration': 0,
            'pause_statistics': {},
            'output_audio_path': output_audio_path,
            'output_video_path': output_video_path
        }
        
        try:
            original_duration = asr_result.get('duration', 0)
            result['original_duration'] = original_duration
            
            # 检测停顿段落
            pause_segments = self.pause_detector.detect_pauses_from_asr(asr_result)
            result['pause_segments'] = pause_segments
            
            # 获取有声段落
            speech_segments = self.pause_detector.get_speech_segments(asr_result)
            result['speech_segments'] = speech_segments
            
            # 计算统计信息
            pause_stats = self.pause_detector.calculate_pause_statistics(pause_segments)
            result['pause_statistics'] = pause_stats
            
            # 计算处理的时长
            processed_duration = sum(end - start for start, end in speech_segments)
            removed_duration = original_duration - processed_duration
            result['processed_duration'] = processed_duration
            result['removed_duration'] = removed_duration
            
            # 同时处理音频和视频
            if speech_segments and speech_segments != [(0.0, original_duration)]:
                # 处理音频
                audio_success = self.audio_processor.extract_audio_segments(
                    audio_path, speech_segments, output_audio_path
                )
                
                # 处理视频
                video_success = False
                if video_path and os.path.exists(video_path):
                    video_success = self.video_processor.extract_video_segments(
                        video_path, speech_segments, output_video_path
                    )
                
                if audio_success:
                    result['success'] = True
                    logger.info(f"音视频停顿移除完成，移除 {removed_duration:.2f} 秒停顿")
                    logger.info(f"音频处理: {'成功' if audio_success else '失败'}")
                    logger.info(f"视频处理: {'成功' if video_success else '失败'}")
                else:
                    logger.error("音视频停顿移除失败")
            else:
                result['success'] = True
                logger.info("未检测到需要移除的停顿")
                
        except Exception as e:
            logger.error(f"音视频停顿移除处理失败: {e}")
            
        return result