#!/usr/bin/env python3
"""
自动并发数检测器

根据当前电脑配置自动确定最优并发数
"""

import os
import sys
import psutil
import platform
import json
import time
from typing import Dict, Any, Tuple

class SystemConcurrencyAnalyzer:
    """系统并发数分析器"""
    
    def __init__(self):
        self.system_info = {}
        self.network_quality = "unknown"
        
    def analyze_hardware(self) -> Dict[str, Any]:
        """分析硬件配置"""
        print("Analyzing hardware configuration... 分析硬件配置...")
        
        # CPU信息
        cpu_logical = psutil.cpu_count(logical=True)
        cpu_physical = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存信息
        memory = psutil.virtual_memory()
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        
        hardware_info = {
            'cpu': {
                'logical_cores': cpu_logical,
                'physical_cores': cpu_physical,
                'max_freq_mhz': cpu_freq.max if cpu_freq else 0,
                'current_usage': cpu_percent
            },
            'memory': {
                'total_gb': memory.total / 1024**3,
                'available_gb': memory.available / 1024**3,
                'usage_percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total / 1024**3,
                'free_gb': disk.free / 1024**3,
                'usage_percent': disk.percent
            },
            'system': platform.system(),
            'python_version': platform.python_version()
        }
        
        return hardware_info
    
    def test_network_quality(self) -> str:
        """测试网络质量"""
        print("Testing network quality... 测试网络质量...")
        
        import requests
        import threading
        
        test_urls = [
            'https://api.coze.cn',
            'https://www.baidu.com',
            'https://www.google.com'
        ]
        
        results = []
        
        def test_url(url):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                latency = (time.time() - start_time) * 1000
                results.append(latency)
            except:
                results.append(9999)  # 超时标记
        
        # 并发测试
        threads = []
        for url in test_urls:
            thread = threading.Thread(target=test_url, args=(url,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 计算平均延迟
        avg_latency = sum(results) / len(results) if results else 9999
        
        if avg_latency < 100:
            return "excellent"
        elif avg_latency < 300:
            return "good"
        elif avg_latency < 1000:
            return "fair"
        else:
            return "poor"
    
    def calculate_optimal_concurrency(self, hardware: Dict[str, Any], network: str) -> Dict[str, Any]:
        """计算最优并发数"""
        print("Calculating optimal concurrency... 计算最优并发数...")
        
        cpu_cores = hardware['cpu']['logical_cores']
        memory_gb = hardware['memory']['total_gb']
        cpu_usage = hardware['cpu']['current_usage']
        memory_usage = hardware['memory']['usage_percent']
        
        # 基础并发数计算
        base_concurrency = min(cpu_cores // 2, 3)
        
        # 根据网络质量调整
        network_multiplier = {
            'excellent': 1.5,
            'good': 1.2,
            'fair': 1.0,
            'poor': 0.7
        }
        
        # 根据内存调整
        if memory_gb < 8:
            memory_multiplier = 0.7
        elif memory_gb < 16:
            memory_multiplier = 1.0
        else:
            memory_multiplier = 1.2
        
        # 根据系统负载调整
        if cpu_usage > 80 or memory_usage > 80:
            load_multiplier = 0.6
        elif cpu_usage > 60 or memory_usage > 60:
            load_multiplier = 0.8
        else:
            load_multiplier = 1.0
        
        # 计算最终并发数
        optimal_concurrency = int(base_concurrency * network_multiplier[network] * 
                                memory_multiplier * load_multiplier)
        
        # 确保在合理范围内
        optimal_concurrency = max(1, min(optimal_concurrency, 8))
        
        # 计算保守和激进配置
        conservative = max(1, optimal_concurrency - 1)
        aggressive = min(8, optimal_concurrency + 1)
        
        return {
            'optimal': optimal_concurrency,
            'conservative': conservative,
            'aggressive': aggressive,
            'calculation_details': {
                'base_concurrency': base_concurrency,
                'network_quality': network,
                'network_multiplier': network_multiplier[network],
                'memory_multiplier': memory_multiplier,
                'load_multiplier': load_multiplier,
                'final_calculation': f"{base_concurrency} × {network_multiplier[network]:.1f} × {memory_multiplier:.1f} × {load_multiplier:.1f} = {optimal_concurrency}"
            }
        }
    
    def generate_config_file(self, concurrency_info: Dict[str, Any], hardware: Dict[str, Any]):
        """生成配置文件"""
        config = {
            'concurrency': {
                'optimal': concurrency_info['optimal'],
                'conservative': concurrency_info['conservative'],
                'aggressive': concurrency_info['aggressive']
            },
            'system_info': hardware,
            'recommendation': 'optimal',
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        config_file = 'auto_concurrency_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"Configuration file generated: {config_file} - 配置文件已生成")
        return config_file
    
    def display_recommendations(self, concurrency_info: Dict[str, Any], hardware: Dict[str, Any]):
        """显示推荐配置"""
        print("\n" + "="*60)
        print("Auto Concurrency Recommendations - 自动并发数推荐结果")
        print("="*60)
        
        print(f"\nSystem Configuration - 系统配置:")
        print(f"  CPU: {hardware['cpu']['logical_cores']} logical cores ({hardware['cpu']['current_usage']:.1f}% usage)")
        print(f"  Memory: {hardware['memory']['total_gb']:.1f}GB ({hardware['memory']['usage_percent']:.1f}% usage)")
        print(f"  Network: {self.network_quality}")
        
        print(f"\nRecommended Concurrency - 推荐并发数:")
        print(f"  Conservative: {concurrency_info['conservative']} workers (most stable)")
        print(f"  Optimal: {concurrency_info['optimal']} workers (recommended)")
        print(f"  Aggressive: {concurrency_info['aggressive']} workers (fastest)")
        
        print(f"\nCalculation Details - 计算详情:")
        details = concurrency_info['calculation_details']
        print(f"  Base concurrency: {details['base_concurrency']}")
        print(f"  Network quality: {details['network_quality']} (×{details['network_multiplier']:.1f})")
        print(f"  Memory multiplier: ×{details['memory_multiplier']:.1f}")
        print(f"  Load multiplier: ×{details['load_multiplier']:.1f}")
        print(f"  Final calculation: {details['final_calculation']}")
        
        print(f"\nEstimated Processing Time (7 tasks) - 预计处理时间:")
        print(f"  Conservative: {7 * 15 // concurrency_info['conservative']:.0f} minutes")
        print(f"  Optimal: {7 * 15 // concurrency_info['optimal']:.0f} minutes")
        print(f"  Aggressive: {7 * 15 // concurrency_info['aggressive']:.0f} minutes")
        
        print(f"\nQuick Start Command - 快速启动命令:")
        print(f"  python workflow/examples/batch_coze_workflow.py --max-workers {concurrency_info['optimal']}")
    
    def run_analysis(self):
        """运行完整分析"""
        print("Auto Concurrency Detector - 自动并发数检测器")
        print("="*60)
        
        # 分析硬件
        hardware = self.analyze_hardware()
        
        # 测试网络
        self.network_quality = self.test_network_quality()
        
        # 计算并发数
        concurrency_info = self.calculate_optimal_concurrency(hardware, self.network_quality)
        
        # 生成配置文件
        config_file = self.generate_config_file(concurrency_info, hardware)
        
        # 显示推荐
        self.display_recommendations(concurrency_info, hardware)
        
        return concurrency_info, hardware

def main():
    """主函数"""
    analyzer = SystemConcurrencyAnalyzer()
    return analyzer.run_analysis()

if __name__ == "__main__":
    main()