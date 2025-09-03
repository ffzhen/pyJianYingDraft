#!/usr/bin/env python3
"""
并发数优化分析和配置工具

分析当前系统的并发限制并提供最优配置建议
"""

import os
import sys
import psutil
import requests
import threading
import time
from typing import Dict, Any

def analyze_system_resources():
    """分析系统资源"""
    print("🔍 系统资源分析")
    print("=" * 50)
    
    # CPU信息
    cpu_count = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    print(f"CPU逻辑核心数: {cpu_count}")
    print(f"CPU物理核心数: {cpu_count_physical}")
    print(f"CPU使用率: {cpu_percent}%")
    print(f"内存总量: {memory.total / 1024**3:.1f} GB")
    print(f"内存可用: {memory.available / 1024**3:.1f} GB")
    print(f"内存使用率: {memory.percent}%")
    
    return {
        'cpu_logical': cpu_count,
        'cpu_physical': cpu_count_physical,
        'cpu_percent': cpu_percent,
        'memory_total_gb': memory.total / 1024**3,
        'memory_available_gb': memory.available / 1024**3,
        'memory_percent': memory.percent
    }

def analyze_network_limits():
    """分析网络限制"""
    print("\n🌐 网络限制分析")
    print("=" * 50)
    
    # 测试网络延迟
    test_urls = [
        'https://api.coze.cn',
        'https://www.baidu.com',
        'https://www.google.com'
    ]
    
    for url in test_urls:
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            latency = (time.time() - start_time) * 1000
            print(f"{url}: {latency:.0f}ms")
        except:
            print(f"{url}: 连接失败")
    
    print("\n📋 Coze API限制:")
    print("- QPS限制: 未知 (建议保守估计)")
    print("- 并发限制: 未知 (建议保守估计)")
    print("- 单任务时长: ~15分钟")

def analyze_task_characteristics():
    """分析任务特征"""
    print("\n📊 任务特征分析")
    print("=" * 50)
    
    characteristics = {
        "单任务CPU使用": "低-中 (主要依赖网络请求)",
        "单任务内存使用": "低 (~100-200MB)",
        "单任务网络带宽": "中 (音频下载+视频上传)",
        "单任务时长": "15-20分钟",
        "I/O密集程度": "高 (文件读写)",
        "网络依赖程度": "高 (API调用)",
        "失败重试成本": "中 (需要重新执行整个任务)"
    }
    
    for key, value in characteristics.items():
        print(f"{key}: {value}")

def recommend_optimal_config(system_info: Dict[str, Any]) -> Dict[str, Any]:
    """推荐最优配置"""
    print("\n⚙️ 最优配置推荐")
    print("=" * 50)
    
    # 基础推荐
    cpu_logical = system_info['cpu_logical']
    memory_gb = system_info['memory_total_gb']
    memory_percent = system_info['memory_percent']
    
    # 保守推荐 (网络限制优先)
    conservative_workers = min(2, cpu_logical // 2)
    
    # 中等推荐 (平衡考虑)
    moderate_workers = min(3, cpu_logical // 2 + 1)
    
    # 激进推荐 (系统资源优先)
    aggressive_workers = min(5, cpu_logical)
    
    # 内存限制
    if memory_gb < 8:
        conservative_workers = min(conservative_workers, 2)
        moderate_workers = min(moderate_workers, 3)
        aggressive_workers = min(aggressive_workers, 3)
    elif memory_gb < 16:
        conservative_workers = min(conservative_workers, 3)
        moderate_workers = min(moderate_workers, 4)
        aggressive_workers = min(aggressive_workers, 4)
    
    # CPU使用率限制
    if memory_percent > 80:
        conservative_workers = max(1, conservative_workers - 1)
        moderate_workers = max(2, moderate_workers - 1)
        aggressive_workers = max(3, aggressive_workers - 1)
    
    recommendations = {
        'conservative': {
            'workers': conservative_workers,
            'description': '保守策略 (网络稳定优先)',
            'estimated_time': '7-8小时 (7个任务)',
            'risk_level': '低',
            'suitable_for': '网络不稳定或API限制严格'
        },
        'moderate': {
            'workers': moderate_workers,
            'description': '平衡策略 (推荐)',
            'estimated_time': '4-5小时 (7个任务)',
            'risk_level': '中',
            'suitable_for': '一般网络条件和系统资源'
        },
        'aggressive': {
            'workers': aggressive_workers,
            'description': '激进策略 (速度优先)',
            'estimated_time': '2-3小时 (7个任务)',
            'risk_level': '高',
            'suitable_for': '网络良好且系统资源充足'
        }
    }
    
    for strategy, config in recommendations.items():
        print(f"\n{strategy.upper()} 策略:")
        print(f"  并发数: {config['workers']}")
        print(f"  描述: {config['description']}")
        print(f"  预计时间: {config['estimated_time']}")
        print(f"  风险等级: {config['risk_level']}")
        print(f"  适用场景: {config['suitable_for']}")
    
    return recommendations

def create_optimized_scripts():
    """创建优化后的脚本"""
    print("\n📝 优化脚本生成")
    print("=" * 50)
    
    # 保守策略脚本
    conservative_script = '''#!/bin/bash
# 保守策略 - 稳定优先
echo "🚀 启动保守策略批量处理 (2并发)"
python workflow/examples/batch_coze_workflow.py --max-workers 2
'''
    
    # 平衡策略脚本
    moderate_script = '''#!/bin/bash
# 平衡策略 - 推荐配置
echo "🚀 启动平衡策略批量处理 (3并发)"
python workflow/examples/batch_coze_workflow.py --max-workers 3
'''
    
    # 激进策略脚本
    aggressive_script = '''#!/bin/bash
# 激进策略 - 速度优先
echo "🚀 启动激进策略批量处理 (5并发)"
python workflow/examples/batch_coze_workflow.py --max-workers 5
'''
    
    # 保存脚本
    scripts = [
        ('conservative_batch.sh', conservative_script),
        ('moderate_batch.sh', moderate_script),
        ('aggressive_batch.sh', aggressive_script)
    ]
    
    for filename, content in scripts:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已生成: {filename}")
    
    print("\n使用方法:")
    print("  bash conservative_batch.sh  # 保守策略")
    print("  bash moderate_batch.sh      # 平衡策略")
    print("  bash aggressive_batch.sh    # 激进策略")

def main():
    """主函数"""
    print("🔧 Coze批量处理并发数优化工具")
    print("=" * 60)
    
    # 系统资源分析
    system_info = analyze_system_resources()
    
    # 网络限制分析
    analyze_network_limits()
    
    # 任务特征分析
    analyze_task_characteristics()
    
    # 配置推荐
    recommendations = recommend_optimal_config(system_info)
    
    # 生成优化脚本
    create_optimized_scripts()
    
    print("\n📋 性能优化建议:")
    print("=" * 50)
    print("1. 首次运行建议使用保守策略")
    print("2. 观察网络稳定性和API响应")
    print("3. 如无问题可逐步提高并发数")
    print("4. 监控系统资源使用情况")
    print("5. 避免在系统高负载时运行")
    
    print("\n🎯 推荐执行策略:")
    print("  开发/测试: 保守策略 (1-2并发)")
    print("  生产环境: 平衡策略 (2-3并发)")
    print("  紧急任务: 激进策略 (3-5并发)")

if __name__ == "__main__":
    main()