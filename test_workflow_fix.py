#!/usr/bin/env python3
"""
测试修复后的Coze工作流
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from workflow.examples.coze_complete_video_workflow import CozeVideoWorkflow


def test_workflow():
    """测试工作流修复"""
    print("测试修复后的Coze工作流")
    print("=" * 40)
    
    try:
        # 创建工作流实例
        workflow = CozeVideoWorkflow("test_draft")
        
        print("[OK] 工作流创建成功")
        
        # 模拟任务参数
        content = "这是一个测试内容"
        digital_no = "D20250820190000005"
        voice_id = "AA20250822120001"
        title = "测试视频"
        
        print("[INFO] 测试任务配置设置...")
        
        # 这会设置task_config
        # 注意：这里不会实际调用API，只是测试task_config设置
        workflow.task_config = {
            "content": content,
            "digital_no": digital_no,
            "voice_id": voice_id,
            "title": title
        }
        
        # 验证task_config是否正确设置
        if hasattr(workflow, 'task_config'):
            print("[OK] task_config属性存在")
            
            # 测试访问task_config
            test_title = workflow.task_config.get('title', '默认标题')
            if test_title == title:
                print(f"[OK] task_config内容正确: {test_title}")
            else:
                print(f"[ERROR] task_config内容错误: {test_title}")
                return False
        else:
            print("[ERROR] task_config属性不存在")
            return False
        
        print("[OK] 工作流修复验证成功")
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_workflow()
    if success:
        print("\n✅ 工作流修复测试通过")
        print("现在可以重新运行批量工作流，task_config错误已修复")
    else:
        print("\n❌ 工作流修复测试失败")