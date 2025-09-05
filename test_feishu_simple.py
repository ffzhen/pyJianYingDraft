#!/usr/bin/env python3
"""
飞书数据获取测试脚本（简化版）
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from workflow.feishu_client import FeishuVideoTaskSource
from workflow.feishu_batch_workflow import load_config_from_file


def test_data_retrieval():
    """测试数据获取和处理"""
    print("飞书数据获取测试")
    print("=" * 60)
    
    # 加载配置
    config_file = "workflow/feishu_config_template.json"
    if not os.path.exists(config_file):
        print(f"[ERROR] 配置文件不存在: {config_file}")
        return
    
    config = load_config_from_file(config_file)
    
    # 提取配置信息
    api_config = config.get("api_config", {})
    tables = config.get("tables", {})
    
    print(f"[INFO] API配置: {api_config['app_id'][:10]}...")
    print(f"[INFO] 内容表ID: {tables['content_table']['table_id']}")
    print(f"[INFO] 账号表ID: {tables['account_table']['table_id']}")
    print(f"[INFO] 音色表ID: {tables['voice_table']['table_id']}")
    print(f"[INFO] 数字人表ID: {tables['digital_human_table']['table_id']}")
    
    try:
        # 创建数据源
        print(f"\n步骤1: 创建飞书数据源...")
        task_source = FeishuVideoTaskSource(
            app_id=api_config["app_id"],
            app_secret=api_config["app_secret"],
            app_token=api_config["app_token"],
            table_id=tables["content_table"]["table_id"],
            field_mapping=tables["content_table"]["field_mapping"],
            account_table_config={
                "app_token": api_config["app_token"],
                "table_id": tables["account_table"]["table_id"],
                "account_field": tables["account_table"]["account_field"],
                "name_field": tables["account_table"]["name_field"]
            },
            voice_table_config={
                "app_token": api_config["app_token"],
                "table_id": tables["voice_table"]["table_id"],
                "account_field": tables["voice_table"]["account_field"],
                "voice_id_field": tables["voice_table"]["voice_id_field"]
            },
            digital_human_table_config={
                "app_token": api_config["app_token"],
                "table_id": tables["digital_human_table"]["table_id"],
                "account_field": tables["digital_human_table"]["account_field"],
                "digital_no_field": tables["digital_human_table"]["digital_no_field"]
            }
        )
        print("[OK] 数据源创建成功")
        
        # 获取过滤条件
        filter_condition = tables["content_table"].get("filter_condition")
        print(f"\n步骤2: 过滤条件")
        print(f"   条件: {filter_condition}")
        
        # 先尝试不使用过滤条件获取数据
        print(f"\n步骤3: 获取原始数据（无过滤条件）...")
        records = task_source.client.get_all_records(
            app_token=api_config["app_token"],
            table_id=tables["content_table"]["table_id"],
            filter_condition=None
        )
        print(f"[OK] 获取到 {len(records)} 条原始记录")
        
        # 显示前3条原始记录
        if records:
            print(f"\n前3条原始记录:")
            for i, record in enumerate(records[:3]):
                fields = record.get("fields", {})
                print(f"\n--- 记录 {i+1} ---")
                print(f"记录ID: {record.get('record_id')}")
                print(f"标题: {fields.get('仿写标题', 'N/A')}")
                print(f"内容: {fields.get('仿写文案', 'N/A')[:50]}...")
                print(f"关联账号: {fields.get('关联账号', 'N/A')}")
                print(f"状态: {fields.get('状态', 'N/A')}")
        
        # 预加载关联数据
        print(f"\n步骤4: 预加载关联数据...")
        if hasattr(task_source, '_preload_account_data'):
            task_source._preload_account_data()
        if hasattr(task_source, '_preload_voice_data'):
            task_source._preload_voice_data()
        if hasattr(task_source, '_preload_digital_human_data'):
            task_source._preload_digital_human_data()
        
        # 显示缓存统计
        print(f"   账号缓存: {len(task_source._account_cache)} 条")
        print(f"   音色缓存: {len(task_source._voice_cache)} 个账号")
        print(f"   数字人缓存: {len(task_source._digital_human_cache)} 个账号")
        
        # 转换为任务数据
        print(f"\n步骤5: 转换为任务数据...")
        tasks = task_source._records_to_tasks_with_relations(records)
        print(f"[OK] 转换为 {len(tasks)} 个任务")
        
        # 显示任务数据
        if tasks:
            print(f"\n生成的任务数据 (前5个):")
            for i, task in enumerate(tasks[:5]):
                print(f"\n--- 任务 {i+1} ---")
                print(f"任务ID: {task['id']}")
                print(f"标题: {task['title']}")
                print(f"内容: {task['content'][:50]}...")
                print(f"关联账号: {task['account_id']}")
                print(f"音色ID: {task['voice_id']}")
                print(f"数字人编号: {task['digital_no']}")
                print(f"项目名称: {task['project_name']}")
                print(f"飞书记录ID: {task['feishu_record_id']}")
        
        # 保存测试结果
        print(f"\n步骤6: 保存测试结果...")
        test_result = {
            "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "api_config": {
                    "app_id": api_config["app_id"],
                    "app_token": api_config["app_token"]
                },
                "tables": {
                    "content_table": tables["content_table"]["table_id"],
                    "account_table": tables["account_table"]["table_id"],
                    "voice_table": tables["voice_table"]["table_id"],
                    "digital_human_table": tables["digital_human_table"]["table_id"]
                }
            },
            "statistics": {
                "total_records": len(records),
                "valid_tasks": len(tasks),
                "account_cache": len(getattr(task_source, '_account_cache', {})),
                "voice_cache": len(getattr(task_source, '_voice_cache', {})),
                "digital_human_cache": len(getattr(task_source, '_digital_human_cache', {}))
            },
            "sample_records": records[:3] if records else [],
            "sample_tasks": tasks[:5] if tasks else []
        }
        
        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_file = f"test_result_{timestamp}.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 测试结果已保存到: {test_file}")
        
        # 显示统计信息
        print(f"\n测试统计:")
        print(f"   原始记录数: {len(records)}")
        print(f"   有效任务数: {len(tasks)}")
        print(f"   账号数据: {len(getattr(task_source, '_account_cache', {}))} 条")
        print(f"   音色数据: {len(getattr(task_source, '_voice_cache', {}))} 个账号")
        print(f"   数字人数据: {len(getattr(task_source, '_digital_human_cache', {}))} 个账号")
        
        return tasks
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    try:
        tasks = test_data_retrieval()
        
        if tasks:
            print(f"\n测试成功！")
            print(f"   获取到 {len(tasks)} 个有效任务")
            print(f"   可以继续执行视频合成流程")
        else:
            print(f"\n测试完成，但没有获取到有效任务")
            print(f"   请检查配置和数据")
            
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断测试")
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")


if __name__ == "__main__":
    main()