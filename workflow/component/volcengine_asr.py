#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    
    def extract_keywords_with_ai(self, text: str, max_keywords: int = None) -> List[str]:
        """使用AI智能提取关键词，优化用户注意力和留存
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数量（已优化为无限制，保留参数向后兼容）
            
        Returns:
            关键词列表（优化后无数量限制，基于内容质量动态提取）
        """
        print(f"[INFO] 使用AI智能提取关键词（无限制模式）: {text[:50]}...")
        
        try:
            # 检查豆包API配置
            if not self.doubao_token:
                print("⚠️ 未配置豆包API token，使用本地智能算法")
                return self._fallback_keyword_extraction(text, max_keywords)
            
            # 豆包API进行智能关键词提取（用户注意力优化版本）
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
                            "content": "你是一个专业的视频内容优化专家，专注于通过关键词高亮提升用户注意力和视频留存。请从给定文本中智能提取所有有价值的关键词。\n\n核心策略（用户注意力最大化）：\n1. 【数量无限制】提取所有有意义的词汇，不设数量上限\n2. 【高频吸引词优先】重点标记能引起用户情感共鸣的词汇\n3. 【多层次覆盖】同时提取：核心概念词、情感触发词、行动导向词、数字金额词\n4. 【用户痛点词汇】特别关注：钱、赚钱、暴富、财富、收入、投资、机会等\n5. 【情绪激发词汇】包含：震惊、惊人、秘密、内幕、真相、爆料等\n6. 【时间紧迫词汇】如：马上、立即、现在、今年、未来、趋势等\n7. 【权威背书词汇】如：专家、官方、政策、国家、央行等\n\n输出要求：\n- 只返回关键词，用逗号分隔\n- 按重要性排序，优先级：情感触发>核心概念>数量词汇>一般名词\n- 长度2-6个字，优先4字成语和专业术语\n- 确保每个词都能抓住用户眼球\n\n示例：\n输入：'年轻人如何在经济不景气时代实现财富自由，专家建议这三个赚钱机会不容错过'\n输出：财富自由,赚钱机会,经济不景气,年轻人,专家建议,不容错过,实现,财富,机会,赚钱,经济,时代,建议,年轻,自由"
                        },
                        {
                            "role": "user",
                            "content": f"请智能提取以下文本的所有有价值关键词：{text}"
                        }
                    ],
                    "max_tokens": 500,  # 增加token限制以支持更多关键词
                    "temperature": 0.1  # 降低温度提高一致性
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                # 解析关键词（无数量限制）
                keywords = [kw.strip() for kw in content.split(',') if kw.strip() and len(kw.strip()) >= 2]
                
                # 去重但保持顺序
                seen = set()
                unique_keywords = []
                for kw in keywords:
                    if kw not in seen and kw:
                        seen.add(kw)
                        unique_keywords.append(kw)
                
                print(f"[OK] AI智能提取关键词（{len(unique_keywords)}个）: {unique_keywords}")
                return unique_keywords
            else:
                print(f"[ERROR] AI关键词提取失败: {response.status_code}, {response.text}")
                print("[INFO] 使用本地智能算法作为备用")
                return self._fallback_keyword_extraction(text, max_keywords)
                
        except Exception as e:
            print(f"[ERROR] AI关键词提取异常: {e}")
            print("[INFO] 使用本地智能算法作为备用")
            return self._fallback_keyword_extraction(text, max_keywords)
    
    def _fallback_keyword_extraction(self, text: str, max_keywords: int = None) -> List[str]:
        """备用关键词提取方法（智能无限制版本，用户注意力优化）
        
        Args:
            text: 输入文本
            max_keywords: 保留参数以向后兼容（实际不限制数量）
            
        Returns:
            关键词列表（基于内容价值动态提取，无数量限制）
        """
        print("[INFO] 使用备用关键词提取方法（智能无限制版本）")
        
        import re
        from collections import Counter
        
        # 移除标点符号，只保留中文和英文
        cleaned_text = re.sub(r'[^\u4e00-\u9fff\w\s]', '', text)
        
        # 大幅扩展的高价值词汇模式（用户注意力优化）
        high_value_patterns = [
            # 财富相关（用户痛点）- 最高优先级
            r'(千万富翁|财富自由|暴富|赚钱|投资理财|经济条件|收入|金钱|资产|理财|投资|股票|房产|创业|商机)',
            
            # 情感触发词（吸引注意力）
            r'(震惊|惊人|秘密|内幕|真相|爆料|揭秘|独家|首次|史上|空前|绝无仅有|前所未有|重磅|突破性)',
            
            # 时间紧迫性（制造焦虑感）
            r'(马上|立即|现在|今年|明年|未来|即将|正在|快速|迅速|急需|紧急|限时|倒计时|最后机会)',
            
            # 权威背书（增加可信度）
            r'(专家|权威|官方|政府|国家|央行|政策|法律|规定|研究|报告|数据|调查|统计|科学|学者)',
            
            # 行业热点（抓住趋势）
            r'(人工智能|科技发展|互联网|大数据|区块链|新能源|房地产|教育|医疗|养老|消费升级)',
            
            # 社会热点（引起共鸣）
            r'(年轻人|中年人|老年人|上班族|学生|家长|城市|农村|社会|民生|就业|教育|医疗|养老)',
            
            # 数字金额（具体化）
            r'(一千万|千万|百万|十万|万元|元|亿|千亿|万亿|倍|百分|折扣|优惠|免费|补贴|奖励)',
            
            # 动作导向词（引导行为）
            r'(学会|掌握|获得|实现|达到|提升|改善|优化|解决|克服|避免|防范|抓住|把握|选择)',
            
            # 对比强调（突出重要性）
            r'(最好|最佳|最优|顶级|一流|高端|低端|普通|平均|标准|特殊|独特|唯一|稀有|珍贵)',
            
            # 问题痛点（引起共鸣）
            r'(问题|困难|挑战|危机|风险|陷阱|误区|盲区|漏洞|缺陷|不足|缺点|弊端|隐患)',
            
            # 解决方案（提供价值）
            r'(方法|技巧|秘诀|策略|方案|建议|指导|教程|攻略|宝典|手册|指南|经验|心得)',
            
            # 4字成语和固定搭配
            r'(拆迁改造|货币化安置|城中村|老旧小区|多拆少建|拆小建大|改善型|舒适型|住房结构|内需|经济|时代红利)',
            
            # 3字重要词汇
            r'(拆迁户|补偿款|库存|供应|品质|升级|刚需|规划|致富|守住|财富|暴富|转眼|归零|政策|方向)',
            
            # 通用2字词汇
            r'(拆迁|改造|安置|补偿|现金|发放|获得|成为|关键|重要|变化|不同|严控|推动|激活|带动|理性|把握)'
        ]
        
        candidate_words = []
        
        # 使用高价值模式提取（按优先级）
        for pattern in high_value_patterns:
            matches = re.findall(pattern, cleaned_text)
            candidate_words.extend(matches)
        
        # 补充通用中文词汇（2-6字）
        general_words = re.findall(r'[\u4e00-\u9fff]{2,6}', cleaned_text)
        candidate_words.extend(general_words)
        
        # 大幅缩减停用词列表，更多词汇参与高亮
        stop_words = {
            # 只过滤最基础的无意义词汇
            '这个', '那个', '这样', '那样', '因为', '所以', '但是', '然后', '如果', 
            '的话', '就是', '还是', '不过', '虽然', '一些', '一个', '什么', '怎么', 
            '为什么', '哪里', '时候', '现在', '以前', '以后'
        }
        
        # 过滤处理
        filtered_words = []
        for word in candidate_words:
            if (word not in stop_words and 
                len(word) >= 2 and 
                not re.match(r'^[\u4e00-\u9fff]{1}[的了着过在]$', word)):  # 过滤助词结尾
                filtered_words.append(word)
        
        # 统计词频，优先长词和高频词
        word_freq = Counter(filtered_words)
        
        # 按重要性排序：词频 × 长度权重
        sorted_words = sorted(word_freq.items(), 
                            key=lambda x: (x[1] * (1 + len(x[0]) * 0.2)), 
                            reverse=True)
        
        # 预定义的超高价值关键词（必须高亮）
        must_highlight_keywords = [
            # 财富相关
            '千万富翁', '财富自由', '拆迁暴富', '补偿款', '数百万元', '上千万元',
            # 政策变化
            '货币化安置', '城中村', '老旧小区', '多拆少建', '拆小建大',
            # 投资理财
            '稳健配置', '改善住房', '盲目消费', '投机',
            # 时间敏感
            '二零二五年', '三十个城市', '三百个', '一夜暴富', '转眼归零',
            # 重要概念
            '拆迁改造', '全面推进', '重新提倡', '时代红利', '政策方向'
        ]
        
        # 构建最终关键词列表
        final_keywords = []
        
        # 第一优先级：必须高亮的超高价值词
        for must_word in must_highlight_keywords:
            if must_word in text and must_word not in final_keywords:
                final_keywords.append(must_word)
        
        # 第二优先级：从频率统计中选择
        for word, freq in sorted_words:
            if word not in final_keywords:
                # 检查重复但允许更多变体
                is_duplicate = False
                for existing in final_keywords:
                    if (len(word) <= 2 and len(existing) <= 2 and 
                        (word == existing or word in existing or existing in word)):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    final_keywords.append(word)
        
        # 按文本出现顺序重新排列（保持阅读自然性）
        text_order_keywords = []
        for word in final_keywords:
            if word in text:
                pos = text.find(word)
                text_order_keywords.append((pos, word))
        
        # 排序并提取词汇
        text_order_keywords.sort(key=lambda x: x[0])
        final_ordered_keywords = [word for pos, word in text_order_keywords]
        
        print(f"[INFO] 智能无限制提取关键词（{len(final_ordered_keywords)}个）: {final_ordered_keywords}")
        return final_ordered_keywords


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
