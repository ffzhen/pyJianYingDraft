#!/usr/bin/env python3
"""
演示配置导入功能
"""

import sys
import os
import json

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def show_config_mapping():
    """显示配置映射关系"""
    print("=== 配置导入映射关系 ===")
    print()
    
    print("📋 从 workflow/feishu_config_template.json 导入到 GUI 的映射：")
    print()
    
    print("🔧 飞书API配置:")
    print("  api_config.app_id → 飞书App ID")
    print("  api_config.app_secret → 飞书App Secret") 
    print("  api_config.app_token → 飞书App Token")
    print()
    
    print("📊 表格配置:")
    print("  tables.content_table.table_id → 内容表ID")
    print("  tables.account_table.table_id → 账号表ID")
    print("  tables.voice_table.table_id → 声音表ID")
    print("  tables.digital_human_table.table_id → 数字人表ID")
    print()
    
    print("⚙️ 工作流配置:")
    print("  workflow_config.coze_config.token → Coze Bearer Token")
    print("  workflow_config.coze_config.workflow_id → Coze Workflow ID")
    print("  workflow_config.volcengine_appid → 火山引擎App ID")
    print("  workflow_config.volcengine_access_token → 火山引擎Access Token")
    print("  workflow_config.doubao_token → 豆包Token")
    print("  workflow_config.draft_folder_path → 剪映草稿文件夹路径")
    print()
    
    print("🚀 并发配置:")
    print("  workflow_config.max_coze_concurrent → Coze最大并发数")
    print("  workflow_config.max_synthesis_workers → 视频合成最大并发数")
    print("  workflow_config.poll_interval → 轮询间隔(秒)")
    print()
    
    print("✅ 使用方法:")
    print("1. 启动GUI: python video_generator_gui.py")
    print("2. 切换到'配置管理'标签页")
    print("3. 点击'导入模板配置'按钮")
    print("4. 所有配置将自动填充到对应字段")
    print("5. 点击'保存配置'保存到本地")

if __name__ == "__main__":
    show_config_mapping()
