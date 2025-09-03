#!/usr/bin/env python3
"""
简化的批量处理启动脚本 - 提供交互式选择
"""

import os
import sys
import json
import subprocess
from typing import List, Dict, Any

def load_tasks(tasks_file: str = 'batch_tasks.json') -> List[Dict[str, Any]]:
    """加载任务列表"""
    if not os.path.exists(tasks_file):
        print(f"❌ 任务文件不存在: {tasks_file}")
        return []
    
    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        return tasks
    except Exception as e:
        print(f"❌ 加载任务文件失败: {e}")
        return []

def show_tasks(tasks: List[Dict[str, Any]]):
    """显示任务列表"""
    if not tasks:
        print("❌ 没有可用任务")
        return
    
    print(f"\n📋 可用任务列表 ({len(tasks)} 个):")
    print("=" * 80)
    for i, task in enumerate(tasks, 1):
        print(f"{i:2d}. [{task.get('id')}] {task.get('title')}")
        print(f"    项目: {task.get('project_name')}")
        print(f"    内容: {task.get('content', '')[:50]}...")
        print("-" * 80)

def select_tasks_interactive(tasks: List[Dict[str, Any]]) -> List[str]:
    """交互式选择任务"""
    if not tasks:
        return []
    
    print("\n🎯 请选择要执行的任务:")
    print("1. 执行所有任务")
    print("2. 选择特定任务")
    print("3. 跳过某些任务")
    print("4. 退出")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        # 执行所有任务
        return []
    elif choice == "2":
        # 选择特定任务
        show_tasks(tasks)
        selected = input("\n请输入要执行的任务编号 (用空格分隔，例如: 1 3 5): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selected.split() if x.strip()]
            selected_ids = [tasks[i]['id'] for i in indices if 0 <= i < len(tasks)]
            print(f"✅ 已选择任务: {selected_ids}")
            return selected_ids
        except ValueError:
            print("❌ 输入格式错误")
            return []
    elif choice == "3":
        # 跳过某些任务
        show_tasks(tasks)
        excluded = input("\n请输入要跳过的任务编号 (用空格分隔，例如: 2 4): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in excluded.split() if x.strip()]
            excluded_ids = [tasks[i]['id'] for i in indices if 0 <= i < len(tasks)]
            print(f"✅ 将跳过任务: {excluded_ids}")
            return excluded_ids
        except ValueError:
            print("❌ 输入格式错误")
            return []
    elif choice == "4":
        # 退出
        return None
    else:
        print("❌ 无效选择")
        return []

def run_batch_workflow(include_ids: List[str] = None, exclude_ids: List[str] = None):
    """运行批量工作流"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    batch_script = os.path.join(script_dir, 'batch_coze_workflow.py')
    python_cmd = sys.executable
    
    # 构建命令
    cmd = [python_cmd, batch_script]
    
    if include_ids:
        cmd.extend(['--include'] + include_ids)
    if exclude_ids:
        cmd.extend(['--exclude'] + exclude_ids)
    
    print(f"\n🚀 执行命令: {' '.join(cmd)}")
    print("=" * 80)
    
    try:
        # 运行脚本
        result = subprocess.run(cmd, cwd=script_dir, check=True)
        print("✅ 批量处理完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 批量处理失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 运行异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Coze视频批量处理 - 交互式选择器")
    print("=" * 60)
    
    # 加载任务
    tasks = load_tasks()
    if not tasks:
        print("❌ 无法加载任务，请检查 batch_tasks.json 文件")
        return
    
    # 显示任务
    show_tasks(tasks)
    
    # 交互式选择
    selection_mode = select_tasks_interactive(tasks)
    
    if selection_mode is None:
        # 用户选择退出
        print("👋 再见!")
        return
    
    # 确定执行模式
    if len(selection_mode) == 0:
        # 执行所有任务
        print("\n🎯 将执行所有任务")
        include_ids = None
        exclude_ids = None
    else:
        # 判断是包含还是排除模式
        if len(selection_mode) <= len(tasks) / 2:
            # 选择的是少数，使用包含模式
            print(f"\n🎯 将执行 {len(selection_mode)} 个指定任务")
            include_ids = selection_mode
            exclude_ids = None
        else:
            # 选择的是多数，使用排除模式
            all_ids = [task['id'] for task in tasks]
            exclude_ids = selection_mode
            include_ids = None
            print(f"\n🎯 将跳过 {len(exclude_ids)} 个任务，执行 {len(all_ids) - len(exclude_ids)} 个任务")
    
    # 确认执行
    confirm = input("\n确认执行吗? (y/N): ").strip().lower()
    if confirm in ['y', 'yes', '是']:
        run_batch_workflow(include_ids, exclude_ids)
    else:
        print("❌ 已取消执行")

if __name__ == "__main__":
    main()