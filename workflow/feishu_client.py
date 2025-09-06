#!/usr/bin/env python3
"""
飞书多维表格API客户端

用于从飞书多维表格获取数据并转换为视频任务
"""

import json
import time
import requests
import random
from typing import Dict, List, Any, Optional
from datetime import datetime


class FeishuBitableClient:
    """飞书多维表格客户端"""
    
    def __init__(self, app_id: str, app_secret: str):
        """初始化客户端
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.token_expires = 0
        
        # API基础URL
        self.base_url = "https://open.feishu.cn/open-apis"
        
    def get_tenant_access_token(self) -> str:
        """获取租户访问令牌
        
        Returns:
            访问令牌
        """
        # 如果令牌未过期，直接返回
        if self.access_token and time.time() < self.token_expires:
            return self.access_token
            
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                self.access_token = data.get("tenant_access_token")
                # 设置令牌过期时间（提前5分钟过期）
                self.token_expires = time.time() + data.get("expire", 3600) - 300
                return self.access_token
            else:
                raise Exception(f"获取访问令牌失败: {data.get('msg')}")
                
        except requests.RequestException as e:
            raise Exception(f"请求失败: {e}")
    
    def search_records(self, app_token: str, table_id: str, 
                     filter_condition: Optional[Dict] = None,
                     page_size: int = 100,
                     page_token: Optional[str] = None) -> Dict[str, Any]:
        """搜索多维表格记录
        
        Args:
            app_token: 应用令牌
            table_id: 表格ID
            filter_condition: 过滤条件
            page_size: 页面大小
            page_token: 分页令牌
            
        Returns:
            搜索结果
        """
        token = self.get_tenant_access_token()
        
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "page_size": page_size
        }
        
        if page_token:
            payload["page_token"] = page_token
            
        if filter_condition:
            payload["filter"] = filter_condition
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {})
            else:
                raise Exception(f"搜索记录失败: {data.get('msg')}")
                
        except requests.RequestException as e:
            raise Exception(f"请求失败: {e}")
    
    def get_all_records(self, app_token: str, table_id: str, 
                       filter_condition: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """获取所有记录（自动处理分页）
        
        Args:
            app_token: 应用令牌
            table_id: 表格ID
            filter_condition: 过滤条件
            
        Returns:
            所有记录列表
        """
        all_records = []
        page_token = None
        
        while True:
            result = self.search_records(
                app_token=app_token,
                table_id=table_id,
                filter_condition=filter_condition,
                page_token=page_token
            )
            
            records = result.get("items", [])
            all_records.extend(records)
            
            # 检查是否还有更多记录
            if not result.get("has_more", False):
                break
                
            page_token = result.get("page_token")
            
        return all_records
    
    def records_to_tasks(self, records: List[Dict[str, Any]], 
                        field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """将飞书记录转换为任务格式
        
        Args:
            records: 飞书记录列表
            field_mapping: 字段映射配置
            
        Returns:
            任务列表
        """
        tasks = []
        
        for i, record in enumerate(records):
            fields = record.get("fields", {})
            
            # 创建任务
            task = {
                "id": f"feishu_{i+1}",
                "title": fields.get(field_mapping.get("title", "title"), ""),
                "content": fields.get(field_mapping.get("content", "content"), ""),
                "digital_no": fields.get(field_mapping.get("digital_no", "digital_no"), ""),
                "voice_id": fields.get(field_mapping.get("voice_id", "voice_id"), ""),
                "project_name": fields.get(field_mapping.get("project_name", "project_name"), ""),
                "feishu_record_id": record.get("record_id"),
                "feishu_data": record  # 保存原始飞书数据
            }
            
            # 只添加有标题和内容的任务
            if task["title"] and task["content"]:
                tasks.append(task)
        
        return tasks


class FeishuVideoTaskSource:
    """飞书视频任务数据源"""
    
    def __init__(self, app_id: str, app_secret: str, 
                 app_token: str, table_id: str,
                 field_mapping: Optional[Dict] = None,
                 account_table_config: Optional[Dict] = None,
                 voice_table_config: Optional[Dict] = None,
                 digital_human_table_config: Optional[Dict] = None):
        """初始化数据源
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            app_token: 多维表格应用令牌
            table_id: 表格ID
            field_mapping: 字段映射配置
            account_table_config: 账号表配置
            voice_table_config: 音色表配置
            digital_human_table_config: 数字人表配置
        """
        self.client = FeishuBitableClient(app_id, app_secret)
        self.app_token = app_token
        self.table_id = table_id
        
        # 默认字段映射
        self.field_mapping = field_mapping or {
            "title": "仿写标题",
            "content": "仿写文案", 
            "digital_no": "数字人编号",
            "voice_id": "声音ID",
            "project_name": "项目名称",
            "account": "关联账号"
        }
        
        # 关联表配置
        self.account_table_config = account_table_config
        self.voice_table_config = voice_table_config
        self.digital_human_table_config = digital_human_table_config
        
        # 缓存
        self._account_cache = {}
        self._voice_cache = {}
        self._digital_human_cache = {}
    
    def get_tasks(self, filter_condition: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """获取任务列表
        
        Args:
            filter_condition: 过滤条件
            
        Returns:
            任务列表
        """
        print(f"[INFO] 正在从飞书多维表格获取数据...")
        print(f"[INFO] 表格ID: {self.table_id}")
        print(f"[INFO] 字段映射: {self.field_mapping}")
        
        try:
            # 尝试使用过滤条件获取记录
            try:
                records = self.client.get_all_records(
                    app_token=self.app_token,
                    table_id=self.table_id,
                    filter_condition=filter_condition
                )
                print(f"[INFO] 使用过滤条件获取到 {len(records)} 条记录")
            except Exception as filter_error:
                print(f"[WARN] 过滤条件失败，回退到获取所有记录: {filter_error}")
                # 如果过滤条件失败，尝试不使用过滤条件
                records = self.client.get_all_records(
                    app_token=self.app_token,
                    table_id=self.table_id,
                    filter_condition=None
                )
                print(f"[INFO] 获取所有记录，共 {len(records)} 条")
            
            # 预加载关联数据
            if self.account_table_config:
                self._preload_account_data()
            if self.voice_table_config:
                self._preload_voice_data()
            if self.digital_human_table_config:
                self._preload_digital_human_data()
            
            # 转换为任务格式（带关联查询）
            tasks = self._records_to_tasks_with_relations(records)
            
            print(f"[INFO] 转换为 {len(tasks)} 个有效任务")
            
            return tasks
            
        except Exception as e:
            print(f"[ERROR] 获取飞书数据失败: {e}")
            raise
    
    def create_default_filter(self) -> Dict:
        """创建默认过滤条件
        
        Returns:
            默认过滤条件
        """
        # 示例：只获取状态为"待处理"的记录
        return {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": "状态",
                    "operator": "is",
                    "value": "视频草稿生成"
                }
            ]
        }
    
    def update_record_status(self, record_id: str, status: str) -> bool:
        """更新记录状态
        
        Args:
            record_id: 记录ID
            status: 新状态
            
        Returns:
            是否成功
        """
        token = self.client.get_tenant_access_token()
        
        url = f"{self.client.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 构建更新 payload，假设状态字段名为"状态"
        payload = {
            "fields": {
                "状态": status
            }
        }
        
        try:
            response = requests.put(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                print(f"[INFO] 成功更新记录 {record_id} 状态为: {status}")
                return True
            else:
                print(f"[ERROR] 更新记录状态失败: {data.get('msg')}")
                return False
                
        except requests.RequestException as e:
            print(f"[ERROR] 更新记录状态请求失败: {e}")
            return False
    
    def update_record_fields(self, record_id: str, fields: Dict[str, Any]) -> bool:
        """更新记录多个字段
        
        Args:
            record_id: 记录ID
            fields: 要更新的字段字典
            
        Returns:
            是否成功
        """
        token = self.client.get_tenant_access_token()
        
        url = f"{self.client.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 构建更新 payload
        payload = {
            "fields": fields
        }
        
        try:
            response = requests.put(url, headers=headers, json=payload)
            
            # 打印响应状态码和内容用于调试
            print(f"[DEBUG] 飞书API响应状态码: {response.status_code}")
            print(f"[DEBUG] 飞书API响应内容: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0:
                print(f"[INFO] 成功更新记录 {record_id} 字段: {list(fields.keys())}")
                return True
            else:
                print(f"[ERROR] 更新记录字段失败: {data.get('msg')}")
                return False
                
        except requests.RequestException as e:
            print(f"[ERROR] 更新记录字段请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] 响应状态码: {e.response.status_code}")
                print(f"[ERROR] 响应内容: {e.response.text}")
            return False
    
    def _preload_account_data(self):
        """预加载账号数据"""
        if not self.account_table_config:
            return
            
        print("[INFO] 预加载账号数据...")
        records = self.client.get_all_records(
            app_token=self.app_token,
            table_id=self.account_table_config["table_id"]
        )
        
        account_field = self.account_table_config.get("account_field", "账号")
        name_field = self.account_table_config.get("name_field", "名称")
        
        for record in records:
            fields = record.get("fields", {})
            account_id = fields.get(account_field)
            if account_id:
                self._account_cache[account_id] = {
                    "name": fields.get(name_field, ""),
                    "record_id": record.get("record_id"),
                    "raw_data": record
                }
        
        print(f"[INFO] 已加载 {len(self._account_cache)} 个账号")
    
    def _preload_voice_data(self):
        """预加载音色数据"""
        if not self.voice_table_config:
            return
            
        print("[INFO] 预加载音色数据...")
        records = self.client.get_all_records(
            app_token=self.app_token,
            table_id=self.voice_table_config["table_id"]
        )
        
        account_field = self.voice_table_config.get("account_field", "关联账号")
        voice_id_field = self.voice_table_config.get("voice_id_field", "声音ID")
        
        for record in records:
            fields = record.get("fields", {})
            account_id = fields.get(account_field)
            voice_id = fields.get(voice_id_field)
            
            if account_id and voice_id:
                if account_id not in self._voice_cache:
                    self._voice_cache[account_id] = []
                self._voice_cache[account_id].append({
                    "voice_id": voice_id,
                    "record_id": record.get("record_id"),
                    "raw_data": record
                })
        
        print(f"[INFO] 已加载 {len(self._voice_cache)} 个账号的音色数据")
    
    def _preload_digital_human_data(self):
        """预加载数字人数据"""
        if not self.digital_human_table_config:
            return
            
        print("[INFO] 预加载数字人数据...")
        records = self.client.get_all_records(
            app_token=self.app_token,
            table_id=self.digital_human_table_config["table_id"]
        )
        
        account_field = self.digital_human_table_config.get("account_field", "关联账号")
        digital_no_field = self.digital_human_table_config.get("digital_no_field", "数字人编号")
        
        for record in records:
            fields = record.get("fields", {})
            account_id = fields.get(account_field)
            digital_no = fields.get(digital_no_field)
            
            if account_id and digital_no:
                if account_id not in self._digital_human_cache:
                    self._digital_human_cache[account_id] = []
                self._digital_human_cache[account_id].append({
                    "digital_no": digital_no,
                    "record_id": record.get("record_id"),
                    "raw_data": record
                })
        
        print(f"[INFO] 已加载 {len(self._digital_human_cache)} 个账号的数字人数据")
    
    def _get_voice_id_by_account(self, account_id: str) -> Optional[str]:
        """根据账号ID获取音色ID
        
        Args:
            account_id: 账号ID
            
        Returns:
            音色ID，如果找不到返回None
        """
        if not account_id:
            return None
            
        voice_data = self._voice_cache.get(account_id)
        if voice_data and len(voice_data) > 0:
            # 一个账号只有一个音色，取第一个并提取纯文本
            raw_voice_id = voice_data[0]["voice_id"]
            return self.extract_text_from_rich_text(raw_voice_id)
        
        return None
    
    def _get_digital_no_by_account(self, account_id: str) -> Optional[str]:
        """根据账号ID随机获取数字人编号
        
        Args:
            account_id: 账号ID
            
        Returns:
            数字人编号，如果找不到返回None
        """
        if not account_id:
            return None
            
        digital_humans = self._digital_human_cache.get(account_id)
        if digital_humans and len(digital_humans) > 0:
            # 随机选择一个数字人
            selected = random.choice(digital_humans)
            raw_digital_no = selected["digital_no"]
            clean_digital_no = self.extract_text_from_rich_text(raw_digital_no)
            print(f"[DEBUG] 账号 {account_id} 随机选择数字人: {clean_digital_no}")
            return clean_digital_no
        
        return None
    
    def extract_text_from_rich_text(self, rich_text):
        """从富文本格式中提取纯文本
        
        Args:
            rich_text: 富文本数据，可以是字符串或列表
            
        Returns:
            纯文本字符串
        """
        if isinstance(rich_text, str):
            return rich_text.strip()
        
        if isinstance(rich_text, list):
            text_parts = []
            for item in rich_text:
                if isinstance(item, dict):
                    text_content = item.get('text', '')
                    if text_content:
                        text_parts.append(text_content)
                elif isinstance(item, str):
                    text_parts.append(item)
            
            combined_text = ''.join(text_parts)
            return combined_text.strip()
        
        return str(rich_text).strip()
    
    def clean_project_name(self, title, account_id, timestamp):
        """生成干净的项目名称
        
        Args:
            title: 标题（可能是富文本格式）
            account_id: 账号ID
            timestamp: 时间戳
            
        Returns:
            干净的项目名称
        """
        # 提取纯文本标题
        clean_title = self.extract_text_from_rich_text(title)
        
        # 清理标题中的特殊字符
        clean_title = clean_title.replace('_', ' ').replace('-', ' ')
        clean_title = ' '.join(clean_title.split())  # 去除多余空格
        
        # 限制标题长度
        if len(clean_title) > 30:
            clean_title = clean_title[:30] + '...'
        
        if account_id and clean_title:
            return f"{account_id}_{clean_title}_{timestamp}"
        elif account_id:
            return f"{account_id}_video_{timestamp}"
        elif clean_title:
            return f"{clean_title}_{timestamp}"
        else:
            return f"video_{timestamp}"
    
    def _records_to_tasks_with_relations(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将飞书记录转换为任务格式（带关联查询）
        
        Args:
            records: 飞书记录列表
            
        Returns:
            任务列表
        """
        tasks = []
        
        for i, record in enumerate(records):
            fields = record.get("fields", {})
            
            # 获取关联账号
            account_id = fields.get(self.field_mapping.get("account", "关联账号"))
            
            # 通过关联账号查询音色ID和数字人编号
            voice_id = self._get_voice_id_by_account(account_id)
            digital_no = self._get_digital_no_by_account(account_id)
            
            # 提取纯文本标题和内容
            title_raw = fields.get(self.field_mapping.get("title", "仿写标题"), "")
            content_raw = fields.get(self.field_mapping.get("content", "仿写文案"), "")
            
            title_clean = self.extract_text_from_rich_text(title_raw)
            content_clean = self.extract_text_from_rich_text(content_raw)
            
            # 生成项目名称：关联账号 + 仿写标题 + 时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = self.clean_project_name(title_clean, account_id, timestamp)
            
            # 创建任务
            task = {
                "id": f"feishu_{i+1}",
                "title": title_clean,
                "content": content_clean,
                "digital_no": digital_no or self.extract_text_from_rich_text(fields.get(self.field_mapping.get("digital_no", "数字人编号"), "")),
                "voice_id": voice_id or self.extract_text_from_rich_text(fields.get(self.field_mapping.get("voice_id", "声音ID"), "")),
                "project_name": project_name,
                "account_id": account_id,
                "feishu_record_id": record.get("record_id"),
                "feishu_data": record  # 保存原始飞书数据
            }
            
            # 只添加有标题和内容的任务
            if task["title"] and task["content"]:
                tasks.append(task)
        
        return tasks


def create_sample_filter_condition():
    """创建示例过滤条件"""
    return {
        "conjunction": "and",
        "conditions": [
            {
                "field_name": "状态",
                "operator": "is",
                "value": "待处理"
            },
            {
                "field_name": "优先级",
                "operator": "isNotEmpty"
            }
        ]
    }


if __name__ == "__main__":
    # 示例用法
    config = {
        "app_id": "your_app_id",
        "app_secret": "your_app_secret", 
        "app_token": "your_app_token",
        "table_id": "your_table_id"
    }
    
    # 创建数据源
    task_source = FeishuVideoTaskSource(**config)
    
    try:
        # 获取任务
        tasks = task_source.get_tasks()
        
        print(f"\n获取到 {len(tasks)} 个任务:")
        for task in tasks[:3]:  # 只显示前3个
            print(f"- {task['title']}")
            
    except Exception as e:
        print(f"示例运行失败: {e}")
        print("请确保配置了正确的飞书API凭据")