#!/usr/bin/env python3
"""
飞书多维表格批量视频工作流

从飞书多维表格获取数据并批量执行视频合成任务
"""

import sys
import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from workflow.examples.batch_coze_workflow import BatchCozeWorkflow
from workflow.feishu_client import FeishuVideoTaskSource


class FeishuBatchWorkflow:
    """飞书批量视频工作流处理器"""
    
    def __init__(self, draft_folder_path: str, max_workers: int = 3):
        """初始化
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            max_workers: 最大并发数
        """
        self.batch_processor = BatchCozeWorkflow(draft_folder_path, max_workers)
        self.feishu_config = None
        self.field_mapping = None
        
    def set_feishu_config(self, app_id: str, app_secret: str, 
                         app_token: str, table_id: str):
        """设置飞书配置
        
        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            app_token: 多维表格应用令牌
            table_id: 表格ID
        """
        self.feishu_config = {
            "app_id": app_id,
            "app_secret": app_secret,
            "app_token": app_token,
            "table_id": table_id
        }
        
    def set_config_from_dict(self, config: Dict):
        """从字典设置配置
        
        Args:
            config: 配置字典
        """
        api_config = config.get("api_config", {})
        tables = config.get("tables", {})
        
        # 设置API配置
        self.feishu_config = {
            "app_id": api_config.get("app_id"),
            "app_secret": api_config.get("app_secret"),
            "app_token": api_config.get("app_token"),
            "table_id": tables.get("content_table", {}).get("table_id")
        }
        
        # 设置字段映射
        self.field_mapping = tables.get("content_table", {}).get("field_mapping", {})
        
        # 设置关联表配置
        account_table = tables.get("account_table", {})
        voice_table = tables.get("voice_table", {})
        digital_human_table = tables.get("digital_human_table", {})
        
        if account_table:
            self.account_table_config = {
                "app_token": api_config.get("app_token"),
                "table_id": account_table.get("table_id"),
                "account_field": account_table.get("account_field", "账号"),
                "name_field": account_table.get("name_field", "名称")
            }
            
        if voice_table:
            self.voice_table_config = {
                "app_token": api_config.get("app_token"),
                "table_id": voice_table.get("table_id"),
                "account_field": voice_table.get("account_field", "关联账号"),
                "voice_id_field": voice_table.get("voice_id_field", "声音ID")
            }
            
        if digital_human_table:
            self.digital_human_table_config = {
                "app_token": api_config.get("app_token"),
                "table_id": digital_human_table.get("table_id"),
                "account_field": digital_human_table.get("account_field", "关联账号"),
                "digital_no_field": digital_human_table.get("digital_no_field", "数字人编号")
            }
        
        # 设置默认过滤条件
        self.default_filter = tables.get("content_table", {}).get("filter_condition")
        
    def set_field_mapping(self, mapping: Dict[str, str]):
        """设置字段映射
        
        Args:
            mapping: 字段映射配置
        """
        self.field_mapping = mapping
        
    def set_relation_tables(self, account_config: Dict = None, 
                           voice_config: Dict = None,
                           digital_human_config: Dict = None):
        """设置关联表配置
        
        Args:
            account_config: 账号表配置
            voice_config: 音色表配置
            digital_human_config: 数字人表配置
        """
        self.account_table_config = account_config
        self.voice_table_config = voice_config
        self.digital_human_table_config = digital_human_config
        
    def set_background_music(self, music_path: str, volume: float = 0.3):
        """设置背景音乐"""
        self.batch_processor.set_background_music(music_path, volume)
        
    def set_doubao_api(self, token: str, model: str):
        """设置豆包API配置"""
        self.batch_processor.set_doubao_api(token, model)
        
    def load_tasks_from_feishu(self, filter_condition: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """从飞书加载任务
        
        Args:
            filter_condition: 过滤条件
            
        Returns:
            任务列表
        """
        if not self.feishu_config:
            raise ValueError("请先设置飞书配置")
            
        # 创建飞书数据源
        task_source = FeishuVideoTaskSource(
            **self.feishu_config,
            field_mapping=self.field_mapping,
            account_table_config=getattr(self, 'account_table_config', None),
            voice_table_config=getattr(self, 'voice_table_config', None),
            digital_human_table_config=getattr(self, 'digital_human_table_config', None)
        )
        
        # 获取任务
        tasks = task_source.get_tasks(filter_condition)
        return tasks
        
    def process_feishu_batch(self, filter_condition: Optional[Dict] = None,
                           include_ids: List[str] = None,
                           exclude_ids: List[str] = None,
                           save_tasks: bool = True) -> List[Dict[str, Any]]:
        """处理飞书批量任务
        
        Args:
            filter_condition: 过滤条件
            include_ids: 包含的任务ID列表
            exclude_ids: 排除的任务ID列表
            save_tasks: 是否保存任务到文件
            
        Returns:
            处理结果列表
        """
        print("[INFO] 开始从飞书加载任务...")
        
        # 使用传入的过滤条件或默认过滤条件
        actual_filter = filter_condition or getattr(self, 'default_filter', None)
        
        # 从飞书加载任务
        tasks = self.load_tasks_from_feishu(actual_filter)
        
        if not tasks:
            print("[WARN] 没有找到符合条件的任务")
            return []
            
        # 保存任务到文件
        if save_tasks:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tasks_file = f"feishu_tasks_{timestamp}.json"
            
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
                
            print(f"[INFO] 任务已保存到: {tasks_file}")
        
        # 显示任务信息
        print(f"\n📋 从飞书获取到 {len(tasks)} 个任务:")
        print("-" * 80)
        for task in tasks[:5]:  # 只显示前5个
            print(f"ID: {task.get('id')}")
            print(f"标题: {task.get('title')}")
            print(f"数字人: {task.get('digital_no')}")
            print(f"声音: {task.get('voice_id')}")
            print("-" * 80)
            
        if len(tasks) > 5:
            print(f"... 还有 {len(tasks) - 5} 个任务")
        
        # 创建飞书任务源并设置给批量处理器以启用状态更新
        print("[INFO] 设置飞书状态更新...")
        task_source = FeishuVideoTaskSource(
            app_id=self.feishu_config["app_id"],
            app_secret=self.feishu_config["app_secret"],
            app_token=self.feishu_config["app_token"],
            table_id=self.feishu_config["table_id"],
            field_mapping=self.field_mapping,
            account_table_config=getattr(self, 'account_table_config', None),
            voice_table_config=getattr(self, 'voice_table_config', None),
            digital_human_table_config=getattr(self, 'digital_human_table_config', None)
        )
        
        # 设置飞书任务源以启用状态更新
        self.batch_processor.set_feishu_task_source(task_source)
        
        # 执行批量处理
        print(f"\n[INFO] 开始批量处理...")
        results = self.batch_processor.process_batch(tasks, include_ids, exclude_ids)
        
        return results


def create_default_field_mapping():
    """创建默认字段映射"""
    return {
        "title": "标题",
        "content": "内容",
        "digital_no": "数字人编号", 
        "voice_id": "声音ID",
        "project_name": "项目名称"
    }


def create_default_filter():
    """创建默认过滤条件"""
    return {
        "conjunction": "and",
        "conditions": [
            {
                "field_name": "状态",
                "operator": "is",
                "value": "待处理"
            }
        ]
    }


def load_config_from_file(config_file: str) -> Dict:
    """从配置文件加载配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置字典
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"配置文件不存在: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='飞书多维表格批量视频工作流')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--app-id', help='飞书应用ID')
    parser.add_argument('--app-secret', help='飞书应用密钥')
    parser.add_argument('--app-token', help='多维表格应用令牌')
    parser.add_argument('--table-id', help='表格ID')
    parser.add_argument('--max-workers', type=int, default=2, help='最大并发数（默认2）')
    parser.add_argument('--music-path', help='背景音乐文件路径')
    parser.add_argument('--music-volume', type=float, default=0.3, help='背景音乐音量（默认0.3）')
    parser.add_argument('--doubao-token', default='adac0afb-5fd4-4c66-badb-370a7ff42df5', help='豆包API令牌')
    parser.add_argument('--doubao-model', default='ep-m-20250902010446-mlwmf', help='豆包模型')
    parser.add_argument('--include', nargs='*', help='只执行指定的任务ID')
    parser.add_argument('--exclude', nargs='*', help='跳过指定的任务ID')
    parser.add_argument('--no-save', action='store_true', help='不保存任务到文件')
    parser.add_argument('--no-relations', action='store_true', help='不使用关联表查询')
    
    args = parser.parse_args()
    
    print("🚀 飞书多维表格批量视频工作流")
    print("=" * 60)
    
    # 加载配置
    if args.config:
        print(f"[INFO] 从配置文件加载: {args.config}")
        config = load_config_from_file(args.config)
        
        api_config = config.get("api_config", {})
        tables = config.get("tables", {})
        workflow_config = config.get("workflow_config", {})
        
        # 命令行参数优先
        app_id = args.app_id or api_config.get("app_id")
        app_secret = args.app_secret or api_config.get("app_secret")
        app_token = args.app_token or api_config.get("app_token")
        table_id = args.table_id or tables.get("content_table", {}).get("table_id")
        
        max_workers = args.max_workers or workflow_config.get("max_workers", 2)
        music_path = args.music_path or workflow_config.get("background_music_path")
        music_volume = args.music_volume or workflow_config.get("background_music_volume", 0.3)
        doubao_token = args.doubao_token or workflow_config.get("doubao_token")
        doubao_model = args.doubao_model or workflow_config.get("doubao_model")
        
    else:
        # 使用命令行参数
        if not all([args.app_id, args.app_secret, args.app_token, args.table_id]):
            print("[ERROR] 请提供配置文件或所有必需的命令行参数")
            parser.print_help()
            return
            
        app_id = args.app_id
        app_secret = args.app_secret
        app_token = args.app_token
        table_id = args.table_id
        max_workers = args.max_workers
        music_path = args.music_path
        music_volume = args.music_volume
        doubao_token = args.doubao_token
        doubao_model = args.doubao_model
        
        config = {}
    
    # 配置路径
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 创建工作流处理器
    workflow = FeishuBatchWorkflow(draft_folder_path, max_workers=max_workers)
    
    if args.config:
        # 使用配置文件设置所有配置
        workflow.set_config_from_dict(config)
        print("[INFO] 已从配置文件加载所有设置")
        
        # 检查是否启用了关联表查询
        has_relations = any([
            tables.get("account_table"),
            tables.get("voice_table"), 
            tables.get("digital_human_table")
        ])
        
        if not args.no_relations and has_relations:
            print("[INFO] 已启用关联表查询")
        else:
            print("[INFO] 关联表查询已禁用")
    else:
        # 使用命令行参数设置
        workflow.set_feishu_config(
            app_id=app_id,
            app_secret=app_secret,
            app_token=app_token,
            table_id=table_id
        )
        workflow.set_field_mapping(create_default_field_mapping())
        print("[INFO] 已使用命令行参数设置配置")
    
    # 设置豆包API
    workflow.set_doubao_api(doubao_token, doubao_model)
    
    # 设置背景音乐
    if music_path and os.path.exists(music_path):
        workflow.set_background_music(music_path, music_volume)
    else:
        # 尝试使用默认背景音乐
        default_music = os.path.join(os.path.dirname(__file__), '..', '华尔兹.mp3')
        if os.path.exists(default_music):
            workflow.set_background_music(default_music, music_volume)
    
    try:
        # 执行批量处理
        results = workflow.process_feishu_batch(
            filter_condition=create_default_filter(),
            include_ids=args.include,
            exclude_ids=args.exclude,
            save_tasks=not args.no_save
        )
        
        # 显示结果统计
        if results:
            success_count = len([r for r in results if r['status'] == 'success'])
            failed_count = len([r for r in results if r['status'] == 'failed'])
            error_count = len([r for r in results if r['status'] == 'error'])
            
            print(f"\n📊 处理结果统计:")
            print(f"✅ 成功: {success_count}")
            print(f"❌ 失败: {failed_count}")
            print(f"⚠️  错误: {error_count}")
            
        else:
            print("[INFO] 没有执行任何任务")
            
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断，程序退出")
    except Exception as e:
        print(f"\n[ERROR] 程序异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[INFO] 程序结束")


if __name__ == "__main__":
    main()