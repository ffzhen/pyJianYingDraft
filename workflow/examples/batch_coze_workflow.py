#!/usr/bin/env python3
"""
批量处理Coze视频工作流

支持并发处理多个视频任务，提高处理效率
"""

import sys
import os
import json
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from workflow.examples.coze_complete_video_workflow import CozeVideoWorkflow, log_with_time


class BatchCozeWorkflow:
    """批量Coze视频工作流处理器"""
    
    def __init__(self, draft_folder_path: str, max_workers: int = 3):
        """初始化批量处理器
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            max_workers: 最大并发数（建议2-3，避免API限制）
        """
        self.draft_folder_path = draft_folder_path
        self.max_workers = max_workers
        self.results = []
        self.lock = threading.Lock()
        
        # 全局配置
        self.background_music_path = None
        self.background_music_volume = 0.3
        self.doubao_token = 'adac0afb-5fd4-4c66-badb-370a7ff42df5'
        self.doubao_model = 'ep-m-20250902010446-mlwmf'
        
        # 飞书状态更新配置
        self.feishu_task_source = None
        
    def set_background_music(self, music_path: str, volume: float = 0.3):
        """设置背景音乐"""
        if not os.path.exists(music_path):
            print(f"[WARN] 背景音乐文件不存在: {music_path}")
            return
        
        self.background_music_path = music_path
        self.background_music_volume = volume
        print(f"[INFO] 背景音乐已设置: {os.path.basename(music_path)}")
    
    def set_feishu_task_source(self, task_source):
        """设置飞书任务源，用于状态更新"""
        self.feishu_task_source = task_source
        print("[INFO] 飞书任务源已设置，将启用状态更新功能")
    
    def set_doubao_api(self, token: str, model: str):
        """设置豆包API配置"""
        self.doubao_token = token
        self.doubao_model = model
        print(f"[INFO] 豆包API已设置: {model}")
    
    def process_single_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            处理结果
        """
        task_id = task_data.get('id', 'unknown')
        content = task_data.get('content')
        digital_no = task_data.get('digital_no')
        voice_id = task_data.get('voice_id')
        title = task_data.get('title')
        feishu_record_id = task_data.get('feishu_record_id')
        
        print(f"[{task_id}] 开始处理任务: {title}")
        start_time = datetime.now()
        
        try:
            # 创建工作流实例，直接使用title作为项目名称
            workflow = CozeVideoWorkflow(self.draft_folder_path)
            
            # 设置API配置
            workflow.set_doubao_api(self.doubao_token, self.doubao_model)
            
            # 设置背景音乐
            if self.background_music_path:
                workflow.set_background_music(self.background_music_path, self.background_music_volume)
            
            # 执行工作流
            result = workflow.run_complete_workflow(content, digital_no, voice_id, title)
            
            # 记录结果
            task_result = {
                'task_id': task_id,
                'title': title,
                'status': 'success' if result else 'failed',
                'result': result,
                'duration': (datetime.now() - start_time).total_seconds(),
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with self.lock:
                self.results.append(task_result)
            
            print(f"[{task_id}] 任务完成: {title} - {'成功' if result else '失败'}")
            if result:
                print(f"[{task_id}] 输出路径: {result}")
                
                # 更新飞书记录状态
                if self.feishu_task_source and feishu_record_id:
                    try:
                        success = self.feishu_task_source.update_record_status(
                            feishu_record_id, "视频生成完成"
                        )
                        if success:
                            print(f"[{task_id}] ✅ 飞书记录状态已更新: 视频生成完成")
                        else:
                            print(f"[{task_id}] ⚠️ 飞书记录状态更新失败")
                    except Exception as update_error:
                        print(f"[{task_id}] ⚠️ 更新飞书记录状态时出错: {update_error}")
            
            return task_result
            
        except Exception as e:
            print(f"[{task_id}] 任务失败: {title} - {e}")
            
            # 记录失败结果
            task_result = {
                'task_id': task_id,
                'title': title,
                'status': 'error',
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds(),
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with self.lock:
                self.results.append(task_result)
            
            # 更新飞书记录状态为失败
            if self.feishu_task_source and feishu_record_id:
                try:
                    success = self.feishu_task_source.update_record_status(
                        feishu_record_id, "视频生成失败"
                    )
                    if success:
                        print(f"[{task_id}] ✅ 飞书记录状态已更新: 视频生成失败")
                    else:
                        print(f"[{task_id}] ⚠️ 飞书记录状态更新失败")
                except Exception as update_error:
                    print(f"[{task_id}] ⚠️ 更新飞书记录状态时出错: {update_error}")
            
            return task_result
    
    def filter_tasks(self, tasks: List[Dict[str, Any]], 
                   include_ids: List[str] = None, 
                   exclude_ids: List[str] = None) -> List[Dict[str, Any]]:
        """过滤任务列表
        
        Args:
            tasks: 原始任务列表
            include_ids: 包含的任务ID列表（如果指定，只处理这些任务）
            exclude_ids: 排除的任务ID列表（如果指定，跳过这些任务）
            
        Returns:
            过滤后的任务列表
        """
        filtered_tasks = tasks.copy()
        
        if include_ids:
            # 只处理指定的任务
            filtered_tasks = [task for task in filtered_tasks if task.get('id') in include_ids]
            print(f"[INFO] 只处理指定的任务: {include_ids}")
        
        if exclude_ids:
            # 跳过指定的任务
            filtered_tasks = [task for task in filtered_tasks if task.get('id') not in exclude_ids]
            print(f"[INFO] 跳过指定的任务: {exclude_ids}")
        
        return filtered_tasks
    
    def process_batch(self, tasks: List[Dict[str, Any]], 
                     include_ids: List[str] = None, 
                     exclude_ids: List[str] = None) -> List[Dict[str, Any]]:
        """批量处理任务
        
        Args:
            tasks: 任务列表
            include_ids: 包含的任务ID列表（如果指定，只处理这些任务）
            exclude_ids: 排除的任务ID列表（如果指定，跳过这些任务）
            
        Returns:
            处理结果列表
        """
        # 过滤任务
        filtered_tasks = self.filter_tasks(tasks, include_ids, exclude_ids)
        
        if not filtered_tasks:
            print("[WARN] 没有可执行的任务")
            return []
        
        print(f"[INFO] 开始批量处理 {len(filtered_tasks)} 个任务，最大并发数: {self.max_workers}")
        print(f"[INFO] 预计总时间: {len(filtered_tasks) * 15} 分钟（每个任务约15分钟）")
        
        start_time = datetime.now()
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self.process_single_task, task): task 
                for task in filtered_tasks
            }
            
            print(f"[DEBUG] 已提交 {len(future_to_task)} 个任务到线程池")
            
            # 收集结果
            completed_count = 0
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                completed_count += 1
                try:
                    result = future.result()
                    print(f"[DEBUG] 任务 {completed_count}/{len(future_to_task)} 完成: {task.get('title', 'unknown')}")
                    # 结果已经在process_single_task中记录
                except Exception as e:
                    print(f"[ERROR] 任务执行异常: {task.get('title', 'unknown')} - {e}")
            
            print(f"[DEBUG] 所有任务已完成，线程池即将关闭")
        
        # 统计结果
        success_count = len([r for r in self.results if r['status'] == 'success'])
        failed_count = len([r for r in self.results if r['status'] == 'failed'])
        error_count = len([r for r in self.results if r['status'] == 'error'])
        
        total_duration = (datetime.now() - start_time).total_seconds()
        
        # 计算成功任务的平均处理时间
        successful_tasks = [r for r in self.results if r['status'] == 'success']
        if successful_tasks:
            avg_task_duration = sum(r['duration'] for r in successful_tasks) / len(successful_tasks)
            # 格式化时间为分钟和秒
            total_minutes = int(total_duration // 60)
            total_seconds = int(total_duration % 60)
            avg_minutes = int(avg_task_duration // 60)
            avg_seconds = int(avg_task_duration % 60)
        else:
            avg_task_duration = 0
            total_minutes = int(total_duration // 60)
            total_seconds = int(total_duration % 60)
            avg_minutes = 0
            avg_seconds = 0
        
        print(f"\n{'='*60}")
        print(f"[INFO] 批量处理完成!")
        print(f"[INFO] 总任务数: {len(filtered_tasks)}")
        print(f"[INFO] 成功: {success_count}")
        print(f"[INFO] 失败: {failed_count}")
        print(f"[INFO] 错误: {error_count}")
        print(f"[INFO] 批处理完成总时间: {total_minutes}分{total_seconds}秒")
        if successful_tasks:
            print(f"[INFO] 平均任务处理时间: {avg_minutes}分{avg_seconds}秒")
            print(f"[INFO] 并发效率提升: {len(successful_tasks) * avg_task_duration / total_duration:.1f}x")
        print(f"{'='*60}")
        
        return self.results
    
    def save_results(self, output_file: str = 'batch_results.json'):
        """保存结果到文件
        
        Args:
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 结果已保存到: {output_file}")


def load_tasks_from_json(json_file: str) -> List[Dict[str, Any]]:
    """从JSON文件加载任务列表
    
    Args:
        json_file: JSON文件路径
        
    Returns:
        任务列表
    """
    if not os.path.exists(json_file):
        raise FileNotFoundError(f"任务文件不存在: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    print(f"[INFO] 从 {json_file} 加载了 {len(tasks)} 个任务")
    return tasks


def create_sample_tasks():
    """创建示例任务列表"""
    return [
        {
            "id": "task_001",
            "title": "未来中国可能出现的九大变化",
            "content": "未来中国有可能出现九大现象。第一个，手机有可能会消失，燃油车可能会被淘汰，人民币已逐渐数字化。第四，孩子国家统一给一套房。第五，全民医疗免费。第六，房子太便宜没人要。第七，将来飞行汽车将会越来越多，不会为堵车而发愁。第八，高科技替代劳动力。第九，人均寿命可以达到100岁以上。你觉得哪个会成为现实呢？",
            "digital_no": "D20250820190000004",
            "voice_id": "AA20250822120001",
            "project_name": "future_china_changes"
        },
        {
            "id": "task_002", 
            "title": "美貌对穷人而言真的是灾难吗",
            "content": "为什么女孩越漂亮越应该好好读书，有个作家说我美貌对于富人来说是锦上添花，对于中产来说是一笔财富，但对于穷人来说就是灾难。",
            "digital_no": "D20250820190000004",
            "voice_id": "AA20250822120001",
            "project_name": "beauty_and_poverty"
        },
        {
            "id": "task_003",
            "title": "人工智能时代的就业挑战",
            "content": "随着人工智能技术的快速发展，许多传统工作岗位面临被替代的风险。我们需要思考如何在AI时代保持竞争力，以及如何重新定义工作的价值。",
            "digital_no": "D20250820190000004", 
            "voice_id": "AA20250822120001",
            "project_name": "ai_employment_challenge"
        },
        {
            "id": "task_006",
            "title": "做生意就不要对低端客户过度的服务",
            "content": "做生意并不是客户的满意度越高越好，而是要提高优质客户的满意度。一定要规避没有支付能力，但是却有时间和精力挑选产品和服务的客户，没有任何一款产品和服务能够讨好所有人。你要明白低价不是一个品牌的核心竞争力，没有人会喜欢没有价值的便宜货。千万别对低端客户投入太多！",
            "digital_no": "D20250820190000004",
            "voice_id": "AA20250822120001",
            "project_name": "business_customer_strategy"
        },
        {
            "id": "task_007",
            "title": "赚钱最快的方式就是做一个聪明的二道贩子",
            "content": "千万别想着什么树立品牌，建设品牌。那些闷声发大财的人都是用了黄牛的思维去做二道贩子的生意。因为他们知道作为一个普通人，没资源、没渠道、没背景，只有做中间商才是唯一的捷径。有一句话说的好啊，新手入行别贪大，倒买倒卖赚差价，不开店铺不囤货，小生意也能做大。",
            "digital_no": "D20250820190000004",
            "voice_id": "AA20250822120001",
            "project_name": "smart_middleman_business"
        }
    ]


def show_available_tasks(tasks: List[Dict[str, Any]]):
    """显示可用任务列表"""
    print(f"\n📋 可用任务列表:")
    print("-" * 80)
    for task in tasks:
        print(f"ID: {task.get('id')}")
        print(f"标题: {task.get('title')}")
        print(f"项目名: {task.get('project_name')}")
        print("-" * 80)

def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Coze视频工作流批量处理器')
    parser.add_argument('--include', nargs='*', help='只执行指定的任务ID（例如：task_001 task_002）')
    parser.add_argument('--exclude', nargs='*', help='跳过指定的任务ID（例如：task_003 task_004）')
    parser.add_argument('--list', action='store_true', help='显示可用任务列表')
    parser.add_argument('--max-workers', type=int, default=2, help='最大并发数（默认2）')
    parser.add_argument('--tasks-file', default='batch_tasks.json', help='任务配置文件路径')
    
    args = parser.parse_args()
    
    print("🚀 Coze视频工作流批量处理器")
    print("=" * 60)
    
    # 配置路径
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 创建批量处理器
    batch_processor = BatchCozeWorkflow(draft_folder_path, max_workers=args.max_workers)
    
    # 设置全局配置
    background_music_path = os.path.join(os.path.dirname(__file__), '..', '..', '华尔兹.mp3')
    if os.path.exists(background_music_path):
        batch_processor.set_background_music(background_music_path, volume=0.3)
    
    batch_processor.set_doubao_api(
        token='adac0afb-5fd4-4c66-badb-370a7ff42df5',
        model='ep-m-20250902010446-mlwmf'
    )
    
    # 加载任务
    if os.path.exists(args.tasks_file):
        print(f"[INFO] 从文件加载任务: {args.tasks_file}")
        tasks = load_tasks_from_json(args.tasks_file)
    else:
        print(f"[INFO] 使用示例任务")
        tasks = create_sample_tasks()
        # 保存示例任务到文件
        with open(args.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 示例任务已保存到: {args.tasks_file}")
    
    # 显示任务列表
    if args.list:
        show_available_tasks(tasks)
        return
    
    # 显示任务过滤信息
    if args.include:
        print(f"[INFO] 只执行指定任务: {args.include}")
    if args.exclude:
        print(f"[INFO] 跳过指定任务: {args.exclude}")
    
    # 执行批量处理
    print("[DEBUG] 开始执行批量处理...")
    results = batch_processor.process_batch(tasks, include_ids=args.include, exclude_ids=args.exclude)
    print("[DEBUG] 批量处理完成，开始保存结果...")
    
    # 保存结果
    batch_processor.save_results('batch_results.json')
    print("[DEBUG] 结果已保存到 batch_results.json")
    
    # 显示详细结果
    if results:
        print(f"\n📊 详细结果:")
        for result in results:
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_icon} {result['title']} - {result['status']} ({result['duration']:.1f}s)")
    else:
        print("[INFO] 没有执行任何任务")
    
    print("[DEBUG] 程序即将退出...")
    
    # 强制退出，避免卡住
    import sys
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断，程序退出")
    except Exception as e:
        print(f"\n[ERROR] 程序异常退出: {e}")
    finally:
        print("[DEBUG] 程序已退出")