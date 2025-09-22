#!/usr/bin/env python3
"""
文案批量二创功能模块

主要功能：
1. 从飞书表格获取待二创的文案记录
2. 批量调用Coze二创工作流处理文案
3. 并发控制（并发数为4）
4. 进度显示和错误处理
"""

import requests
import json
import threading
import time
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class ContentRewriteProcessor:
    """文案批量二创处理器"""

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
            print(message)

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

    def get_pending_rewrite_records(self, app_token: str, table_id: str, view_id: str = "", rewrite_filter: bool = True) -> List[Dict[str, Any]]:
        """
        从飞书表格获取待二创记录

        Args:
            app_token: 飞书应用token
            table_id: 表格ID
            view_id: 视图ID（可选）
            rewrite_filter: 是否只采集需要二创的记录

        Returns:
            表格数据列表
        """
        if not app_token:
            raise ValueError("飞书app_token不能为空")

        # 获取访问令牌
        access_token = self.get_access_token()

        if rewrite_filter:
            # 使用搜索API，添加二创过滤条件
            base_url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
            url = f"{base_url}/{app_token}/tables/{table_id}/records/search"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # 构建过滤条件：需要二创为true
            filter_condition = {
                "conjunction": "and",
                "conditions": [
                    {
                        "field_name": "状态",
                        "operator": "is",
                        "value": ["二创文案生成"]
                    }
                ]
            }

            payload = {
                "page_size": 100,
                "filter": filter_condition
            }

            try:
                self.log_message(f"ContentRewrite搜索请求URL: {url}")
                self.log_message(f"ContentRewrite搜索请求体: {payload}")

                response = requests.post(url, headers=headers, json=payload, timeout=30)

                self.log_message(f"ContentRewrite搜索响应状态码: {response.status_code}")
                self.log_message(f"ContentRewrite搜索响应内容: {response.text}")

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
            if view_id and view_id.strip():
                params["view_id"] = view_id

            try:
                self.log_message(f"ContentRewrite请求URL: {url}")
                self.log_message(f"ContentRewrite请求参数: {params}")

                response = requests.get(url, headers=headers, params=params, timeout=30)

                self.log_message(f"ContentRewrite响应状态码: {response.status_code}")
                self.log_message(f"ContentRewrite响应内容: {response.text}")

                response.raise_for_status()

                data = response.json()
                if data.get("code") == 0:
                    return data.get("data", {}).get("items", [])
                else:
                    raise Exception(f"飞书API错误: {data.get('msg', '未知错误')} (错误码: {data.get('code')})")

            except Exception as e:
                raise Exception(f"获取飞书表格数据失败: {str(e)}")

    def coze_rewrite_workflow_request(self, token: str, workflow_id: str, content: str, current_user: str = None,
                                     digital_no: str = None, material_video: str = None, voice_id: str = None,
                                     record_id: str = None, table_id: str = None, app_token: str = None) -> Dict[str, Any]:
        """
        发送请求到Coze二创工作流

        Args:
            token: Coze API token
            workflow_id: 工作流ID
            content: 视频文案内容
            current_user: 当前用户
            digital_no: 数字人编号
            material_video: 素材视频
            voice_id: 语音ID
            record_id: 记录ID
            table_id: 表格ID
            app_token: 应用token

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
                "content": content,
                "currentUser": current_user or "",
                "digitalNo": digital_no or "",
                "materialVideo": material_video or "",
                "voiceId": voice_id or "",
                "recordId": record_id or "",
                "tableId": table_id or "",
                "appToken": app_token or ""
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

            # 响应信息
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

                        # 提取execute_id用于后续轮询
                        execute_id = result.get("data", {}).get("execute_id")
                        if execute_id:
                            self.log_message(f"获取到执行ID: {execute_id}")
                            result["execute_id"] = execute_id  # 将execute_id添加到结果中
                        else:
                            self.log_message("⚠️ 响应中未找到execute_id")

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

    def poll_workflow_result(self, execute_id: str, workflow_id: str, token: str, max_attempts: int = 20, interval: int = 60) -> Optional[Dict[str, Any]]:
        """
        轮询工作流结果

        Args:
            execute_id: 执行ID
            workflow_id: 工作流ID
            token: Coze API token
            max_attempts: 最大尝试次数（默认20次，总计20分钟）
            interval: 轮询间隔（默认60秒，即每分钟一次）

        Returns:
            工作流执行结果，超时或失败返回None
        """
        url = f"https://api.coze.cn/v1/workflows/{workflow_id}/run_histories/{execute_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(url, headers=headers, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    self.log_message(f"轮询第{attempt}次，响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

                    if result.get("code") == 0:
                        data = result.get("data", [])
                        if data:
                            execution_record = data[0]
                            execute_status = execution_record.get("execute_status")

                            if execute_status == "Success":
                                self.log_message(f"✅ 工作流执行成功")
                                return execution_record
                            elif execute_status == "Failed":
                                self.log_message(f"❌ 工作流执行失败")
                                return None
                            elif execute_status == "Running":
                                self.log_message(f"⏳ 工作流正在执行中... (第{attempt}/{max_attempts}次)")
                                if attempt < max_attempts:
                                    time.sleep(interval)
                                    continue
                            else:
                                self.log_message(f"❓ 未知状态: {execute_status}")
                                if attempt < max_attempts:
                                    time.sleep(interval)
                                    continue
                        else:
                            self.log_message(f"⚠️ 响应数据为空")
                    else:
                        self.log_message(f"❌ API错误: {result.get('msg', '未知错误')}")

                        # 检查是否是网络超时等错误
                        error_msg = result.get('msg', '')
                        error_code = result.get('code')

                        # 网络超时等严重错误立即终止
                        if (any(keyword in error_msg.lower() for keyword in ['timeout', 'timed out', 'access plugin', 'server error']) or
                            error_code in ["720701002", "720701001"]):
                            self.log_message("🚨 检测到严重错误，立即终止轮询")
                            return None

                        if attempt < max_attempts:
                            time.sleep(interval)
                            continue
                else:
                    self.log_message(f"❌ HTTP请求失败，状态码：{response.status_code}")
                    if attempt < max_attempts:
                        time.sleep(interval)
                        continue

            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                self.log_message(f"❌ 请求异常：{error_msg}")

                # 网络错误立即终止
                if any(keyword in error_msg.lower() for keyword in ['timeout', 'timed out', 'connection', 'network']):
                    self.log_message("🚨 检测到网络错误，立即终止轮询")
                    return None

                if attempt < max_attempts:
                    time.sleep(interval)
                    continue

        # 超时处理
        self.log_message(f"⏰ 轮询超时（{max_attempts * interval}秒）")
        return None

    def process_single_rewrite(self, item: Dict[str, Any], coze_token: str, coze_workflow_id: str,
                              feishu_table_id: str, feishu_app_token: str) -> Dict[str, Any]:
        """
        处理单个文案二创

        Args:
            item: 文案数据
            coze_token: Coze API token
            coze_workflow_id: Coze工作流ID
            feishu_table_id: 飞书表格ID
            feishu_app_token: 飞书应用token

        Returns:
            处理结果
        """
        record_id = item.get('record_id', '')
        fields = item.get('fields', {})
        content = fields.get('视频文案', '')

        try:
            self.log_message(f"开始处理记录 {record_id} 的文案二创...")

            # 调用Coze二创工作流
            result = self.coze_rewrite_workflow_request(
                token=coze_token,
                workflow_id=coze_workflow_id,
                content=content,
                current_user=fields.get('当前用户', ''),
                digital_no=fields.get('数字人编号', ''),
                material_video=fields.get('素材视频', ''),
                voice_id=fields.get('语音ID', ''),
                record_id=record_id,
                table_id=feishu_table_id,
                app_token=feishu_app_token
            )

            if result:
                # 检查是否有execute_id，如果有则进行轮询
                execute_id = result.get("execute_id")
                if execute_id:
                    self.log_message(f"开始轮询记录 {record_id} 的执行结果...")

                    # 轮询工作流执行结果
                    poll_result = self.poll_workflow_result(
                        execute_id=execute_id,
                        workflow_id=coze_workflow_id,
                        token=coze_token,
                        max_attempts=20,
                        interval=30
                    )

                    if poll_result:
                        self.log_message(f"✅ 记录 {record_id} 文案二创成功（轮询完成）")
                        return {
                            'record_id': record_id,
                            'success': True,
                            'result': poll_result,
                            'execute_id': execute_id
                        }
                    else:
                        self.log_message(f"❌ 记录 {record_id} 文案二创失败（轮询超时或失败）")
                        return {
                            'record_id': record_id,
                            'success': False,
                            'error': '轮询工作流结果失败',
                            'execute_id': execute_id
                        }
                else:
                    # 没有execute_id，假设立即完成
                    self.log_message(f"✅ 记录 {record_id} 文案二创成功（无轮询）")
                    return {
                        'record_id': record_id,
                        'success': True,
                        'result': result
                    }
            else:
                self.log_message(f"❌ 记录 {record_id} 文案二创失败")
                return {
                    'record_id': record_id,
                    'success': False,
                    'error': 'Coze工作流调用失败'
                }

        except Exception as e:
            self.log_message(f"❌ 记录 {record_id} 处理异常: {str(e)}")
            return {
                'record_id': record_id,
                'success': False,
                'error': str(e)
            }

    def process_content_rewrite_batch(self,
                                    feishu_app_token: str,
                                    feishu_table_id: str,
                                    feishu_view_id: str = "",
                                    coze_token: str = None,
                                    coze_workflow_id: str = None,
                                    content_field: str = "视频文案",
                                    max_workers: int = 4,
                                    progress_callback=None) -> Dict[str, Any]:
        """
        批量处理文案二创

        Args:
            feishu_app_token: 飞书应用token
            feishu_table_id: 飞书表格ID
            feishu_view_id: 飞书视图ID
            coze_token: Coze API token
            coze_workflow_id: Coze工作流ID
            content_field: 文案字段名
            max_workers: 最大并发数
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
            # 1. 获取飞书表格数据
            if progress_callback:
                progress_callback("正在获取飞书状态为'二创文案生成'的记录数据...", 0)

            # 使用配置中的默认值
            actual_feishu_view_id = feishu_view_id or self.feishu_config.get('content_view_id', '')
            actual_coze_token = coze_token or self.coze_config.get('bearer_token', '')
            actual_coze_workflow_id = coze_workflow_id or self.coze_config.get('content_workflow_id', '')

            table_data = self.get_pending_rewrite_records(feishu_app_token, feishu_table_id, actual_feishu_view_id, rewrite_filter=True)

            if not table_data:
                if progress_callback:
                    progress_callback("飞书表格中没有状态为'二创文案生成'的记录", 100)
                return results

            # 2. 提取视频文案并统计有效记录
            content_list = []
            invalid_records = []
            for record in table_data:
                fields = record.get('fields', {})
                content = fields.get(content_field)
                record_id = record.get('record_id', '')

                if content:
                    content_list.append({
                        'content': content,
                        'record_id': record_id,
                        'fields': fields
                    })
                else:
                    invalid_records.append({
                        'record_id': record_id,
                        'reason': '视频文案为空'
                    })

            # 设置总数为有效记录数
            results['total'] = len(content_list)

            # 记录无效记录
            for invalid_record in invalid_records:
                results['errors'].append(f"无效记录: {invalid_record['record_id']}, 原因: {invalid_record['reason']}")

            if not content_list:
                if progress_callback:
                    progress_callback("未找到有效的视频文案", 100)
                return results

            # 3. 使用线程池批量处理视频文案
            self.log_message(f"开始批量处理 {len(content_list)} 个状态为'二创文案生成'的文案（并发数: {max_workers}）...")
            self.log_message(f"Coze Token: {actual_coze_token[:20]}..." if actual_coze_token else "Coze Token: 未设置")
            self.log_message(f"Coze Workflow ID: {actual_coze_workflow_id}")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_item = {
                    executor.submit(
                        self.process_single_rewrite,
                        item,
                        actual_coze_token,
                        actual_coze_workflow_id,
                        feishu_table_id,
                        feishu_app_token
                    ): item for item in content_list
                }

                # 处理完成的任务
                completed_count = 0
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        result = future.result()
                        completed_count += 1

                        if result['success']:
                            results['success'] += 1
                        else:
                            results['failed'] += 1
                            results['errors'].append(f"文案二创失败: {result['record_id']}, 错误: {result.get('error', '未知错误')}")

                        # 更新进度
                        if progress_callback:
                            progress = int(completed_count / len(content_list) * 90)
                            progress_callback(f"正在处理第 {completed_count}/{len(content_list)} 条状态为'二创文案生成'的文案...", progress)

                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f"处理文案二创时出错: {item.get('record_id', 'unknown')}, 错误: {str(e)}")
                        self.log_message(f"❌ 处理文案二创时发生异常: {str(e)}")

            results['end_time'] = datetime.now()

            # 添加处理结果汇总日志
            duration = results['end_time'] - results['start_time']
            self.log_message(f"\n=== 批量文案二创完成（状态为'二创文案生成'） ===")
            self.log_message(f"飞书表格总记录数: {len(table_data)}")
            self.log_message(f"有效记录数: {results['total']}")
            self.log_message(f"无效记录数: {len(invalid_records)}")
            self.log_message(f"成功处理: {results['success']}")
            self.log_message(f"失败数量: {results['failed']}")
            self.log_message(f"处理耗时: {duration.total_seconds():.1f} 秒")

            # 统计错误类型
            if invalid_records:
                self.log_message("无效记录详情:")
                for invalid_record in invalid_records:
                    self.log_message(f"  - 记录ID: {invalid_record['record_id']}, 原因: {invalid_record['reason']}")

            if results['errors']:
                self.log_message("处理错误详情:")
                for error in results['errors']:
                    self.log_message(f"  - {error}")

            if progress_callback:
                progress_callback(f"批量文案二创完成! 共处理{len(content_list)}条状态为'二创文案生成'的文案", 100)

        except Exception as e:
            self.log_message(f"❌ 批量处理过程中发生严重错误: {str(e)}")
            import traceback
            self.log_message(f"异常堆栈: {traceback.format_exc()}")
            results['errors'].append(f"批量处理过程中发生错误: {str(e)}")
            results['end_time'] = datetime.now()

            if progress_callback:
                progress_callback(f"处理失败: {str(e)}", 100)

        return results


class ContentRewriteThread(threading.Thread):
    """文案二创线程"""

    def __init__(self, processor: ContentRewriteProcessor, params: Dict[str, Any], callback=None):
        super().__init__()
        self.processor = processor
        self.params = params
        self.callback = callback
        self.results = None
        self.is_running = False

    def run(self):
        self.is_running = True
        try:
            self.results = self.processor.process_content_rewrite_batch(
                feishu_app_token=self.params.get('feishu_app_token', ''),
                feishu_table_id=self.params.get('feishu_table_id', ''),
                feishu_view_id=self.params.get('feishu_view_id', ''),
                coze_token=self.params.get('coze_token', ''),
                coze_workflow_id=self.params.get('coze_workflow_id', ''),
                content_field=self.params.get('content_field', '视频文案'),
                max_workers=self.params.get('max_workers', 4),
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