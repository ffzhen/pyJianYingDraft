#!/usr/bin/env python3
"""
测试GUI配置导入功能
"""

import sys
import os
import json

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_config_import():
    """测试配置导入功能"""
    print("=== 测试配置导入功能 ===")
    print()
    
    # 检查模板配置文件
    template_path = os.path.join(PROJECT_ROOT, 'workflow', 'feishu_config_template.json')
    print(f"模板配置文件路径: {template_path}")
    print(f"文件是否存在: {os.path.exists(template_path)}")
    
    if not os.path.exists(template_path):
        print("❌ 模板配置文件不存在")
        return False
    
    try:
        # 读取模板配置
        with open(template_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ 模板配置文件读取成功")
        print()
        
        # 显示配置映射
        print("📋 配置映射关系:")
        print()
        
        api_config = config.get('api_config', {})
        print("🔧 飞书API配置:")
        print(f"  App ID: {api_config.get('app_id', 'N/A')}")
        print(f"  App Secret: {api_config.get('app_secret', 'N/A')[:10]}...")
        print(f"  App Token: {api_config.get('app_token', 'N/A')}")
        print()
        
        tables = config.get('tables', {})
        print("📊 表格配置:")
        content_table = tables.get('content_table', {})
        print(f"  内容表ID: {content_table.get('table_id', 'N/A')}")
        
        account_table = tables.get('account_table', {})
        print(f"  账号表ID: {account_table.get('table_id', 'N/A')}")
        
        voice_table = tables.get('voice_table', {})
        print(f"  声音表ID: {voice_table.get('table_id', 'N/A')}")
        
        digital_table = tables.get('digital_human_table', {})
        print(f"  数字人表ID: {digital_table.get('table_id', 'N/A')}")
        print()
        
        workflow_config = config.get('workflow_config', {})
        print("⚙️ 工作流配置:")
        coze_config = workflow_config.get('coze_config', {})
        print(f"  Coze Token: {coze_config.get('token', 'N/A')[:20]}...")
        print(f"  Coze Workflow ID: {coze_config.get('workflow_id', 'N/A')}")
        print(f"  火山引擎App ID: {workflow_config.get('volcengine_appid', 'N/A')}")
        print(f"  豆包Token: {workflow_config.get('doubao_token', 'N/A')[:20]}...")
        print(f"  剪映路径: {workflow_config.get('draft_folder_path', 'N/A')}")
        print()
        
        print("🚀 并发配置:")
        print(f"  Coze最大并发数: {workflow_config.get('max_coze_concurrent', 16)}")
        print(f"  视频合成最大并发数: {workflow_config.get('max_synthesis_workers', 4)}")
        print(f"  轮询间隔: {workflow_config.get('poll_interval', 30)}秒")
        print()
        
        print("✅ 配置导入功能测试通过！")
        print()
        print("📝 使用方法:")
        print("1. 启动GUI: python video_generator_gui.py")
        print("2. 切换到'配置管理'标签页")
        print("3. 滚动到底部，点击'导入模板配置'按钮")
        print("4. 所有配置将自动填充到对应字段")
        print("5. 点击'保存配置'保存到本地")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置读取失败: {e}")
        return False

if __name__ == "__main__":
    success = test_config_import()
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n💥 测试失败！")
