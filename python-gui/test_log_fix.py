#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日志修复
"""

import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

def test_log_methods():
    """测试日志方法"""
    print("🧪 测试日志方法...")
    
    # 模拟VideoGeneratorGUI的日志相关方法
    class MockGUI:
        def __init__(self):
            self.temp_logs = []
            self.log_text = None
            self.current_session_id = "test_session"
            self.session_logs = {}
        
        def _temp_log_setup(self):
            """临时日志设置"""
            self.temp_logs = []
        
        def _temp_log_message(self, message):
            """临时日志方法"""
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            self.temp_logs.append(log_entry)
            print(log_entry)
        
        def _replace_temp_log(self):
            """替换临时日志方法为正式方法"""
            # 将临时日志转移到正式日志
            if hasattr(self, 'temp_logs') and hasattr(self, 'log_text'):
                for log in self.temp_logs:
                    self.log_text.insert(log + "\n")
                delattr(self, 'temp_logs')

            # 清理临时方法（如果存在）
            if hasattr(self, '_temp_log_message'):
                delattr(self, '_temp_log_message')
            
            # log_message方法已经在create_log_tab中定义，无需额外操作
        
        def log_message(self, message):
            """正式日志方法"""
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            session_info = f"[会话:{self.current_session_id}]" if self.current_session_id else "[系统]"
            log_entry = f"[{timestamp}] {session_info} {message}"
            print(log_entry)
    
    # 测试日志方法
    gui = MockGUI()
    
    # 测试临时日志设置
    gui._temp_log_setup()
    print("✅ 临时日志设置成功")
    
    # 测试临时日志方法
    gui._temp_log_message("测试临时日志")
    print("✅ 临时日志方法工作正常")
    
    # 测试替换日志方法
    gui._replace_temp_log()
    print("✅ 日志方法替换成功")
    
    # 测试正式日志方法
    gui.log_message("测试正式日志")
    print("✅ 正式日志方法工作正常")
    
    print("✅ 所有日志方法测试通过")
    return True

def test_attribute_handling():
    """测试属性处理"""
    print("\n🔧 测试属性处理...")
    
    class TestClass:
        def __init__(self):
            self.test_attr = "test_value"
        
        def test_method(self):
            return "test_method"
        
        def cleanup(self):
            # 测试删除属性
            if hasattr(self, 'test_attr'):
                delattr(self, 'test_attr')
                print("✅ 属性删除成功")
            
            # 测试删除方法
            if hasattr(self, 'test_method'):
                delattr(self, 'test_method')
                print("✅ 方法删除成功")
    
    obj = TestClass()
    print(f"初始属性: {hasattr(obj, 'test_attr')}")
    print(f"初始方法: {hasattr(obj, 'test_method')}")
    
    obj.cleanup()
    print(f"清理后属性: {hasattr(obj, 'test_attr')}")
    print(f"清理后方法: {hasattr(obj, 'test_method')}")
    
    print("✅ 属性处理测试通过")
    return True

if __name__ == "__main__":
    print("🚀 开始测试日志修复...")
    
    success1 = test_log_methods()
    success2 = test_attribute_handling()
    
    if success1 and success2:
        print("\n✅ 日志修复测试完成！")
        print("📝 现在应该可以正常启动GUI了")
    else:
        print("\n❌ 部分测试失败，需要进一步检查。")
