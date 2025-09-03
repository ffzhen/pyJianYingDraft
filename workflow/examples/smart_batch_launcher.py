#!/usr/bin/env python3
"""
智能批量处理启动器

根据自动检测的并发数配置启动批量处理
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

class SmartBatchLauncher:
    """智能批量处理启动器"""
    
    def __init__(self):
        self.config_file = 'auto_concurrency_config.json'
        self.config = None
        
    def load_config(self) -> Optional[Dict[str, Any]]:
        """加载自动检测的配置"""
        if not os.path.exists(self.config_file):
            print(f"❌ 配置文件不存在: {self.config_file}")
            print("请先运行: python workflow/examples/auto_concurrency_detector.py")
            return None
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✅ 配置文件已加载: {self.config_file}")
            return self.config
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return None
    
    def get_concurrency(self, strategy: str = 'optimal') -> int:
        """获取并发数"""
        if not self.config:
            return 2  # 默认值
        
        concurrency = self.config.get('concurrency', {})
        return concurrency.get(strategy, 2)
    
    def display_config_info(self):
        """显示配置信息"""
        if not self.config:
            return
        
        print("\n📋 当前配置:")
        print("="*50)
        
        system_info = self.config.get('system_info', {})
        concurrency = self.config.get('concurrency', {})
        
        print(f"系统: {system_info.get('system', 'Unknown')}")
        print(f"CPU: {system_info.get('cpu', {}).get('logical_cores', 'Unknown')} 逻辑核心")
        print(f"内存: {system_info.get('memory', {}).get('total_gb', 'Unknown'):.1f}GB")
        print(f"生成时间: {self.config.get('generated_at', 'Unknown')}")
        
        print(f"\n并发数配置:")
        print(f"  保守: {concurrency.get('conservative', 'Unknown')}")
        print(f"  最优: {concurrency.get('optimal', 'Unknown')}")
        print(f"  激进: {concurrency.get('aggressive', 'Unknown')}")
        print(f"  推荐: {self.config.get('recommendation', 'Unknown')}")
    
    def run_batch(self, strategy: str = 'optimal', **kwargs):
        """运行批量处理"""
        # 加载配置
        config = self.load_config()
        if not config:
            return False
        
        # 获取并发数
        max_workers = self.get_concurrency(strategy)
        
        # 显示配置信息
        self.display_config_info()
        
        print(f"\n🚀 启动批量处理 (策略: {strategy}, 并发数: {max_workers})")
        print("="*60)
        
        # 构建命令
        script_dir = os.path.dirname(os.path.abspath(__file__))
        batch_script = os.path.join(script_dir, 'batch_coze_workflow.py')
        python_cmd = sys.executable
        
        cmd = [python_cmd, batch_script, '--max-workers', str(max_workers)]
        
        # 添加其他参数
        if kwargs.get('include'):
            cmd.extend(['--include'] + kwargs['include'])
        if kwargs.get('exclude'):
            cmd.extend(['--exclude'] + kwargs['exclude'])
        if kwargs.get('tasks_file'):
            cmd.extend(['--tasks-file', kwargs['tasks_file']])
        
        print(f"执行命令: {' '.join(cmd)}")
        print("="*60)
        
        # 运行命令
        try:
            import subprocess
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
    parser = argparse.ArgumentParser(description='智能批量处理启动器')
    parser.add_argument('--strategy', choices=['conservative', 'optimal', 'aggressive'], 
                       default='optimal', help='并发策略 (默认: optimal)')
    parser.add_argument('--include', nargs='*', help='只执行指定的任务ID')
    parser.add_argument('--exclude', nargs='*', help='跳过指定的任务ID')
    parser.add_argument('--tasks-file', default='batch_tasks.json', help='任务配置文件路径')
    parser.add_argument('--show-config', action='store_true', help='显示当前配置')
    parser.add_argument('--redetect', action='store_true', help='重新检测系统配置')
    
    args = parser.parse_args()
    
    launcher = SmartBatchLauncher()
    
    # 重新检测
    if args.redetect:
        print("🔍 重新检测系统配置...")
        from workflow.examples.auto_concurrency_detector import SystemConcurrencyAnalyzer
        analyzer = SystemConcurrencyAnalyzer()
        analyzer.run_analysis()
        return
    
    # 显示配置
    if args.show_config:
        launcher.load_config()
        launcher.display_config_info()
        return
    
    # 运行批量处理
    launcher.run_batch(
        strategy=args.strategy,
        include=args.include,
        exclude=args.exclude,
        tasks_file=args.tasks_file
    )

if __name__ == "__main__":
    main()