#!/usr/bin/env python3
"""
精选笔记批量采集功能模块

主要功能：
1. 从飞书表格获取笔记链接
2. 批量调用Coze工作流处理笔记
3. 进度显示和错误处理
"""

import requests
import json
import threading
import time
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime


class FeishuNotesCollector:
    """飞书笔记批量采集器"""

    def __init__(self, config: Dict[str, Any], log_callback=None):
        self.config = config
        self.feishu_config = config.get('feishu', {})
        self.coze_config = config.get('coze', {})
        self.access_token = None
        self.base_url = "https://open.feishu.cn/open-apis"
        self.log_callback = log_callback

    def log_message(self, message: str):
        """记录日志消息"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)  # 如果没有回调，则打印到控制台

    def get_access_token(self) -> str:
        """获取访问令牌"""
        if not self.access_token:
            app_id = self.feishu_config.get('app_id')
            app_secret = self.feishu_config.get('app_secret')

            if not app_id or not app_secret:
                raise ValueError("飞书app_id或app_secret未配置")

            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            data = {
                "app_id": app_id,
                "app_secret": app_secret
            }

            response = requests.post(url, json=data)
            response.raise_for_status()

            result = response.json()
            if result.get('code') == 0:
                self.access_token = result.get('tenant_access_token')
            else:
                raise ValueError(f"获取访问令牌失败: {result.get('msg')}")

        return self.access_token

    def get_feishu_table_data(self, app_token: str, table_id: str, view_id: str = None, rpa_filter: bool = True) -> List[Dict[str, Any]]:
        """
        从飞书表格获取数据

        Args:
            app_token: 飞书应用token
            table_id: 表格ID
            view_id: 视图ID（可选）
            rpa_filter: 是否只采集RPA字段为true的记录

        Returns:
            表格数据列表
        """
        if not app_token:
            raise ValueError("飞书app_token不能为空")

        # 获取访问令牌
        access_token = self.get_access_token()

        if rpa_filter:
            # 使用搜索API，添加RPA字段过滤条件
            base_url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
            url = f"{base_url}/{app_token}/tables/{table_id}/records/search"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # 构建过滤条件：RPA字段为true
            filter_condition = {
                "conjunction": "and",
                "conditions": [
                    {
                        "field_name": "仅采集RPA",
                        "operator": "is",
                        "value": ['true']
                    }
                ]
            }

            payload = {
                "page_size": 100,
                "filter": filter_condition
            }

            try:
                self.log_message(f"NotesCollector搜索请求URL: {url}")
                self.log_message(f"NotesCollector搜索请求体: {payload}")

                response = requests.post(url, headers=headers, json=payload, timeout=30)

                self.log_message(f"NotesCollector搜索响应状态码: {response.status_code}")
                self.log_message(f"NotesCollector搜索响应内容: {response.text}")

                response.raise_for_status()

                data = response.json()
                if data.get("code") == 0:
                    return data.get("data", {}).get("items", [])
                else:
                    raise Exception(f"飞书搜索API错误: {data.get('msg', '未知错误')} (错误码: {data.get('code')})")

            except Exception as e:
                raise Exception(f"搜索飞书表格数据失败: {str(e)}")
        else:
            # 使用普通获取API
            base_url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
            url = f"{base_url}/{app_token}/tables/{table_id}/records"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            params = {}
            if view_id:
                params["view_id"] = view_id

            try:
                self.log_message(f"NotesCollector请求URL: {url}")
                self.log_message(f"NotesCollector请求参数: {params}")

                response = requests.get(url, headers=headers, params=params, timeout=30)

                self.log_message(f"NotesCollector响应状态码: {response.status_code}")
                self.log_message(f"NotesCollector响应内容: {response.text}")

                response.raise_for_status()

                data = response.json()
                if data.get("code") == 0:
                    return data.get("data", {}).get("items", [])
                else:
                    raise Exception(f"飞书API错误: {data.get('msg', '未知错误')} (错误码: {data.get('code')})")

            except Exception as e:
                raise Exception(f"获取飞书表格数据失败: {str(e)}")

    def coze_workflow_request(self, token: str, workflow_id: str, shareText: str) -> Dict[str, Any]:
        """
        发送请求到Coze工作流

        Args:
            token: Coze API token
            workflow_id: 工作流ID
            shareText: 分享文本

        Returns:
            响应结果
        """
        # 固定的API基础URL
        base_url = "https://api.coze.cn/v1/workflow/run"
        # 请求参数
        request_data = {
            "workflow_id": workflow_id,
            "is_async": True,
            "parameters": {
                "shareText": shareText
            }
        }

        # 请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            # 发送POST请求
            response = requests.post(base_url, headers=headers, json=request_data, timeout=30)

            # 打印响应信息
            self.log_message(f"HTTP状态码：{response.status_code}")
            self.log_message(f"原始响应内容：{response.text}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    if "code" in result and result["code"] != 0:
                        self.log_message(f"业务错误码：{result['code']}")
                        self.log_message(f"错误信息：{result.get('msg', '未知错误')}")

                        if result['code'] == 700012006:
                            self.log_message("错误说明：登录验证无效，请检查token是否正确或已过期")
                    else:
                        self.log_message("请求成功！")
                        self.log_message("JSON响应内容：")
                        self.log_message(json.dumps(result, indent=2, ensure_ascii=False))
                        return result
                except json.JSONDecodeError as e:
                    self.log_message(f"JSON解析错误：{e}")
                    self.log_message("响应不是有效的JSON格式")
            else:
                self.log_message(f"HTTP请求失败，状态码：{response.status_code}")
                self.log_message(f"响应内容：{response.text}")

        except requests.exceptions.RequestException as e:
            self.log_message(f"请求发生异常：{e}")

        return None

    def process_notes_batch(self,
                          feishu_app_token: str,
                          feishu_table_id: str,
                          feishu_view_id: str,
                          coze_token: str,
                          coze_workflow_id: str,
                          note_link_field: str = "笔记链接",
                          progress_callback=None) -> Dict[str, Any]:
        """
        批量处理笔记

        Args:
            feishu_app_token: 飞书应用token
            feishu_table_id: 飞书表格ID
            feishu_view_id: 飞书视图ID
            coze_token: Coze API token
            coze_workflow_id: Coze工作流ID
            note_link_field: 笔记链接字段名
            progress_callback: 进度回调函数

        Returns:
            处理结果统计
        """
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': [],
            'start_time': datetime.now(),
            'end_time': None
        }

        try:
            # 1. 获取飞书表格数据（只采集RPA字段为true的记录）
            if progress_callback:
                progress_callback("正在获取飞书表格数据（筛选RPA=true的记录）...", 0)

            table_data = self.get_feishu_table_data(feishu_app_token, feishu_table_id, feishu_view_id, rpa_filter=True)
            results['total'] = len(table_data)

            if not table_data:
                if progress_callback:
                    progress_callback("飞书表格中没有RPA=true的记录", 100)
                return results

            # 2. 提取笔记链接
            note_links = []
            self.log_message(f"开始提取笔记链接，使用字段名: {note_link_field}")

            for i, record in enumerate(table_data):
                fields = record.get('fields', {})
                self.log_message(f"记录 {i+1}: {fields}")

                # 尝试从指定字段获取笔记链接
                note_link = fields.get(note_link_field)

                # 如果指定字段没有，尝试从"分享链接"字段获取
                if not note_link:
                    share_link = fields.get('分享链接')
                    if share_link:
                        # 处理分享链接的不同格式
                        if isinstance(share_link, dict):
                            note_link = share_link.get('link') or share_link.get('text')
                        elif isinstance(share_link, str):
                            note_link = share_link

                if note_link:
                    self.log_message(f"找到笔记链接: {note_link}")
                    note_links.append(note_link)
                else:
                    self.log_message(f"记录 {i+1} 未找到有效的笔记链接")

            self.log_message(f"总共提取到 {len(note_links)} 个笔记链接: {note_links}")

            if not note_links:
                if progress_callback:
                    progress_callback("未找到有效的笔记链接", 100)
                return results

            # 3. 批量处理笔记链接
            self.log_message(f"开始批量处理 {len(note_links)} 个笔记链接...")
            self.log_message(f"Coze Token: {coze_token[:20]}..." if coze_token else "Coze Token: 未设置")
            self.log_message(f"Coze Workflow ID: {coze_workflow_id}")

            for i, note_link in enumerate(note_links):
                try:
                    self.log_message(f"\n=== 处理第 {i+1}/{len(note_links)} 条笔记 ===")
                    self.log_message(f"笔记链接: {note_link}")

                    if progress_callback:
                        progress = int((i + 1) / len(note_links) * 90)
                        progress_callback(f"正在处理第 {i+1}/{len(note_links)} 条笔记（RPA=true）...", progress)

                    # 调用Coze工作流
                    self.log_message("开始调用Coze工作流...")
                    result = self.coze_workflow_request(coze_token, coze_workflow_id, note_link)

                    if result:
                        self.log_message(f"✅ Coze工作流调用成功: {result}")
                        results['success'] += 1
                    else:
                        self.log_message(f"❌ Coze工作流调用失败，返回结果为空")
                        results['failed'] += 1
                        results['errors'].append(f"笔记链接处理失败: {note_link}")

                    # 避免请求过于频繁
                    self.log_message("等待1秒...")
                    time.sleep(1)

                except Exception as e:
                    self.log_message(f"❌ 处理笔记链接时发生异常: {str(e)}")
                    results['failed'] += 1
                    results['errors'].append(f"处理笔记链接时出错: {note_link}, 错误: {str(e)}")
                    import traceback
                    self.log_message(f"异常详情: {traceback.format_exc()}")

            results['end_time'] = datetime.now()

            # 添加处理结果汇总日志
            duration = results['end_time'] - results['start_time']
            self.log_message(f"\n=== 批量处理完成 ===")
            self.log_message(f"总记录数: {results['total']}")
            self.log_message(f"成功处理: {results['success']}")
            self.log_message(f"失败数量: {results['failed']}")
            self.log_message(f"处理耗时: {duration.total_seconds():.1f} 秒")
            if results['errors']:
                self.log_message("错误详情:")
                for error in results['errors']:
                    self.log_message(f"  - {error}")

            if progress_callback:
                progress_callback(f"批量处理完成! 共处理{len(note_links)}条RPA=true的笔记", 100)

        except Exception as e:
            self.log_message(f"❌ 批量处理过程中发生严重错误: {str(e)}")
            import traceback
            self.log_message(f"异常堆栈: {traceback.format_exc()}")
            results['errors'].append(f"批量处理过程中发生错误: {str(e)}")
            results['end_time'] = datetime.now()

            if progress_callback:
                progress_callback(f"处理失败: {str(e)}", 100)

        return results


class NotesCollectionThread(threading.Thread):
    """笔记采集线程"""

    def __init__(self, collector: FeishuNotesCollector, params: Dict[str, Any], callback=None):
        super().__init__()
        self.collector = collector
        self.params = params
        self.callback = callback
        self.results = None
        self.is_running = False

    def run(self):
        self.is_running = True
        try:
            self.results = self.collector.process_notes_batch(
                feishu_app_token=self.params['feishu_app_token'],
                feishu_table_id=self.params['feishu_table_id'],
                feishu_view_id=self.params['feishu_view_id'],
                coze_token=self.params['coze_token'],
                coze_workflow_id=self.params['coze_workflow_id'],
                note_link_field=self.params.get('note_link_field', '笔记链接'),
                progress_callback=self._progress_callback
            )
        except Exception as e:
            self.results = {
                'total': 0,
                'success': 0,
                'failed': 0,
                'errors': [str(e)],
                'start_time': datetime.now(),
                'end_time': datetime.now()
            }
        finally:
            self.is_running = False
            if self.callback:
                self.callback(self.results)

    def _progress_callback(self, message: str, progress: int):
        """进度回调"""
        if self.callback:
            self.callback({
                'type': 'progress',
                'message': message,
                'progress': progress
            })

    def stop(self):
        """停止线程"""
        self.is_running = False