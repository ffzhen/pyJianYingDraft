#!/usr/bin/env python3
"""
完整工作流：Coze API调用 + 结果轮询 + 视频合成

1. 调用Coze工作流API生成资源
2. 轮询获取生成的音频、视频等资源
3. 使用本地视频合成方法生成最终视频
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from workflow.component.flow_python_implementation import VideoEditingWorkflow

def log_with_time(message: str, start_time: datetime = None):
    """带时间戳的日志输出
    
    Args:
        message: 日志消息
        start_time: 开始时间，用于计算运行时间
    """
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    if start_time:
        elapsed = (current_time - start_time).total_seconds()
        time_info = f"[{timestamp}] [已运行: {elapsed:.1f}s]"
    else:
        time_info = f"[{timestamp}]"
    
    print(f"{time_info} {message}")

class CozeVideoWorkflow:
    """完整的Coze视频工作流"""
    
    def __init__(self, draft_folder_path: str, project_name: str = None):
        """初始化工作流
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            project_name: 项目名称（可选，如果不提供将使用title+时间戳生成）
        """
        self.bearer_token = "pat_n4y1hGj8jOusHQ8jHm1CPkPNBpP96jHGGoz8DhYQcJbkK9Q7JNjMGxOi4xuCof1T"
        self.workflow_id = "7545326358185525248"
        self.base_url = "https://api.coze.cn/v1/workflow"
        
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        # 保存参数
        self.draft_folder_path = draft_folder_path
        self.base_project_name = project_name
        self.video_workflow = None  # 稍后初始化
        
        # 记录开始时间
        self.start_time = datetime.now()
        
        # 背景音乐配置
        self.background_music_path = None
        self.background_music_volume = 0.3
        
        # 豆包API配置
        self.doubao_token = 'adac0afb-5fd4-4c66-badb-370a7ff42df5'
        self.doubao_model = 'ep-m-20250902010446-mlwmf'
    
    def set_background_music(self, music_path: str, volume: float = 0.3):
        """设置背景音乐
        
        Args:
            music_path: 背景音乐文件路径
            volume: 音量 (0-1)
        """
        if not os.path.exists(music_path):
            raise ValueError(f"背景音乐文件不存在: {music_path}")
        
        self.background_music_path = music_path
        self.background_music_volume = volume
        log_with_time(f"🎵 背景音乐已设置: {os.path.basename(music_path)}，音量: {volume}", self.start_time)
    
    def set_doubao_api(self, token: str, model: str):
        """设置豆包API配置
        
        Args:
            token: 豆包API token
            model: 豆包模型接入点
        """
        self.doubao_token = token
        self.doubao_model = model
        log_with_time(f"🤖 豆包API已设置: 模型={model}", self.start_time)
    
    def generate_project_name(self, title: str = None) -> str:
        """生成项目名称
        
        Args:
            title: 视频标题
            
        Returns:
            项目名称
        """
        if self.base_project_name:
            # 如果指定了基础项目名称，使用它加时间戳
            base_name = self.base_project_name
        elif title:
            # 使用标题作为基础名称，清理特殊字符
            import re
            base_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', title)[:20]  # 限制长度并清理特殊字符
        else:
            # 默认名称
            base_name = "coze_video_workflow"
        
        # 添加时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"{base_name}_{timestamp}"
        
        log_with_time(f"Project name generated: {project_name} - 生成项目名称", self.start_time)
        return project_name
        
    def call_coze_workflow(self, parameters: Dict[str, Any]) -> Optional[str]:
        """调用Coze工作流API
        
        Args:
            parameters: 工作流参数
            
        Returns:
            execute_id or None
        """
        url = f"{self.base_url}/run"
        
        payload = {
            "workflow_id": self.workflow_id,
            "parameters": parameters,
            "is_async": True
        }
        
        try:
            log_with_time("🚀 正在调用Coze工作流API...", self.start_time)
            log_with_time(f"📋 工作流ID: {self.workflow_id}", self.start_time)
            log_with_time(f"📋 参数: {json.dumps(parameters, ensure_ascii=False, indent=2)}", self.start_time)
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            log_with_time(f"✅ API调用成功: {json.dumps(result, ensure_ascii=False, indent=2)}", self.start_time)
            
            if result.get("code") == 0:
                execute_id = result.get("execute_id")
                debug_url = result.get("debug_url")
                log_with_time(f"🔄 任务已创建，执行ID: {execute_id}", self.start_time)
                log_with_time(f"🔍 调试URL: {debug_url}", self.start_time)
                return execute_id
            else:
                log_with_time(f"❌ API返回错误: {result.get('msg')}", self.start_time)
                return None
                
        except requests.exceptions.RequestException as e:
            log_with_time(f"❌ API调用失败: {e}", self.start_time)
            if hasattr(e, 'response') and e.response:
                log_with_time(f"错误详情: {e.response.text}", self.start_time)
            return None
    
    def poll_workflow_result(self, execute_id: str, max_attempts: int = 20, interval: int = 60) -> Optional[Dict[str, Any]]:
        """轮询工作流结果
        
        Args:
            execute_id: 执行ID
            max_attempts: 最大尝试次数（默认20次，总计20分钟）
            interval: 轮询间隔（默认60秒，即每分钟一次）
            
        Returns:
            工作流结果数据或None
        """
        url = f"https://api.coze.cn/v1/workflows/{self.workflow_id}/run_histories/{execute_id}"
        
        log_with_time(f"⏳ 开始轮询工作流结果，最大尝试次数: {max_attempts}，间隔: {interval}秒（总计: {max_attempts * interval}秒）", self.start_time)
        
        for attempt in range(max_attempts):
            try:
                log_with_time(f"🔄 第 {attempt + 1}/{max_attempts} 次尝试...", self.start_time)
                
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                result = response.json()
                log_with_time(f"📊 轮询结果: {json.dumps(result, ensure_ascii=False, indent=2)}", self.start_time)
                
                if result.get("code") == 0:
                    data_array = result.get("data")
                    if data_array and isinstance(data_array, list) and len(data_array) > 0:
                        # 获取最新的执行记录
                        execution_record = data_array[0]
                        execute_status = execution_record.get("execute_status")
                        
                        log_with_time(f"📋 执行状态: {execute_status}", self.start_time)
                        
                        if execute_status == "Success":
                            # 解析输出数据
                            output_str = execution_record.get("output")
                            if output_str:
                                try:
                                    output_data = json.loads(output_str)
                                    log_with_time("✅ 工作流执行完成，获得资源数据", self.start_time)
                                    return output_data
                                except json.JSONDecodeError as e:
                                    log_with_time(f"❌ 输出数据解析失败: {e}", self.start_time)
                                    log_with_time(f"原始输出: {output_str}", self.start_time)
                            else:
                                log_with_time("⚠️  工作流完成但无输出数据", self.start_time)
                                return execution_record
                        elif execute_status == "Failed":
                            error_code = execution_record.get("error_code", "未知错误")
                            log_with_time(f"❌ 工作流执行失败: {error_code}", self.start_time)
                            return None
                        elif execute_status == "Running":
                            log_with_time("📋 工作流仍在运行中...", self.start_time)
                        else:
                            log_with_time(f"📋 工作流状态: {execute_status}", self.start_time)
                    else:
                        log_with_time("📋 暂无执行记录...", self.start_time)
                else:
                    log_with_time(f"❌ 轮询出错: {result.get('msg')}", self.start_time)
                
                if attempt < max_attempts - 1:
                    time.sleep(interval)
                    
            except requests.exceptions.RequestException as e:
                log_with_time(f"❌ 轮询请求失败: {e}", self.start_time)
                if attempt < max_attempts - 1:
                    time.sleep(interval)
        
        log_with_time(f"⏰ 轮询超时（{max_attempts * interval}秒）", self.start_time)
        return None
    
    def synthesize_video(self, coze_result: Dict[str, Any]) -> Optional[str]:
        """使用Coze结果合成视频
        
        Args:
            coze_result: Coze工作流返回的结果数据
            
        Returns:
            视频保存路径或None
        """
        try:
            log_with_time("🎬 开始视频合成...", self.start_time)
            log_with_time(f"📋 合成参数: {json.dumps(coze_result, ensure_ascii=False, indent=2)}", self.start_time)
            
            # 解析嵌套的Output数据
            actual_data = coze_result
            if 'Output' in coze_result:
                try:
                    output_str = coze_result['Output']
                    actual_data = json.loads(output_str)
                    log_with_time(f"📋 解析后的数据: {json.dumps(actual_data, ensure_ascii=False, indent=2)}", self.start_time)
                except json.JSONDecodeError as e:
                    log_with_time(f"⚠️  Output解析失败，使用原始数据: {e}", self.start_time)
                    actual_data = coze_result
            
            # 使用任务配置中的标题，而不是Coze返回的标题
            title = self.task_config.get('title', 'AI视频生成')
            project_name = self.generate_project_name(title)
            
            # 初始化视频工作流（使用动态生成的项目名称）
            if not self.video_workflow:
                self.video_workflow = VideoEditingWorkflow(self.draft_folder_path, project_name)
                log_with_time(f"🛠️  视频工作流已初始化: {project_name}", self.start_time)
            
            # 配置视频合成参数
            video_inputs = {
                # 必需参数
                'audio_url': actual_data.get('audioUrl', ''),
                'title': title,  # 使用任务配置中的标题
                'content': actual_data.get('content', ''),
                'digital_video_url': actual_data.get('videoUrl', ''),  # 修正参数名映射
                'recordId': actual_data.get('recordId', ''),
                'tableId': actual_data.get('tableId', ''),
                
                # 火山引擎ASR配置
                'volcengine_appid': '6046310832',
                'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',
                
                # 豆包API配置（可选）- 如未配置将使用本地关键词提取算法
                'doubao_token': self.doubao_token,  # 豆包API token
                'doubao_model': self.doubao_model,  # 豆包模型接入点
                
                # 可选参数
                'subtitle_delay': 0.0,
                'subtitle_speed': 1.0,
                
                # 背景音乐配置（如果已设置）
                'background_music_path': self.background_music_path,
                'background_music_volume': self.background_music_volume,
            }
            
            # 执行视频合成
            save_path = self.video_workflow.process_workflow(video_inputs)
            
            log_with_time(f"✅ 视频合成完成!", self.start_time)
            log_with_time(f"📁 剪映项目已保存到: {save_path}", self.start_time)
            
            return save_path
            
        except Exception as e:
            log_with_time(f"❌ 视频合成失败: {e}", self.start_time)
            return None
    
    def run_complete_workflow(self, content: str, digital_no: str, voice_id: str, title: str = None) -> Optional[str]:
        """运行完整工作流
        
        Args:
            content: 内容文本
            digital_no: 数字编号
            voice_id: 语音ID
            title: 视频标题（可选，如果不提供将使用默认标题）
            
        Returns:
            最终视频保存路径或None
        """
        log_with_time("🎯 启动完整Coze视频工作流", self.start_time)
        log_with_time("=" * 60, self.start_time)
        
        # 1. 调用Coze工作流
        log_with_time("\n📞 步骤1: 调用Coze工作流API...", self.start_time)
        parameters = {
            "content": content,
            "digitalNo": digital_no,
            "voiceId": voice_id,
            "title": title or "AI视频生成"  # 添加title参数
        }
        
        execute_id = self.call_coze_workflow(parameters)
        if not execute_id:
            log_with_time("❌ Coze工作流调用失败", self.start_time)
            return None
        
        # 2. 轮询结果
        log_with_time("\n⏳ 步骤2: 轮询工作流结果...", self.start_time)
        coze_result = self.poll_workflow_result(execute_id, max_attempts=20, interval=60)
        if not coze_result:
            log_with_time("❌ 获取工作流结果失败", self.start_time)
            return None
        
        # 3. 视频合成
        log_with_time("\n🎬 步骤3: 开始视频合成...", self.start_time)
        video_path = self.synthesize_video(coze_result)
        if not video_path:
            log_with_time("❌ 视频合成失败", self.start_time)
            return None
        
        log_with_time(f"\n🎉 完整工作流执行成功!", self.start_time)
        log_with_time(f"📁 最终视频项目: {video_path}", self.start_time)
        return video_path


def main():
    """主函数"""
    start_time = datetime.now()
    log_with_time("🎯 美貌与贫困主题 - 完整Coze视频工作流", start_time)
    log_with_time("=" * 60, start_time)
    
    # 配置剪映草稿文件夹路径（请根据实际情况修改）
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 工作流参数
    content = "未来中国有可能出现九大现象。第一个，手机有可能会消失，燃油车可能会被淘汰，人民币已逐渐数字化。第四，孩子国家统一给一套房。第五，全民医疗免费。第六，房子太便宜没人要。第七，将来飞行汽车将会越来越多，不会为堵车而发愁。第八，高科技替代劳动力。第九，人均寿命可以达到100岁以上。你觉得哪个会成为现实呢？"
    digital_no = "D20250820190000004"
    voice_id = "AA20250822120001"
    title = "未来中国可能出现的九大变化"  # 添加title参数
    
    # 创建工作流实例（项目名称将根据标题动态生成）
    workflow = CozeVideoWorkflow(draft_folder_path)
    
    # 在最外层传入豆包API配置
    workflow.set_doubao_api(
        token='adac0afb-5fd4-4c66-badb-370a7ff42df5',
        model='ep-m-20250902010446-mlwmf'
    )
    
    # 设置背景音乐（可选）
    background_music_path = os.path.join(os.path.dirname(__file__), '..', '..', '华尔兹.mp3')
    if os.path.exists(background_music_path):
        workflow.set_background_music(background_music_path, volume=0.3)
        log_with_time(f"✅ 背景音乐已加载: {background_music_path}", start_time)
    else:
        log_with_time(f"⚠️  背景音乐文件未找到: {background_music_path}", start_time)
        log_with_time("💡 如需添加背景音乐，请将华尔兹.mp3文件放置在项目根目录下", start_time)
    
    # 运行完整工作流
    result = workflow.run_complete_workflow(content, digital_no, voice_id, title)
    
    if result:
        print(f"\n✅ 工作流执行完成: {result}")
    else:
        print(f"\n❌ 工作流执行失败")


if __name__ == "__main__":
    main()