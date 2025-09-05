#!/usr/bin/env python3
"""
测试飞书记录状态更新功能
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from workflow.feishu_client import FeishuVideoTaskSource
from workflow.feishu_batch_workflow import load_config_from_file


def test_status_update():
    """测试状态更新功能"""
    print("测试飞书记录状态更新功能")
    print("=" * 50)
    
    # 加载配置
    config_file = "workflow/feishu_config_template.json"
    if not os.path.exists(config_file):
        print(f"[ERROR] 配置文件不存在: {config_file}")
        return False
    
    config = load_config_from_file(config_file)
    
    # 提取配置信息
    api_config = config.get("api_config", {})
    tables = config.get("tables", {})
    
    try:
        # 创建任务源
        task_source = FeishuVideoTaskSource(
            app_id=api_config["app_id"],
            app_secret=api_config["app_secret"],
            app_token=api_config["app_token"],
            table_id=tables["content_table"]["table_id"],
            field_mapping=tables["content_table"]["field_mapping"]
        )
        
        print("[OK] 飞书任务源创建成功")
        
        # 测试状态更新
        test_record_id = "recuVOced36TiW"  # 使用一个真实的记录ID
        
        print(f"[INFO] 测试更新记录状态: {test_record_id}")
        
        # 尝试更新状态
        success = task_source.update_record_status(test_record_id, "测试状态")
        
        if success:
            print("[OK] 状态更新成功")
            return True
        else:
            print("[ERROR] 状态更新失败")
            return False
            
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_status_update()
    if success:
        print("\n✅ 状态更新功能测试通过")
    else:
        print("\n❌ 状态更新功能测试失败")