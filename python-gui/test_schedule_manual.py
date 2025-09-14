#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动测试定时任务执行
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def load_schedules():
    """加载定时任务配置"""
    schedules_file = os.path.join(current_dir, "schedules.json")
    if not os.path.exists(schedules_file):
        print("❌ 定时任务文件不存在")
        return {}
    
    try:
        with open(schedules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载定时任务文件失败: {e}")
        return {}

def update_last_run(schedule_id):
    """更新最后运行时间"""
    schedules = load_schedules()
    if schedule_id in schedules:
        schedules[schedule_id]['last_run'] = datetime.now().isoformat()
        
        try:
            with open(os.path.join(current_dir, "schedules.json"), 'w', encoding='utf-8') as f:
                json.dump(schedules, f, ensure_ascii=False, indent=2)
            print(f"✅ 已更新任务 {schedule_id} 的最后运行时间")
        except Exception as e:
            print(f"❌ 更新最后运行时间失败: {e}")

def list_schedules():
    """列出所有定时任务"""
    schedules = load_schedules()
    if not schedules:
        print("📋 没有找到定时任务")
        return
    
    print("📋 定时任务列表:")
    for i, (schedule_id, schedule) in enumerate(schedules.items(), 1):
        print(f"\n{i}. {schedule.get('name', 'N/A')}")
        print(f"   ID: {schedule_id}")
        print(f"   工作流: {schedule.get('workflow_id', 'N/A')}")
        print(f"   执行时间: {schedule.get('time', 'N/A')}")
        print(f"   重复周期: {schedule.get('repeat', 'N/A')}")
        print(f"   启用状态: {schedule.get('enabled', False)}")
        print(f"   最后运行: {schedule.get('last_run', '从未运行')}")

def simulate_schedule_execution(schedule_id):
    """模拟定时任务执行"""
    schedules = load_schedules()
    if schedule_id not in schedules:
        print(f"❌ 找不到任务ID: {schedule_id}")
        return
    
    schedule = schedules[schedule_id]
    print(f"🎯 模拟执行定时任务: {schedule.get('name')}")
    print(f"   工作流: {schedule.get('workflow_id')}")
    print(f"   执行时间: {schedule.get('time')}")
    print(f"   重复周期: {schedule.get('repeat')}")
    
    # 检查工作流类型
    workflow_id = schedule.get('workflow_id')
    if '飞书' in workflow_id or 'feishu' in workflow_id.lower():
        print(f"✅ 这是飞书异步批量工作流")
        print(f"💡 建议：在GUI中手动执行飞书异步批量处理来测试")
    else:
        print(f"✅ 这是手动生成工作流")
        print(f"💡 建议：在GUI中手动执行工作流来测试")
    
    # 更新最后运行时间
    update_last_run(schedule_id)

def reset_last_run(schedule_id):
    """重置最后运行时间"""
    schedules = load_schedules()
    if schedule_id not in schedules:
        print(f"❌ 找不到任务ID: {schedule_id}")
        return
    
    if 'last_run' in schedules[schedule_id]:
        del schedules[schedule_id]['last_run']
        
        try:
            with open(os.path.join(current_dir, "schedules.json"), 'w', encoding='utf-8') as f:
                json.dump(schedules, f, ensure_ascii=False, indent=2)
            print(f"✅ 已重置任务 {schedule_id} 的最后运行时间")
        except Exception as e:
            print(f"❌ 重置最后运行时间失败: {e}")

def main():
    """主函数"""
    print("🚀 定时任务手动测试工具")
    print("=" * 50)
    
    while True:
        print(f"\n📋 请选择操作:")
        print(f"1. 列出所有定时任务")
        print(f"2. 模拟执行定时任务")
        print(f"3. 重置最后运行时间")
        print(f"4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            list_schedules()
        
        elif choice == '2':
            list_schedules()
            schedule_id = input("\n请输入要模拟执行的任务ID: ").strip()
            if schedule_id:
                simulate_schedule_execution(schedule_id)
        
        elif choice == '3':
            list_schedules()
            schedule_id = input("\n请输入要重置的任务ID: ").strip()
            if schedule_id:
                reset_last_run(schedule_id)
        
        elif choice == '4':
            print("👋 再见！")
            break
        
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    main()
