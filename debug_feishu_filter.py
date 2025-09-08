#!/usr/bin/env python3
"""
调试飞书过滤条件问题
"""

import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow.feishu_client import FeishuBitableClient, FeishuVideoTaskSource

def test_feishu_filter():
    """测试飞书过滤条件"""
    
    # 读取配置
    with open('workflow/feishu_config_template.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    api_config = config['api_config']
    table_config = config['tables']['content_table']
    
    print("=== 飞书API配置 ===")
    print(f"App ID: {api_config['app_id']}")
    print(f"App Token: {api_config['app_token']}")
    print(f"Table ID: {table_config['table_id']}")
    print()
    
    # 创建客户端
    client = FeishuBitableClient(api_config['app_id'], api_config['app_secret'])
    
    print("=== 测试1: 不使用过滤条件获取所有记录 ===")
    try:
        records = client.get_all_records(
            app_token=api_config['app_token'],
            table_id=table_config['table_id'],
            filter_condition=None
        )
        print(f"✅ 成功获取 {len(records)} 条记录")
        
        # 显示前几条记录的字段信息
        if records:
            print("\n=== 记录字段信息 ===")
            first_record = records[0]
            fields = first_record.get('fields', {})
            print("可用字段:")
            for field_name, field_value in fields.items():
                print(f"  - {field_name}: {type(field_value).__name__} = {field_value}")
            
            # 检查状态字段的值
            status_field = table_config['field_mapping'].get('status', '状态')
            if status_field in fields:
                print(f"\n状态字段 '{status_field}' 的值: {fields[status_field]}")
            else:
                print(f"\n❌ 未找到状态字段 '{status_field}'")
                print("可用的状态相关字段:")
                for field_name in fields.keys():
                    if '状态' in field_name or 'status' in field_name.lower():
                        print(f"  - {field_name}: {fields[field_name]}")
        
    except Exception as e:
        print(f"❌ 获取所有记录失败: {e}")
        return
    
    print("\n=== 测试2: 使用原始过滤条件 ===")
    original_filter = table_config['filter_condition']
    print(f"过滤条件: {json.dumps(original_filter, ensure_ascii=False, indent=2)}")
    
    try:
        records = client.get_all_records(
            app_token=api_config['app_token'],
            table_id=table_config['table_id'],
            filter_condition=original_filter
        )
        print(f"✅ 使用原始过滤条件获取到 {len(records)} 条记录")
    except Exception as e:
        print(f"❌ 原始过滤条件失败: {e}")
        
        # 尝试不同的过滤条件格式
        print("\n=== 测试3: 尝试不同的过滤条件格式 ===")
        
        # 测试1: 使用正确的字段名称
        if records:
            first_record = records[0]
            fields = first_record.get('fields', {})
            status_field = None
            for field_name in fields.keys():
                if '状态' in field_name:
                    status_field = field_name
                    break
            
            if status_field:
                print(f"找到状态字段: {status_field}")
                
                # 测试使用正确的字段名称
                test_filter1 = {
                    "conjunction": "and",
                    "conditions": [
                        {
                            "field_name": status_field,
                            "operator": "is",
                            "value": ["视频草稿生成"]
                        }
                    ]
                }
                
                try:
                    records = client.get_all_records(
                        app_token=api_config['app_token'],
                        table_id=table_config['table_id'],
                        filter_condition=test_filter1
                    )
                    print(f"✅ 使用正确字段名称获取到 {len(records)} 条记录")
                except Exception as e2:
                    print(f"❌ 使用正确字段名称仍然失败: {e2}")
                
                # 测试2: 尝试不同的操作符
                test_filter2 = {
                    "conjunction": "and",
                    "conditions": [
                        {
                            "field_name": status_field,
                            "operator": "equals",
                            "value": "视频草稿生成"
                        }
                    ]
                }
                
                try:
                    records = client.get_all_records(
                        app_token=api_config['app_token'],
                        table_id=table_config['table_id'],
                        filter_condition=test_filter2
                    )
                    print(f"✅ 使用equals操作符获取到 {len(records)} 条记录")
                except Exception as e3:
                    print(f"❌ 使用equals操作符失败: {e3}")
                
                # 测试3: 尝试isNotEmpty操作符
                test_filter3 = {
                    "conjunction": "and",
                    "conditions": [
                        {
                            "field_name": status_field,
                            "operator": "isNotEmpty"
                        }
                    ]
                }
                
                try:
                    records = client.get_all_records(
                        app_token=api_config['app_token'],
                        table_id=table_config['table_id'],
                        filter_condition=test_filter3
                    )
                    print(f"✅ 使用isNotEmpty操作符获取到 {len(records)} 条记录")
                except Exception as e4:
                    print(f"❌ 使用isNotEmpty操作符失败: {e4}")

if __name__ == "__main__":
    test_feishu_filter()
