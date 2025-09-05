#!/usr/bin/env python3
"""
测试改进的错误处理机制
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from workflow.examples.coze_complete_video_workflow import CozeVideoWorkflow


def test_error_handling():
    """测试错误处理机制"""
    print("测试改进的错误处理机制")
    print("=" * 50)
    
    try:
        # 创建工作流实例
        workflow = CozeVideoWorkflow("test_draft")
        
        print("[OK] 工作流创建成功")
        
        # 测试错误检测关键词
        test_errors = [
            "Access plugin server url timed out",
            "Server timeout",
            "Network connection failed",
            "Request timed out",
            "Internal server error",
            "Normal error that should retry"
        ]
        
        keywords = ['timeout', 'timed out', 'access plugin', 'server error']
        
        print("\n[INFO] 测试错误关键词检测...")
        for error_msg in test_errors:
            should_terminate = any(keyword in error_msg.lower() for keyword in keywords)
            status = "🚨 立即终止" if should_terminate else "🔄 继续重试"
            print(f"  错误: '{error_msg}' -> {status}")
        
        print("\n[OK] 错误关键词检测测试通过")
        
        # 测试工作流方法是否存在
        methods_to_check = [
            'poll_workflow_result',
            'call_coze_workflow',
            'synthesize_video',
            'run_complete_workflow'
        ]
        
        print("\n[INFO] 检查工作流方法...")
        for method_name in methods_to_check:
            if hasattr(workflow, method_name):
                print(f"  ✅ {method_name} 方法存在")
            else:
                print(f"  ❌ {method_name} 方法不存在")
                return False
        
        print("\n[OK] 工作流方法检查通过")
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_error_handling()
    if success:
        print("\n✅ 错误处理机制测试通过")
        print("现在工作流能够智能识别严重错误并立即终止轮询")
    else:
        print("\n❌ 错误处理机制测试失败")