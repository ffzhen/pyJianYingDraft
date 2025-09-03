#!/usr/bin/env python3
"""
批量处理性能监控脚本

实时监控系统资源，动态调整并发数
"""

import psutil
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.current_workers = 0
        self.monitoring = False
        self.history = []
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count(logical=True)
            
            # 内存指标
            memory = psutil.virtual_memory()
            
            # 网络指标
            network = psutil.net_io_counters()
            
            # 磁盘指标
            disk = psutil.disk_usage('/')
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_per_core': cpu_percent / cpu_count
                },
                'memory': {
                    'percent': memory.percent,
                    'available_gb': memory.available / 1024**3,
                    'total_gb': memory.total / 1024**3
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                'disk': {
                    'percent': disk.percent,
                    'free_gb': disk.free / 1024**3
                },
                'workers': {
                    'current': self.current_workers,
                    'max': self.max_workers
                }
            }
        except Exception as e:
            print(f"❌ 获取系统指标失败: {e}")
            return {}
    
    def should_adjust_workers(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """判断是否需要调整并发数"""
        cpu_percent = metrics.get('cpu', {}).get('percent', 0)
        memory_percent = metrics.get('memory', {}).get('percent', 0)
        load_per_core = metrics.get('cpu', {}).get('load_per_core', 0)
        
        recommendations = {
            'increase': False,
            'decrease': False,
            'new_workers': self.current_workers,
            'reason': ''
        }
        
        # 判断是否需要减少并发数
        if cpu_percent > 85 or memory_percent > 85:
            recommendations['decrease'] = True
            recommendations['new_workers'] = max(1, self.current_workers - 1)
            recommendations['reason'] = f"系统负载过高 (CPU: {cpu_percent}%, 内存: {memory_percent}%)"
        
        elif load_per_core > 0.8:
            recommendations['decrease'] = True
            recommendations['new_workers'] = max(1, self.current_workers - 1)
            recommendations['reason'] = f"单核心负载过高 ({load_per_core:.2f})"
        
        # 判断是否可以增加并发数
        elif cpu_percent < 50 and memory_percent < 60 and self.current_workers < self.max_workers:
            recommendations['increase'] = True
            recommendations['new_workers'] = min(self.max_workers, self.current_workers + 1)
            recommendations['reason'] = f"系统负载较低 (CPU: {cpu_percent}%, 内存: {memory_percent}%)"
        
        return recommendations
    
    def start_monitoring(self, duration: int = 3600, interval: int = 30):
        """开始监控"""
        print(f"🔍 开始性能监控 (持续 {duration//60} 小时, 间隔 {interval} 秒)")
        print(f"📊 当前并发数: {self.current_workers}/{self.max_workers}")
        print("=" * 80)
        
        self.monitoring = True
        start_time = time.time()
        
        while self.monitoring and (time.time() - start_time) < duration:
            # 获取系统指标
            metrics = self.get_system_metrics()
            if not metrics:
                time.sleep(interval)
                continue
            
            # 保存历史记录
            self.history.append(metrics)
            
            # 分析是否需要调整
            adjustment = self.should_adjust_workers(metrics)
            
            # 显示状态
            timestamp = datetime.now().strftime('%H:%M:%S')
            cpu_percent = metrics['cpu']['percent']
            memory_percent = metrics['memory']['percent']
            load_per_core = metrics['cpu']['load_per_core']
            
            print(f"[{timestamp}] CPU: {cpu_percent:5.1f}% | 内存: {memory_percent:5.1f}% | 负载/核心: {load_per_core:.2f}")
            
            # 显示调整建议
            if adjustment['increase'] or adjustment['decrease']:
                print(f"⚠️  建议: {adjustment['reason']}")
                if adjustment['increase']:
                    print(f"📈 建议增加并发数: {self.current_workers} → {adjustment['new_workers']}")
                elif adjustment['decrease']:
                    print(f"📉 建议减少并发数: {self.current_workers} → {adjustment['new_workers']}")
                print("-" * 80)
            
            time.sleep(interval)
        
        self.monitoring = False
        print(f"✅ 监控结束")
    
    def save_report(self, filename: str = 'performance_report.json'):
        """保存性能报告"""
        report = {
            'monitoring_period': {
                'start': self.history[0]['timestamp'] if self.history else None,
                'end': self.history[-1]['timestamp'] if self.history else None,
                'duration_minutes': len(self.history) * (30 // 60)  # 假设30秒间隔
            },
            'configuration': {
                'max_workers': self.max_workers,
                'current_workers': self.current_workers
            },
            'metrics_history': self.history,
            'summary': self.generate_summary()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 性能报告已保存: {filename}")
    
    def generate_summary(self) -> Dict[str, Any]:
        """生成性能摘要"""
        if not self.history:
            return {}
        
        cpu_values = [m['cpu']['percent'] for m in self.history]
        memory_values = [m['memory']['percent'] for m in self.history]
        
        return {
            'cpu': {
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'total_samples': len(self.history)
        }

def main():
    """主函数"""
    print("🔧 批量处理性能监控工具")
    print("=" * 60)
    
    # 配置监控参数
    max_workers = 3  # 最大并发数
    current_workers = 2  # 当前并发数
    duration = 3600  # 监控时长（秒）
    interval = 30  # 监控间隔（秒）
    
    # 创建监控器
    monitor = PerformanceMonitor(max_workers)
    monitor.current_workers = current_workers
    
    # 开始监控
    monitor.start_monitoring(duration, interval)
    
    # 保存报告
    monitor.save_report()
    
    # 显示摘要
    summary = monitor.generate_summary()
    if summary:
        print("\n📊 性能摘要:")
        print(f"CPU使用率 - 平均: {summary['cpu']['average']:.1f}%, 最高: {summary['cpu']['max']:.1f}%")
        print(f"内存使用率 - 平均: {summary['memory']['average']:.1f}%, 最高: {summary['memory']['max']:.1f}%")
        print(f"监控样本数: {summary['total_samples']}")

if __name__ == "__main__":
    main()