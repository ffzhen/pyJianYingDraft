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
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from workflow.component.flow_python_implementation import VideoEditingWorkflow

class CozeVideoWorkflow:
    """完整的Coze视频工作流"""
    
    def __init__(self, draft_folder_path: str, project_name: str = "coze_video_workflow"):
        """初始化工作流
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            project_name: 项目名称
        """
        self.bearer_token = "cztei_hsNwRnVcJ3V0d5gaKsD3tAO8S8FxxOJZiFKdbjLK1NiCvqn1fMNaGI1c0MhRh7OtA"
        self.workflow_id = "7545326358185525248"
        self.base_url = "https://api.coze.cn/v1/workflow"
        
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        # 初始化视频合成工作流
        self.video_workflow = VideoEditingWorkflow(draft_folder_path, project_name)
        
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
            print("🚀 正在调用Coze工作流API...")
            print(f"📋 工作流ID: {self.workflow_id}")
            print(f"📋 参数: {json.dumps(parameters, ensure_ascii=False, indent=2)}")
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ API调用成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get("code") == 0:
                execute_id = result.get("execute_id")
                debug_url = result.get("debug_url")
                print(f"🔄 任务已创建，执行ID: {execute_id}")
                print(f"🔍 调试URL: {debug_url}")
                return execute_id
            else:
                print(f"❌ API返回错误: {result.get('msg')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API调用失败: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"错误详情: {e.response.text}")
            return None
    
    def poll_workflow_result(self, execute_id: str, max_attempts: int = 60, interval: int = 5) -> Optional[Dict[str, Any]]:
        """轮询工作流结果
        
        Args:
            execute_id: 执行ID
            max_attempts: 最大尝试次数
            interval: 轮询间隔（秒）
            
        Returns:
            工作流结果数据或None
        """
        url = f"{self.base_url}/run_histories/{execute_id}"
        
        print(f"⏳ 开始轮询工作流结果，最大尝试次数: {max_attempts}")
        
        for attempt in range(max_attempts):
            try:
                print(f"🔄 第 {attempt + 1}/{max_attempts} 次尝试...")
                
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                result = response.json()
                print(f"📊 轮询结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get("code") == 0:
                    data_str = result.get("data")
                    if data_str and data_str != "null":
                        try:
                            # 解析内层JSON字符串
                            data = json.loads(data_str)
                            print("✅ 工作流执行完成，获得资源数据")
                            return data
                        except json.JSONDecodeError as e:
                            print(f"❌ 数据解析失败: {e}")
                            print(f"原始数据: {data_str}")
                    else:
                        print("📋 工作流仍在处理中...")
                else:
                    print(f"❌ 轮询出错: {result.get('msg')}")
                
                if attempt < max_attempts - 1:
                    time.sleep(interval)
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ 轮询请求失败: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(interval)
        
        print(f"⏰ 轮询超时（{max_attempts * interval}秒）")
        return None
    
    def synthesize_video(self, coze_result: Dict[str, Any]) -> Optional[str]:
        """使用Coze结果合成视频
        
        Args:
            coze_result: Coze工作流返回的结果数据
            
        Returns:
            视频保存路径或None
        """
        try:
            print("🎬 开始视频合成...")
            print(f"📋 合成参数: {json.dumps(coze_result, ensure_ascii=False, indent=2)}")
            
            # 配置视频合成参数
            video_inputs = {
                # 必需参数
                'audio_url': coze_result.get('audioUrl', ''),
                'title': coze_result.get('title', '美貌对穷人而言真的是灾难吗'),
                'content': coze_result.get('content', ''),
                'video_url': coze_result.get('videoUrl', ''),
                'recordId': coze_result.get('recordId', ''),
                'tableId': coze_result.get('tableId', ''),
                
                # 火山引擎ASR配置
                'volcengine_appid': '6046310832',
                'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',
                
                # 豆包API配置（可选）
                'doubao_token': 'your_doubao_token_here',
                'doubao_model': 'doubao-1-5-pro-32k-250115',
                
                # 可选参数
                'subtitle_delay': 0.0,
                'subtitle_speed': 1.0,
            }
            
            # 执行视频合成
            save_path = self.video_workflow.process_workflow(video_inputs)
            
            print(f"✅ 视频合成完成!")
            print(f"📁 剪映项目已保存到: {save_path}")
            
            return save_path
            
        except Exception as e:
            print(f"❌ 视频合成失败: {e}")
            return None
    
    def run_complete_workflow(self, content: str, digital_no: str, voice_id: str) -> Optional[str]:
        """运行完整工作流
        
        Args:
            content: 内容文本
            digital_no: 数字编号
            voice_id: 语音ID
            
        Returns:
            最终视频保存路径或None
        """
        print("🎯 启动完整Coze视频工作流")
        print("=" * 60)
        
        # 1. 调用Coze工作流
        print("\n📞 步骤1: 调用Coze工作流API...")
        parameters = {
            "content": content,
            "digitalNo": digital_no,
            "voiceId": voice_id
        }
        
        execute_id = self.call_coze_workflow(parameters)
        if not execute_id:
            print("❌ Coze工作流调用失败")
            return None
        
        # 2. 轮询结果
        print("\n⏳ 步骤2: 轮询工作流结果...")
        coze_result = self.poll_workflow_result(execute_id, max_attempts=60, interval=5)
        if not coze_result:
            print("❌ 获取工作流结果失败")
            return None
        
        # 3. 视频合成
        print("\n🎬 步骤3: 开始视频合成...")
        video_path = self.synthesize_video(coze_result)
        if not video_path:
            print("❌ 视频合成失败")
            return None
        
        print(f"\n🎉 完整工作流执行成功!")
        print(f"📁 最终视频项目: {video_path}")
        return video_path


def main():
    """主函数"""
    print("🎯 美貌与贫困主题 - 完整Coze视频工作流")
    print("=" * 60)
    
    # 配置剪映草稿文件夹路径（请根据实际情况修改）
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 工作流参数
    content = "为什么女孩越漂亮越应该好好读书，有个作家说我美貌对于富人来说是锦上添花，对于中产来说是一笔财富，但对于穷人来说就是灾难。"
    digital_no = "D20250820190000004"
    voice_id = "AA20250822120001"
    
    # 创建工作流实例
    workflow = CozeVideoWorkflow(draft_folder_path, "beauty_poverty_complete_workflow")
    
    # 运行完整工作流
    result = workflow.run_complete_workflow(content, digital_no, voice_id)
    
    if result:
        print(f"\n✅ 工作流执行完成: {result}")
    else:
        print(f"\n❌ 工作流执行失败")


if __name__ == "__main__":
    main()