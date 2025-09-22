# -*- coding: utf-8 -*-
"""
飞书异步批量工作流 - 高效并发处理版本

核心优化：
1. 分离Coze调用和视频合成（异步处理）
2. 最大化Coze API并发利用率（16个并发）
3. 实时监听和处理，一有结果立即合成视频
4. 智能任务调度和错误恢复
"""

import sys
import os
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from unittest import result

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 导入现有组件
from workflow.feishu_client import FeishuVideoTaskSource
from workflow.async_coze_processor import AsyncCozeProcessor, AsyncCozeTask


class FeishuAsyncBatchWorkflow:
    """飞书异步批量工作流处理器"""
    
    def __init__(self, config: Dict[str, Any], log_callback=None):
        """初始化飞书异步批量工作流

        Args:
            config: 配置字典，包含飞书API、Coze API等配置
            log_callback: 日志回调函数
        """
        self.config = config
        
        # 飞书配置
        self.feishu_config = config.get('api_config', {})
        self.tables_config = config.get('tables', {})
        self.workflow_config = config.get('workflow_config', {})
        self.template_config = config.get('template_config', {})
        
        # 剪映草稿路径
        self.draft_folder_path = self.workflow_config.get(
            'draft_folder_path', 
            r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
        )
        
        # Coze配置
        coze_config = self.workflow_config.get('coze_config', {})
        self.coze_token = coze_config.get('token', '')
        self.coze_workflow_id = coze_config.get('workflow_id', '')
        
        # 并发配置
        self.max_coze_concurrent = self.workflow_config.get('max_coze_concurrent', 16)
        self.max_synthesis_workers = self.workflow_config.get('max_synthesis_workers', 4)
        self.poll_interval = self.workflow_config.get('poll_interval', 30)

        # 日志回调
        self.log_callback = log_callback

        # 初始化飞书客户端
        self.feishu_task_source = None
        
        # 初始化异步处理器
        self.async_processor = None
        self._init_async_processor()
        
        self.log_message(f"🚀 飞书异步批量工作流已初始化")
        self.log_message(f"   Coze并发数: {self.max_coze_concurrent}")
        self.log_message(f"   合成并发数: {self.max_synthesis_workers}")

    def log_message(self, message: str):
        """记录日志消息"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def _init_feishu_client(self) -> None:
        """初始化飞书客户端"""
        if self.feishu_task_source:
            return
            
        self.log_message(f"📡 初始化飞书客户端...")
        
        # 从content_table配置中提取table_id和field_mapping
        content_table_config = self.tables_config.get('content_table', {})
        table_id = content_table_config.get('table_id', '')
        field_mapping = content_table_config.get('field_mapping', {})
        
        self.feishu_task_source = FeishuVideoTaskSource(
            app_id=self.feishu_config['app_id'],
            app_secret=self.feishu_config['app_secret'],
            app_token=self.feishu_config['app_token'],
            table_id=table_id,
            field_mapping=field_mapping,
            account_table_config=self.tables_config.get('account_table'),
            voice_table_config=self.tables_config.get('voice_table'),
            digital_human_table_config=self.tables_config.get('digital_human_table')
        )
        
        self.log_message(f"✅ 飞书客户端初始化完成")
    
    def _init_async_processor(self) -> None:
        """初始化异步处理器"""
        if self.async_processor:
            return
            
        self.log_message(f"⚡ 初始化异步Coze处理器...")
        
        self.async_processor = AsyncCozeProcessor(
            draft_folder_path=self.draft_folder_path,
            coze_token=self.coze_token,
            workflow_id=self.coze_workflow_id,
            max_coze_concurrent=self.max_coze_concurrent,
            max_synthesis_workers=self.max_synthesis_workers,
            poll_interval=self.poll_interval,
            template_config=self.template_config,
            log_callback=self.log_message
        )
        
        # 设置回调函数
        self.async_processor.on_task_completed = self._on_task_completed
        self.async_processor.on_task_failed = self._on_task_failed
        self.async_processor.on_batch_finished = self._on_batch_finished
        
        self.log_message(f"✅ 异步处理器初始化完成")
    
    def _on_task_completed(self, task: AsyncCozeTask) -> None:
        """任务完成回调"""
        self.log_message(f"🎉 任务完成: {task.task_id} - {task.title}")
        self.log_message(f"   视频路径: {task.video_path}")
        
        # 更新飞书状态
        self._update_feishu_status(task, "视频草稿生成完成", task.video_path)
    
    def _on_task_failed(self, task: AsyncCozeTask, error: str) -> None:
        """任务失败回调"""
        self.log_message(f"❌ 任务失败: {task.task_id} - {error}")
        
        # 更新飞书状态
        self._update_feishu_status(task, "处理失败", error_message=error)
    
    def _on_batch_finished(self, stats: Dict) -> None:
        """批量处理完成回调"""
        total_time = stats.get('end_time') - stats.get('start_time')
        self.log_message(f"🏁 批量处理完成!")
        self.log_message(f"   总耗时: {total_time}")
        
        # 发送完成通知或执行其他收尾工作
    
    def load_tasks_from_feishu(self, filter_condition: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """从飞书加载任务数据"""
        self._init_feishu_client()

        print(f"📋 从飞书多维表格加载任务...")

        # 内置过滤条件：只获取状态为"视频草稿生成"的记录
        built_in_filter = {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": "状态",
                    "operator": "is",
                    "value": ["视频草稿生成"]
                }
            ]
        }

        # 如果传入了filter_condition参数，则使用它；否则使用内置过滤条件
        actual_filter = filter_condition or built_in_filter

        # 加载任务
        tasks = self.feishu_task_source.get_tasks(actual_filter)

        print(f"✅ 从飞书加载了 {len(tasks)} 个任务")

        return tasks
    
    def convert_feishu_tasks_to_coze_tasks(self, feishu_tasks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """将飞书任务转换为Coze任务格式"""
        coze_tasks = []
        
        for i, task in enumerate(feishu_tasks, 1):
            # 从飞书任务中提取必要字段
            task_id = f'task_{i}'
            feishu_record_id = task.get('feishu_record_id', '')
            content = task.get('content', '')
            title = task.get('title', f'视频_{i}')
            project_name = task.get('project_name', f'项目_{i}')
            digital_no = task.get('digital_no', 'default_digital')
            voice_id = task.get('voice_id', 'default_voice')
            account_id = task.get('account_id', '')  # 使用正确的字段名
            
            if not content:
                print(f"⚠️ 跳过空内容任务: {task_id}")
                continue
                
            if not feishu_record_id:
                print(f"⚠️ 跳过无飞书记录ID的任务: {task_id}")
                continue
            
            coze_task = {
                'task_id': task_id,
                'content': content,
                'title': title,
                'project_name': project_name,
                'digital_no': digital_no,
                'voice_id': voice_id,
                'account_id': account_id,  # 使用正确的字段名
                'record_id': feishu_record_id,  # 使用飞书记录ID
                'original_task': task  # 保留原始任务数据
            }
            
            coze_tasks.append(coze_task)
        
        print(f"🔄 转换了 {len(coze_tasks)} 个有效任务")
        
        return coze_tasks
    
    def _update_feishu_status(self, task: AsyncCozeTask, status: str, video_path: str = None, error_message: str = None) -> None:
        """更新飞书记录状态
        
        Args:
            task: 任务对象
            status: 新状态
            video_path: 视频路径（可选）
            error_message: 错误信息（可选）
        """
        if not task.record_id:
            print(f"⚠️ 任务 {task.task_id} 没有记录ID，跳过飞书状态更新")
            return
            
        print(f"🔄 正在更新飞书状态: 记录ID={task.record_id}, 状态={status}")
            
        try:
            # 构建更新字段 - 使用配置中的字段映射
            field_mapping = self.tables_config.get('content_table', {}).get('field_mapping', {})
            
            # 尝试使用配置中的字段名，如果没有则使用默认值
            status_field = field_mapping.get('status', '状态')
            result_field = field_mapping.get('result ', '返回结果')
            
            update_fields = {
                status_field: status
            }
            
            # 如果有视频路径，更新视频路径字段
            if video_path:
                update_fields[result_field] = video_path
                
            # 如果有错误信息，更新错误信息字段
            if error_message:
                update_fields[result_field] = error_message
                
            print(f"📝 更新字段: {update_fields}")
                
            # 更新记录
            success = self.feishu_task_source.update_record_fields(task.record_id, update_fields)
            
            if success:
                print(f"✅ 飞书状态更新成功: {task.task_id} -> {status}")
            else:
                print(f"❌ 飞书状态更新失败: {task.task_id}")
                
        except Exception as e:
            print(f"❌ 飞书状态更新异常: {task.task_id} - {e}")
            import traceback
            traceback.print_exc()
    
    def process_async_batch(self,
                           include_ids: List[str] = None,
                           exclude_ids: List[str] = None,
                           save_results: bool = True,
                           filter_condition: Optional[Dict] = None) -> Dict[str, Any]:
        """异步批量处理飞书任务

        Args:
            include_ids: 包含的任务ID列表
            exclude_ids: 排除的任务ID列表
            save_results: 是否保存结果

        Returns:
            处理结果统计
        """
        print(f"\n🚀 开始飞书异步批量处理")
        print(f"=" * 60)
        
        # 1. 从飞书加载任务（支持传入过滤条件，默认使用内置条件）
        feishu_tasks = self.load_tasks_from_feishu(filter_condition)
        
        if not feishu_tasks:
            print(f"⚠️ 没有找到符合条件的任务")
            return {'success': False, 'message': '没有任务需要处理'}
        
        # 2. 应用包含/排除过滤
        if include_ids:
            feishu_tasks = [t for t in feishu_tasks if t.get('record_id') in include_ids]
            print(f"🎯 应用包含过滤，剩余 {len(feishu_tasks)} 个任务")
        
        if exclude_ids:
            feishu_tasks = [t for t in feishu_tasks if t.get('record_id') not in exclude_ids]
            print(f"🚫 应用排除过滤，剩余 {len(feishu_tasks)} 个任务")
        
        # 3. 转换为Coze任务格式
        coze_tasks = self.convert_feishu_tasks_to_coze_tasks(feishu_tasks)
        
        if not coze_tasks:
            print(f"⚠️ 没有有效的任务可以处理")
            return {'success': False, 'message': '没有有效任务'}
        
        # 4. 初始化异步处理器
        self._init_async_processor()
        
        # 5. 添加任务到异步处理器
        self.async_processor.add_tasks_batch(coze_tasks)
        
        # 6. 开始异步批量处理
        self.async_processor.start_batch_processing()
        
        # 7. 等待所有任务完成
        print(f"⏳ 等待所有任务完成...")
        results = self.async_processor.wait_for_completion()
        
        # 8. 保存结果
        if save_results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"feishu_async_results_{timestamp}.json"
            self.async_processor.save_results(output_path)
        
        # 9. 返回统计结果
        statistics = results.get('statistics', {})
        tasks_data = results.get('tasks', {})
        
        finished_count = len([t for t in tasks_data.values() if t.get('status') == 'finished'])
        failed_count = len([t for t in tasks_data.values() if t.get('status') == 'failed'])
        
        final_result = {
            'success': True,
            'total_tasks': len(coze_tasks),
            'finished_tasks': finished_count,
            'failed_tasks': failed_count,
            'success_rate': finished_count / len(coze_tasks) * 100 if coze_tasks else 0,
            'total_time': statistics.get('end_time', datetime.now()) - statistics.get('start_time', datetime.now()),
            'detailed_results': results
        }
        
        print(f"\n🎉 飞书异步批量处理完成!")
        print(f"📊 成功率: {final_result['success_rate']:.1f}% ({finished_count}/{len(coze_tasks)})")
        print(f"⏱️ 总耗时: {final_result['total_time']}")
        
        return final_result


def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config




def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='飞书异步批量工作流')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--include', nargs='*', help='包含的任务ID列表')
    parser.add_argument('--exclude', nargs='*', help='排除的任务ID列表')
    parser.add_argument('--no-save', action='store_true', help='不保存结果到文件')
    parser.add_argument('--max-coze', type=int, default=16, help='Coze最大并发数')
    parser.add_argument('--max-synthesis', type=int, default=4, help='视频合成最大并发数')
    parser.add_argument('--poll-interval', type=int, default=30, help='轮询间隔(秒)')
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        print(f"📋 加载配置文件: {args.config}")
        config = load_config(args.config)
        
        # 应用命令行参数覆盖
        workflow_config = config.setdefault('workflow_config', {})
        if args.max_coze:
            workflow_config['max_coze_concurrent'] = args.max_coze
        if args.max_synthesis:
            workflow_config['max_synthesis_workers'] = args.max_synthesis
        if args.poll_interval:
            workflow_config['poll_interval'] = args.poll_interval
        
        # 创建工作流实例
        workflow = FeishuAsyncBatchWorkflow(config)
        
        # 执行异步批量处理（过滤条件已内置到代码中）
        results = workflow.process_async_batch(
            include_ids=args.include,
            exclude_ids=args.exclude,
            save_results=not args.no_save
        )
        
        print(f"\\n✅ 飞书异步批量工作流执行完成")
        # print(f"📊 处理结果: {results}")
        
    except KeyboardInterrupt:
        print(f"\\n⚠️ 用户中断执行")
    except Exception as e:
        print(f"\\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()