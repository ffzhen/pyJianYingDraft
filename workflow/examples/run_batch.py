#!/usr/bin/env python3
"""
批量处理启动脚本
"""

import os
import sys
import subprocess

def run_batch_workflow():
    """运行批量工作流"""
    print("🚀 启动Coze视频批量处理工作流")
    print("=" * 60)
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    batch_script = os.path.join(script_dir, 'batch_coze_workflow.py')
    
    # 检查Python环境
    python_cmd = sys.executable
    
    # 运行批量处理脚本
    cmd = [python_cmd, batch_script]
    
    print(f"📁 工作目录: {script_dir}")
    print(f"🐍 Python命令: {python_cmd}")
    print(f"📜 批处理脚本: {batch_script}")
    print("=" * 60)
    
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

if __name__ == "__main__":
    run_batch_workflow()