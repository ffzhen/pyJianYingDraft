#!/usr/bin/env python3
"""
测试配置导入功能
"""

import sys
import os
import json

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_template_config_loading():
    """测试模板配置加载"""
    template_path = os.path.join(PROJECT_ROOT, 'workflow', 'feishu_config_template.json')
    
    print(f"模板配置文件路径: {template_path}")
    print(f"文件是否存在: {os.path.exists(template_path)}")
    
    if os.path.exists(template_path):
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print("\n=== 配置内容 ===")
            print(f"API配置: {config.get('api_config', {})}")
            print(f"表格配置: {config.get('tables', {})}")
            print(f"工作流配置: {config.get('workflow_config', {})}")
            
            # 验证关键配置项
            api_config = config.get('api_config', {})
            print(f"\n=== 关键配置项 ===")
            print(f"飞书App ID: {api_config.get('app_id')}")
            print(f"飞书App Secret: {api_config.get('app_secret')}")
            print(f"飞书App Token: {api_config.get('app_token')}")
            
            tables = config.get('tables', {})
            content_table = tables.get('content_table', {})
            print(f"内容表ID: {content_table.get('table_id')}")
            
            workflow_config = config.get('workflow_config', {})
            coze_config = workflow_config.get('coze_config', {})
            print(f"Coze Token: {coze_config.get('token')}")
            print(f"Coze Workflow ID: {coze_config.get('workflow_id')}")
            print(f"剪映路径: {workflow_config.get('draft_folder_path')}")
            
            print("\n✅ 配置加载成功！")
            return True
            
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            return False
    else:
        print("❌ 模板配置文件不存在")
        return False

if __name__ == "__main__":
    print("开始测试配置导入功能...")
    success = test_template_config_loading()
    
    if success:
        print("\n🎉 测试通过！可以正常导入配置。")
    else:
        print("\n💥 测试失败！请检查配置文件。")
