# -*- coding: utf-8 -*-
"""
异步Coze工作流处理器 - 分离式批量处理

核心特性：
1. 批量提交Coze工作流（最多16个并发）
2. 异步监听所有任务状态
3. 实时触发视频合成（一旦Coze返回立即处理）
4. 智能任务调度和错误恢复
"""

import asyncio
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import os
import sys

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from workflow.examples.coze_complete_video_workflow import CozeVideoWorkflow


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 待提交
    SUBMITTED = "submitted"      # 已提交Coze
    RUNNING = "running"         # Coze执行中
    COMPLETED = "completed"     # Coze已完成
    SYNTHESIZING = "synthesizing" # 视频合成中
    FINISHED = "finished"       # 全部完成
    FAILED = "failed"           # 失败


@dataclass
class AsyncCozeTask:
    """异步Coze任务数据结构"""
    task_id: str                    # 任务唯一ID
    content: str                    # 内容文案
    digital_no: str                 # 数字人编号
    voice_id: str                   # 声音ID
    title: str = ""                 # 标题
    project_name: str = ""          # 项目名称
    record_id: str = ""             # 飞书记录ID（用于状态更新）
    
    # 执行状态
    status: TaskStatus = TaskStatus.PENDING
    execute_id: Optional[str] = None  # Coze执行ID
    submit_time: Optional[datetime] = None
    complete_time: Optional[datetime] = None
    
    # 结果数据
    coze_result: Optional[Dict] = None
    video_path: Optional[str] = None
    error_message: Optional[str] = None
    
    # 重试机制
    retry_count: int = 0
    max_retries: int = 3


class AsyncCozeProcessor:
    """异步Coze处理器 - 高效批量处理"""
    
    def __init__(self, 
                 draft_folder_path: str,
                 coze_token: str,
                 workflow_id: str,
                 max_coze_concurrent: int = 16,
                 max_synthesis_workers: int = 4,
                 poll_interval: int = 30,
                 template_config: Dict[str, Any] = None):
        """初始化异步处理器
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            coze_token: Coze API令牌
            workflow_id: Coze工作流ID
            max_coze_concurrent: Coze最大并发数（默认16）
            max_synthesis_workers: 视频合成最大并发数（默认4）
            poll_interval: 轮询间隔秒数（默认30秒）
        """
        self.draft_folder_path = draft_folder_path
        self.coze_token = coze_token
        self.workflow_id = workflow_id
        self.max_coze_concurrent = max_coze_concurrent
        self.max_synthesis_workers = max_synthesis_workers
        self.poll_interval = poll_interval
        self.template_config = template_config or {}
        
        # 任务管理
        self.tasks: Dict[str, AsyncCozeTask] = {}
        self.task_lock = threading.RLock()
        
        # 执行统计
        self.stats = {
            'total_tasks': 0,
            'submitted_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 回调函数
        self.on_task_completed: Optional[Callable] = None
        self.on_task_failed: Optional[Callable] = None
        self.on_batch_finished: Optional[Callable] = None
        
        # 线程池
        self.coze_executor = ThreadPoolExecutor(max_workers=max_coze_concurrent)
        self.synthesis_executor = ThreadPoolExecutor(max_workers=max_synthesis_workers)
        
        # 监听控制
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Coze API配置
        self.coze_headers = {
            'Authorization': f'Bearer {coze_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"🚀 异步Coze处理器已初始化")
        print(f"   Coze并发数: {max_coze_concurrent}")
        print(f"   合成并发数: {max_synthesis_workers}")
        print(f"   轮询间隔: {poll_interval}秒")
    
    def add_task(self, task_id: str, content: str, digital_no: str, 
                 voice_id: str, title: str = "", project_name: str = "", record_id: str = "") -> None:
        """添加异步任务"""
        with self.task_lock:
            task = AsyncCozeTask(
                task_id=task_id,
                content=content,
                digital_no=digital_no,
                voice_id=voice_id,
                title=title or f"视频_{task_id}",
                project_name=project_name or f"项目_{task_id}",
                record_id=record_id
            )
            self.tasks[task_id] = task
            self.stats['total_tasks'] = len(self.tasks)
            print(f"✅ 任务已添加: {task_id} - {title[:20]}...")
    
    def add_tasks_batch(self, tasks_data: List[Dict[str, str]]) -> None:
        """批量添加任务"""
        print(f"📋 批量添加 {len(tasks_data)} 个任务...")
        for i, task_data in enumerate(tasks_data, 1):
            task_id = task_data.get('task_id', f'task_{i}')
            self.add_task(
                task_id=task_id,
                content=task_data['content'],
                digital_no=task_data['digital_no'],
                voice_id=task_data['voice_id'],
                title=task_data.get('title', ''),
                project_name=task_data.get('project_name', ''),
                record_id=task_data.get('record_id', '')
            )
        print(f"🎉 批量添加完成: {len(tasks_data)} 个任务")
    
    def submit_coze_workflow(self, task: AsyncCozeTask) -> Optional[str]:
        """提交单个Coze工作流"""
        try:
            url = "https://api.coze.cn/v1/workflow/run"
            
            parameters = {
                "content": task.content,
                "digitalNo": task.digital_no,
                "voiceId": task.voice_id,
                "title": task.title
            }
            
            payload = {
                "workflow_id": self.workflow_id,
                "parameters": parameters,
                "is_async": True
            }
            
            print(f"🚀 提交Coze工作流: {task.task_id} - {task.title[:20]}...")
            
            response = requests.post(url, headers=self.coze_headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            execute_id = result.get('execute_id')
            debug_url = result.get('debug_url')
            
            if execute_id:
                with self.task_lock:
                    task.execute_id = execute_id
                    task.status = TaskStatus.SUBMITTED
                    task.submit_time = datetime.now()
                    self.stats['submitted_tasks'] += 1
                
                print(f"✅ Coze提交成功: {task.task_id} -> {execute_id}")
                if debug_url:
                    print(f"🔍 调试URL: {debug_url}")
                return execute_id
            else:
                raise Exception(f"未获取到execute_id: {result}")
                
        except Exception as e:
            error_msg = f"Coze提交失败: {e}"
            print(f"❌ {error_msg} - 任务: {task.task_id}")
            
            with self.task_lock:
                task.status = TaskStatus.FAILED
                task.error_message = error_msg
                self.stats['failed_tasks'] += 1
            
            if self.on_task_failed:
                self.on_task_failed(task, error_msg)
            
            return None
    
    def check_coze_result(self, task: AsyncCozeTask) -> Optional[Dict]:
        """检查Coze工作流结果 - 参考已有的实现"""
        if not task.execute_id:
            return None
            
        try:
            url = f"https://api.coze.cn/v1/workflows/{self.workflow_id}/run_histories/{task.execute_id}"
            
            response = requests.get(url, headers=self.coze_headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") == 0:
                data_array = result.get("data")
                if data_array and isinstance(data_array, list) and len(data_array) > 0:
                    # 获取最新的执行记录
                    execution_record = data_array[0]
                    execute_status = execution_record.get("execute_status")
                    
                    if execute_status == "Success":
                        # 解析输出数据
                        output_str = execution_record.get("output")
                        if output_str:
                            try:
                                output_data = json.loads(output_str)
                                # 工作流已完成
                                with self.task_lock:
                                    task.status = TaskStatus.COMPLETED
                                    task.complete_time = datetime.now()
                                    task.coze_result = output_data
                                    self.stats['completed_tasks'] += 1
                                
                                duration = task.complete_time - task.submit_time
                                print(f"🎉 Coze完成: {task.task_id} (耗时: {duration})")
                                
                                return task.coze_result
                            except json.JSONDecodeError as e:
                                error_msg = f"输出数据解析失败: {e}"
                                with self.task_lock:
                                    task.status = TaskStatus.FAILED
                                    task.error_message = error_msg
                                    self.stats['failed_tasks'] += 1
                                print(f"❌ {error_msg} - 任务: {task.task_id}")
                                return None
                        else:
                            error_msg = "工作流完成但无输出数据"
                            with self.task_lock:
                                task.status = TaskStatus.FAILED
                                task.error_message = error_msg
                                self.stats['failed_tasks'] += 1
                            print(f"❌ {error_msg} - 任务: {task.task_id}")
                            return None
                    elif execute_status == "Failed":
                        error_code = execution_record.get("error_code", "未知错误")
                        error_message = execution_record.get("error_message", "")
                        error_msg = f"Coze执行失败: {error_code} - {error_message}"
                        
                        with self.task_lock:
                            task.status = TaskStatus.FAILED
                            task.error_message = error_msg
                            self.stats['failed_tasks'] += 1
                        
                        print(f"❌ {error_msg} - 任务: {task.task_id}")
                        
                        if self.on_task_failed:
                            self.on_task_failed(task, error_msg)
                        
                        return None
                    elif execute_status == "Running":
                        # 仍在运行中
                        if task.status != TaskStatus.RUNNING:
                            with self.task_lock:
                                task.status = TaskStatus.RUNNING
                            print(f"🔄 Coze运行中: {task.task_id}")
                        return None
                    else:
                        # 其他状态
                        if task.status != TaskStatus.RUNNING:
                            with self.task_lock:
                                task.status = TaskStatus.RUNNING
                            print(f"🔄 Coze状态: {task.task_id} - {execute_status}")
                        return None
                else:
                    # 暂无执行记录
                    if task.status != TaskStatus.RUNNING:
                        with self.task_lock:
                            task.status = TaskStatus.RUNNING
                        print(f"🔄 Coze等待中: {task.task_id}")
                    return None
            else:
                error_msg = result.get('msg', '轮询出错')
                print(f"❌ 轮询出错: {error_msg} - 任务: {task.task_id}")
                return None
                
        except Exception as e:
            print(f"⚠️ 检查Coze结果异常: {e} - 任务: {task.task_id}")
            return None
    
    def synthesize_video_async(self, task: AsyncCozeTask) -> None:
        """异步视频合成"""
        try:
            with self.task_lock:
                task.status = TaskStatus.SYNTHESIZING
            
            print(f"🎬 开始视频合成: {task.task_id}")
            
            # 创建CozeVideoWorkflow实例
            workflow = CozeVideoWorkflow(
                draft_folder_path=self.draft_folder_path,
                project_name=task.project_name,
                template_config=self.template_config
            )
            
            # 设置任务配置（synthesize_video方法需要）
            workflow.task_config = {
                "content": task.content,
                "digital_no": task.digital_no,
                "voice_id": task.voice_id,
                "title": task.title,
            }
            
            # 直接使用Coze结果进行视频合成
            video_path = workflow.synthesize_video(task.coze_result)
            
            if video_path:
                with self.task_lock:
                    task.status = TaskStatus.FINISHED
                    task.video_path = video_path
                
                print(f"🎉 视频合成完成: {task.task_id} -> {video_path}")
                
                if self.on_task_completed:
                    self.on_task_completed(task)
            else:
                raise Exception("视频合成返回空路径")
                
        except Exception as e:
            error_msg = f"视频合成失败: {e}"
            print(f"❌ {error_msg} - 任务: {task.task_id}")
            
            with self.task_lock:
                task.status = TaskStatus.FAILED
                task.error_message = error_msg
                self.stats['failed_tasks'] += 1
            
            if self.on_task_failed:
                self.on_task_failed(task, error_msg)
    
    def start_batch_processing(self) -> None:
        """开始批量处理"""
        if not self.tasks:
            print("⚠️ 没有任务需要处理")
            return
        
        print(f"\n🚀 开始批量异步处理")
        print(f"📊 任务总数: {len(self.tasks)}")
        print(f"🔥 Coze并发: {self.max_coze_concurrent}")
        print(f"🎬 合成并发: {self.max_synthesis_workers}")
        print("=" * 60)
        
        self.stats['start_time'] = datetime.now()
        
        # 阶段1: 批量提交Coze工作流
        self._batch_submit_coze()
        
        # 阶段2: 启动监听和合成
        self._start_monitoring()
        
        print(f"✅ 批量处理已启动")
    
    def _batch_submit_coze(self) -> None:
        """批量提交Coze工作流"""
        print(f"\n📤 阶段1: 批量提交Coze工作流...")
        
        pending_tasks = [task for task in self.tasks.values() if task.status == TaskStatus.PENDING]
        
        print(f"📋 准备提交 {len(pending_tasks)} 个任务")
        
        # 使用线程池并发提交
        future_to_task = {}
        with ThreadPoolExecutor(max_workers=self.max_coze_concurrent) as executor:
            for task in pending_tasks:
                future = executor.submit(self.submit_coze_workflow, task)
                future_to_task[future] = task
            
            # 等待所有提交完成
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    execute_id = future.result()
                    # 结果已在submit_coze_workflow中处理
                except Exception as e:
                    print(f"❌ 提交异常: {e} - 任务: {task.task_id}")
        
        submitted_count = len([t for t in self.tasks.values() if t.status == TaskStatus.SUBMITTED])
        print(f"✅ 阶段1完成: 成功提交 {submitted_count}/{len(pending_tasks)} 个任务")
    
    def _start_monitoring(self) -> None:
        """启动监听线程"""
        print(f"\n👁️ 阶段2: 启动智能监听和实时合成...")
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        print(f"✅ 监听线程已启动")
    
    def _monitoring_loop(self) -> None:
        """监听循环"""
        print(f"🔄 开始监听循环，间隔: {self.poll_interval}秒")
        
        while self.is_monitoring:
            try:
                # 检查所有提交或运行中的任务
                tasks_to_check = [
                    task for task in self.tasks.values() 
                    if task.status in [TaskStatus.SUBMITTED, TaskStatus.RUNNING]
                ]
                
                if not tasks_to_check:
                    # 检查是否所有任务都完成
                    active_tasks = [
                        task for task in self.tasks.values()
                        if task.status in [TaskStatus.PENDING, TaskStatus.SUBMITTED, 
                                         TaskStatus.RUNNING, TaskStatus.SYNTHESIZING]
                    ]
                    
                    if not active_tasks:
                        print(f"🎉 所有任务已完成，停止监听")
                        self._finish_batch_processing()
                        break
                    
                    time.sleep(self.poll_interval)
                    continue
                
                print(f"🔍 检查 {len(tasks_to_check)} 个任务状态...")
                
                # 并发检查任务状态
                with ThreadPoolExecutor(max_workers=8) as executor:
                    future_to_task = {
                        executor.submit(self.check_coze_result, task): task
                        for task in tasks_to_check
                    }
                    
                    completed_tasks = []
                    for future in as_completed(future_to_task):
                        task = future_to_task[future]
                        try:
                            coze_result = future.result()
                            if coze_result and task.status == TaskStatus.COMPLETED:
                                completed_tasks.append(task)
                        except Exception as e:
                            print(f"⚠️ 状态检查异常: {e} - 任务: {task.task_id}")
                    
                    # 立即触发已完成任务的视频合成
                    if completed_tasks:
                        print(f"🎬 发现 {len(completed_tasks)} 个已完成任务，立即触发视频合成")
                        print(f"任务： {completed_tasks}")
                        for task in completed_tasks:
                            self.synthesis_executor.submit(self.synthesize_video_async, task)
                
                # 打印进度统计
                self._print_progress()
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"❌ 监听循环异常: {e}")
                time.sleep(self.poll_interval)
    
    def _print_progress(self) -> None:
        """打印进度统计"""
        with self.task_lock:
            status_counts = {}
            for task in self.tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
        
        total = len(self.tasks)
        finished = status_counts.get('finished', 0)
        failed = status_counts.get('failed', 0)
        
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"📊 进度: {finished}/{total} 完成, {failed} 失败, 耗时: {elapsed}")
        print(f"   状态分布: {status_counts}")
    
    def _finish_batch_processing(self) -> None:
        """完成批量处理"""
        self.is_monitoring = False
        self.stats['end_time'] = datetime.now()
        
        # 等待合成线程池完成
        self.synthesis_executor.shutdown(wait=True)
        self.coze_executor.shutdown(wait=True)
        
        print(f"\n🎉 批量异步处理完成!")
        self._print_final_statistics()
        
        if self.on_batch_finished:
            self.on_batch_finished(self.stats)
    
    def _print_final_statistics(self) -> None:
        """打印最终统计"""
        total_time = self.stats['end_time'] - self.stats['start_time']
        
        finished_count = len([t for t in self.tasks.values() if t.status == TaskStatus.FINISHED])
        failed_count = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        
        print(f"📊 最终统计:")
        print(f"   总任务数: {len(self.tasks)}")
        print(f"   成功完成: {finished_count}")
        print(f"   处理失败: {failed_count}")
        print(f"   成功率: {finished_count/len(self.tasks)*100:.1f}%")
        print(f"   总耗时: {total_time}")
        print(f"   平均耗时: {total_time/len(self.tasks) if self.tasks else 0}")
    
    def wait_for_completion(self) -> Dict[str, Any]:
        """等待所有任务完成"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join()
        
        return self.get_results()
    
    def get_results(self) -> Dict[str, Any]:
        """获取所有结果"""
        with self.task_lock:
            results = {
                'tasks': {task_id: asdict(task) for task_id, task in self.tasks.items()},
                'statistics': self.stats.copy()
            }
        return results
    
    def save_results(self, output_path: str) -> None:
        """保存结果到文件"""
        results = self.get_results()
        
        # 处理datetime对象
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, TaskStatus):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=datetime_handler)
        
        print(f"💾 结果已保存: {output_path}")
    
    def stop(self) -> None:
        """停止处理"""
        print(f"🛑 停止异步处理...")
        self.is_monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.synthesis_executor.shutdown(wait=False)
        self.coze_executor.shutdown(wait=False)


# 使用示例和测试函数
def create_sample_tasks() -> List[Dict[str, str]]:
    """创建示例任务"""
    return [
        {
            'task_id': 'demo_1',
            'content': '测试内容1：AI技术的发展前景',
            'digital_no': 'digital_001',
            'voice_id': 'voice_001',
            'title': '测试标题1',
            'project_name': '异步处理测试1'
        },
        {
            'task_id': 'demo_2', 
            'content': '测试内容2：未来科技趋势分析',
            'digital_no': 'digital_002',
            'voice_id': 'voice_002',
            'title': '测试标题2',
            'project_name': '异步处理测试2'
        }
    ]


if __name__ == "__main__":
    # 测试用例
    print("🧪 异步Coze处理器测试")
    
    # 配置参数
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    coze_token = "your_coze_token"
    workflow_id = "your_workflow_id"
    
    # 创建异步处理器
    processor = AsyncCozeProcessor(
        draft_folder_path=draft_folder_path,
        coze_token=coze_token,
        workflow_id=workflow_id,
        max_coze_concurrent=16,
        max_synthesis_workers=4,
        poll_interval=30
    )
    
    # 添加测试任务
    sample_tasks = create_sample_tasks()
    processor.add_tasks_batch(sample_tasks)
    
    # 设置回调函数
    def on_task_completed(task: AsyncCozeTask):
        print(f"🎉 任务完成回调: {task.task_id} -> {task.video_path}")
    
    def on_task_failed(task: AsyncCozeTask, error: str):
        print(f"❌ 任务失败回调: {task.task_id} -> {error}")
    
    def on_batch_finished(stats: Dict):
        print(f"🏁 批量处理完成回调: {stats}")
    
    processor.on_task_completed = on_task_completed
    processor.on_task_failed = on_task_failed
    processor.on_batch_finished = on_batch_finished
    
    # 开始处理
    processor.start_batch_processing()
    
    # 等待完成
    results = processor.wait_for_completion()
    
    # 保存结果
    output_path = f"async_coze_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    processor.save_results(output_path)
    
    print(f"✅ 异步处理测试完成")