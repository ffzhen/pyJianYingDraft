#!/usr/bin/env python3
"""
火山引擎语音识别集成
使用火山引擎ASR接口替代Whisper进行音频转录
"""

import time
import requests
import json
from typing import Dict, Any, List, Optional


class VolcengineASR:
    """火山引擎语音识别客户端"""
    
    def __init__(self, appid: str, access_token: str, doubao_token: str = None, doubao_model: str = "doubao-1-5-pro-32k-250115"):
        """初始化火山引擎ASR客户端
        
        Args:
            appid: 火山引擎ASR应用ID
            access_token: 火山引擎ASR访问令牌
            doubao_token: 豆包API访问令牌（用于关键词提取）
            doubao_model: 豆包模型名称，默认为doubao-1-5-pro-32k-250115
        """
        # 火山引擎ASR配置
        self.base_url = 'https://openspeech.bytedance.com/api/v1/vc'
        self.appid = appid
        self.access_token = access_token
        
        # 豆包API配置（用于关键词提取）
        self.doubao_token = doubao_token
        self.doubao_model = doubao_model
        
    def submit_audio_file(self, file_url: str, language: str = 'zh-CN') -> Optional[str]:
        """提交音频文件进行识别
        
        Args:
            file_url: 音频文件URL
            language: 语言代码，默认中文
            
        Returns:
            任务ID，失败返回None
        """
        print(f"[INFO] 提交音频文件进行识别: {file_url}")
        
        try:
            response = requests.post(
                f'{self.base_url}/submit',
                params={
                    'appid': self.appid,
                    'language': language,
                    'use_itn': 'True',           # 启用逆文本标准化
                    'use_capitalize': 'True',    # 启用首字母大写
                    'max_lines': 1,              # 每行最多1句
                    'words_per_line': 10,        # 每行最多15词
                },
                json={
                    'url': file_url,
                },
                headers={
                    'content-type': 'application/json',
                    'Authorization': f'Bearer; {self.access_token}'
                }
            )
            
            print(f"[INFO] 提交响应: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('message') == 'Success':
                    job_id = result.get('id')
                    print(f"[OK] 任务提交成功，任务ID: {job_id}")
                    return job_id
                else:
                    print(f"[ERROR] 任务提交失败: {result}")
                    return None
            else:
                print(f"[ERROR] HTTP错误: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 提交音频文件异常: {e}")
            return None
    
    def query_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """查询识别结果
        
        Args:
            job_id: 任务ID
            
        Returns:
            识别结果，失败返回None
        """
        try:
            response = requests.get(
                f'{self.base_url}/query',
                params={
                    'appid': self.appid,
                    'id': job_id,
                },
                headers={
                    'Authorization': f'Bearer; {self.access_token}'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"[INFO] 查询响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return result
            else:
                print(f"[ERROR] 查询HTTP错误: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 查询结果异常: {e}")
            return None
    
    def wait_for_completion(self, job_id: str, max_wait_time: int = 300) -> Optional[Dict[str, Any]]:
        """等待识别完成
        
        Args:
            job_id: 任务ID
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            最终识别结果，失败返回None
        """
        print(f"[INFO] 等待识别完成，最大等待时间: {max_wait_time}秒")
        
        start_time = time.time()
        wait_interval = 5  # 每5秒查询一次
        
        while time.time() - start_time < max_wait_time:
            result = self.query_result(job_id)
            
            if result is None:
                print("[ERROR] 查询失败")
                return None
            
            # 检查是否有utterances数据，如果有就表示成功
            utterances = result.get('utterances', [])
            code = result.get('code', -1)
            message = result.get('message', '')
            
            print(f"[INFO] 当前状态码: {code}, 消息: {message}")
            
            if code == 0 and utterances:
                print("[OK] 识别完成!")
                return result
            elif code != 0:
                print(f"[ERROR] 识别失败! 错误码: {code}, 消息: {message}")
                return None
            else:
                print(f"[INFO] 识别进行中，等待{wait_interval}秒后重试...")
                time.sleep(wait_interval)
        
        print("[ERROR] 等待超时")
        return None
    
    def process_audio_file(self, file_url: str, language: str = 'zh-CN') -> List[Dict[str, Any]]:
        """完整处理音频文件，返回字幕格式数据
        
        Args:
            file_url: 音频文件URL
            language: 语言代码
            
        Returns:
            字幕对象数组
        """
        print(f"🎯 开始火山引擎语音识别: {file_url}")
        
        # 1. 提交任务
        job_id = self.submit_audio_file(file_url, language)
        if not job_id:
            return []
        
        # 2. 等待完成
        result = self.wait_for_completion(job_id)
        if not result:
            return []
        
        # 3. 解析结果
        subtitles = self.parse_result_to_subtitles(result)
        print(f"[OK] 火山引擎识别完成，生成 {len(subtitles)} 段字幕")
        
        return subtitles
    
    def transcribe_audio_for_silence_detection(self, file_url: str, language: str = 'zh-CN') -> Optional[Dict[str, Any]]:
        """转录音频用于停顿检测（返回原始ASR结果）
        
        Args:
            file_url: 音频文件URL
            language: 语言代码，默认中文
            
        Returns:
            原始ASR结果，失败返回None
        """
        print(f"[INFO] 转录音频用于停顿检测: {file_url}")
        
        try:
            # 提交音频文件
            job_id = self.submit_audio_file(file_url, language)
            if not job_id:
                return None
            
            # 等待识别完成
            result = self.wait_for_completion(job_id)
            if not result:
                return None
            
            # 检查识别结果
            if result.get('code') != 0:
                print(f"[ERROR] 识别失败: {result.get('message', '未知错误')}")
                return None
            
            utterances = result.get('utterances', [])
            if not utterances:
                print("⚠️ 未识别到语音内容")
                return None
            
            print(f"[OK] 音频转录完成，识别到 {len(utterances)} 个语音片段")
            return result
            
        except Exception as e:
            print(f"[ERROR] 音频转录失败: {e}")
            return None
    
    def parse_result_to_subtitles(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析火山引擎结果为字幕格式
        
        Args:
            result: 火山引擎识别结果
            
        Returns:
            字幕对象数组
        """
        subtitles = []
        
        try:
            # 获取识别数据 - 根据API文档，utterances在根层级
            utterances = result.get('utterances', [])
            
            if not utterances:
                print("⚠️ 未找到识别结果")
                return []
            
            print(f"[INFO] 解析 {len(utterances)} 个语音片段")
            
            for i, utterance in enumerate(utterances):
                text = utterance.get('text', '').strip()
                start_time = utterance.get('start_time', 0) / 1000.0  # 转换为秒
                end_time = utterance.get('end_time', 0) / 1000.0      # 转换为秒
                
                if text:
                    # 清理文本（移除标点符号）
                    clean_text = self.clean_text(text)
                    
                    subtitle = {
                        'text': clean_text,
                        'start': start_time,
                        'end': end_time
                    }
                    subtitles.append(subtitle)
                    
                    duration = end_time - start_time
                    print(f"   第{i+1}段: [{start_time:.3f}s-{end_time:.3f}s] ({duration:.1f}s) {clean_text}")
            
            return subtitles
            
        except Exception as e:
            print(f"[ERROR] 解析结果异常: {e}")
            return []
    
    def clean_text(self, text: str) -> str:
        """清理文本，移除标点符号"""
        import re
        
        # 移除标点符号，保留中文、英文、数字
        cleaned = re.sub(r'[^\u4e00-\u9fff\w\s]', '', text)
        
        # 移除多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def extract_keywords_with_ai(self, text: str, max_keywords: int = 10) -> List[str]:
        """使用AI提取关键词
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        print(f"[INFO] 使用AI提取关键词: {text[:50]}...")
        
        try:
            # 检查豆包API配置
            if not self.doubao_token:
                print("⚠️ 未配置豆包API token，使用本地算法")
                return self._fallback_keyword_extraction(text, max_keywords)
            
            # 豆包API进行关键词提取
            response = requests.post(
                'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.doubao_token}'  # 使用豆包token
                },
                json={
                    "model": self.doubao_model,  # 使用豆包模型名称
                    "messages": [
                        {
                            "role": "system",
                            "content": f"你是一个专业的关键词提取专家。请从给定的文本中提取最重要的{max_keywords}个关键词，用于视频字幕高亮显示。\n\n要求：\n1. 提取有意义的词汇，如名词、动词、形容词\n2. 避免提取助词、介词、连词等功能词\n3. 避免提取不完整的词组片段\n4. 关键词长度在2-4个字之间\n5. 优先提取核心概念和重要动作\n6. 只返回关键词列表，用逗号分隔，不要其他说明文字\n\n示例：\n输入：'年轻人要学会享受生活，在经济条件允许的情况下适当吃喝玩乐'\n输出：年轻,享受,生活,经济条件,吃喝玩乐"
                        },
                        {
                            "role": "user",
                            "content": f"请从以下文本中提取关键词：{text}"
                        }
                    ],
                    "max_tokens": 200,
                    "temperature": 0.3
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # 解析关键词
                keywords = [kw.strip() for kw in content.split(',') if kw.strip()]
                keywords = keywords[:max_keywords]  # 限制数量
                
                print(f"[OK] AI提取关键词: {keywords}")
                return keywords
            else:
                print(f"[ERROR] AI关键词提取失败: {response.status_code}, {response.text}")
                print("[INFO] 使用本地智能算法作为备用")
                return self._fallback_keyword_extraction(text, max_keywords)
                
        except Exception as e:
            print(f"[ERROR] AI关键词提取异常: {e}")
            print("[INFO] 使用本地智能算法作为备用")
            return self._fallback_keyword_extraction(text, max_keywords)
    
    def _fallback_keyword_extraction(self, text: str, max_keywords: int = 10) -> List[str]:
        """备用关键词提取方法（改进的词频统计 + 规则过滤）
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        print("[INFO] 使用备用关键词提取方法（智能词频统计）")
        
        import re
        from collections import Counter
        
        # 移除标点符号，只保留中文和英文
        cleaned_text = re.sub(r'[^\u4e00-\u9fff\w\s]', '', text)
        
        # 预定义的常见有意义词汇模式
        meaningful_patterns = [
            # 4字词汇（完整概念）
            r'(经济条件|享受生活|吃喝玩乐|科技发展|人工智能|工作方式|社会进步|无限可能)',
            # 3字词汇
            r'(年轻人|改变|发展|进步|未来|触动|退休|消费|领域|应用|生活|变化)',
            # 2字词汇
            r'(年轻|享受|科技|智能|工作|社会|可能|触动|退休|消费|领域|应用|生活|变化|发展|进步|未来)'
        ]
        
        candidate_words = []
        
        # 首先使用预定义模式提取
        for pattern in meaningful_patterns:
            matches = re.findall(pattern, cleaned_text)
            candidate_words.extend(matches)
        
        # 然后使用通用模式补充
        # 优先提取较长的连续中文词汇
        general_words = re.findall(r'[\u4e00-\u9fff]{2,4}', cleaned_text)
        candidate_words.extend(general_words)
        
        # 扩展停用词列表，过滤无意义词汇
        stop_words = {
            # 代词
            '我们', '这个', '那个', '他们', '她们', '它们', '自己', '大家',
            # 副词和连词
            '可以', '应该', '非常', '比较', '还是', '就是', '这样', '那样', '因为', '所以', '但是', '然后', '如果',
            # 介词和助词
            '在于', '关于', '对于', '由于', '通过', '根据', '按照', '为了', '来说', '而且', '不过', '虽然',
            # 时间词（常见但不太重要）
            '时候', '现在', '以前', '以后', '今天', '明天', '昨天', '刚才', '马上', '立即',
            # 程度词
            '特别', '尤其', '更加', '最后', '首先', '其次', '另外', '同时',
            # 其他常见但无意义的词
            '一些', '一个', '这些', '那些', '什么', '怎么', '为什么', '哪里'
        }
        
        # 过滤停用词和过短词汇
        filtered_words = []
        for word in candidate_words:
            if (word not in stop_words and 
                len(word) >= 2 and 
                not re.match(r'^[\u4e00-\u9fff]{1}[的了着过]$', word) and  # 过滤如"做的"、"说了"等
                not re.match(r'^[一二三四五六七八九十]+$', word)):  # 过滤纯数字
                filtered_words.append(word)
        
        # 统计词频，优先选择较长的词汇
        word_freq = Counter(filtered_words)
        
        # 按词频和长度排序（长度越长权重越高）
        sorted_words = sorted(word_freq.items(), 
                            key=lambda x: (x[1], len(x[0])), 
                            reverse=True)
        
        # 预定义的高质量关键词（优先级最高）
        priority_keywords = [
            '经济条件', '享受生活', '吃喝玩乐', '科技发展', '人工智能', '工作方式', '社会进步',
            '年轻', '触动', '退休', '消费', '改变', '发展', '进步', '未来', '科技', '智能',
            '享受', '生活', '领域', '应用', '变化'
        ]
        
        # 先提取预定义的高质量关键词
        final_keywords = []
        for priority_word in priority_keywords:
            if priority_word in text and priority_word not in final_keywords:
                final_keywords.append(priority_word)
                if len(final_keywords) >= max_keywords:
                    break
        
        # 如果还需要更多关键词，从频率统计中补充
        if len(final_keywords) < max_keywords:
            for word, freq in sorted_words:
                if word not in final_keywords:
                    # 检查是否与已选择的关键词重复
                    is_duplicate = False
                    for existing in final_keywords:
                        if (word in existing or existing in word) and word != existing:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        final_keywords.append(word)
                    
                    if len(final_keywords) >= max_keywords:
                        break
        
        print(f"[INFO] 备用方法提取关键词: {final_keywords}")
        return final_keywords


def test_volcengine_asr():
    """测试火山引擎ASR功能"""
    
    print("🧪 火山引擎ASR测试")
    print("=" * 50)
    
    # 使用您提供的凭据
    appid = "6046310832"
    access_token = "fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY"
    
    # 创建ASR客户端
    asr = VolcengineASR(appid, access_token)
    
    # 测试音频文件URL（您需要提供一个可访问的音频URL）
    file_url = "https://oss.oemi.jdword.com/prod/temp/srt/V20250901152556001.wav"
    
    print(f"[INFO] 测试音频: {file_url}")
    print("[INFO] 预期结果: 生成精确的字幕时间戳")
    
    try:
        # 处理音频文件
        subtitles = asr.process_audio_file(file_url)
        
        if subtitles:
            print(f"\n[OK] 识别成功! 生成 {len(subtitles)} 段字幕")
            print("\n📋 字幕内容:")
            print("-" * 40)
            
            for i, subtitle in enumerate(subtitles, 1):
                duration = subtitle['end'] - subtitle['start']
                print(f"{i:2d}. [{subtitle['start']:6.3f}s-{subtitle['end']:6.3f}s] ({duration:4.1f}s) {subtitle['text']}")
            
            # 生成SRT文件
            srt_content = generate_srt(subtitles)
            
            output_path = "volcengine_test_result.srt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            print(f"\n📁 SRT文件已保存: {output_path}")
            
        else:
            print("[ERROR] 识别失败")
            
    except Exception as e:
        print(f"[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()


def generate_srt(subtitles: List[Dict[str, Any]]) -> str:
    """生成SRT格式内容"""
    srt_content = []
    
    for i, subtitle in enumerate(subtitles, 1):
        start_time = subtitle['start']
        end_time = subtitle['end']
        text = subtitle['text']
        
        # 转换为SRT时间格式
        start_srt = seconds_to_srt_time(start_time)
        end_srt = seconds_to_srt_time(end_time)
        
        srt_content.append(f"{i}")
        srt_content.append(f"{start_srt} --> {end_srt}")
        srt_content.append(text)
        srt_content.append("")
    
    return "\n".join(srt_content)


def seconds_to_srt_time(seconds: float) -> str:
    """将秒数转换为SRT时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


if __name__ == "__main__":
    test_volcengine_asr()
