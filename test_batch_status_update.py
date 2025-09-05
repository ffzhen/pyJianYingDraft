#!/usr/bin/env python3
"""
测试批量工作流中的状态更新功能（简化版，不实际生成视频）
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from workflow.feishu_batch_workflow import FeishuBatchWorkflow
from workflow.feishu_batch_workflow import load_config_from_file


def test_batch_status_update():
    """测试批量工作流中的状态更新功能"""
    print("测试批量工作流中的状态更新功能")
    print("=" * 60)
    
    # 加载配置
    config_file = "workflow/feishu_config_template.json"
    if not os.path.exists(config_file):
        print(f"[ERROR] 配置文件不存在: {config_file}")
        return False
    
    config = load_config_from_file(config_file)
    
    try:
        # 创建批量工作流
        workflow = FeishuBatchWorkflow("draft_output")
        
        # 从配置文件设置
        workflow.set_config_from_dict(config)
        
        print("[OK] 批量工作流创建成功")
        
        # 获取任务（但不实际处理）
        print("[INFO] 获取飞书任务...")
        tasks = workflow.load_tasks_from_feishu(None)  # 不使用过滤条件
        
        if not tasks:
            print("[WARN] 没有找到任务")
            return False
        
        print(f"[OK] 获取到 {len(tasks)} 个任务")
        
        # 创建飞书任务源
        from workflow.feishu_client import FeishuVideoTaskSource
        
        api_config = config.get("api_config", {})
        tables = config.get("tables", {})
        
        task_source = FeishuVideoTaskSource(
            app_id=api_config["app_id"],
            app_secret=api_config["app_secret"],
            app_token=api_config["app_token"],
            table_id=tables["content_table"]["table_id"],
            field_mapping=tables["content_table"]["field_mapping"]
        )
        
        # 测试更新第一个任务的状态
        first_task = tasks[0]
        record_id = first_task.get("feishu_record_id")
        task_id = first_task.get("id")
        
        if record_id:
            print(f"[INFO] 测试更新任务 {task_id} 的状态...")
            
            # 模拟视频生成完成
            success = task_source.update_record_status(record_id, "视频生成完成")
            
            if success:
                print(f"[OK] 任务 {task_id} 状态更新成功")
                
                # 等待一下再测试失败状态
                import time
                time.sleep(2)
                
                # 恢复为原始状态
                success2 = task_source.update_record_status(record_id, "视频草稿生成")
                if success2:
                    print(f"[OK] 任务 {task_id} 状态已恢复")
                    return True
                else:
                    print(f"[ERROR] 任务 {task_id} 状态恢复失败")
                    return False
            else:
                print(f"[ERROR] 任务 {task_id} 状态更新失败")
                return False
        else:
            print(f"[ERROR] 任务 {task_id} 没有飞书记录ID")
            return False
            
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_batch_status_update()
    if success:
        print("\n✅ 批量工作流状态更新功能测试通过")
        print("现在可以运行完整的批量工作流，视频生成完成后会自动更新飞书记录状态")
    else:
        print("\n❌ 批量工作流状态更新功能测试失败")