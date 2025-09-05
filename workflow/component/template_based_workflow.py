# -*- coding: utf-8 -*-
"""
基于模板系统的视频工作流实现

使用新的模板架构重构原有的视频合成逻辑
"""

import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

# 添加本地 pyJianYingDraft 模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

from .video_templates import VideoTemplateFactory
from .style_config import style_config_manager, HighlightStyleConfig, TextBackgroundConfig


class TemplateBasedVideoWorkflow:
    """基于模板系统的视频工作流"""
    
    def __init__(self, draft_folder_path: str, template_name: str = "original", project_name: str = None):
        """
        初始化工作流
        
        Args:
            draft_folder_path: 剪映草稿文件夹路径
            template_name: 模板名称
            project_name: 项目名称
        """
        self.draft_folder_path = draft_folder_path
        self.template_name = template_name
        self.project_name = project_name
        
        # 获取模板配置
        self.style_config = style_config_manager.get_config(template_name)
        if not self.style_config:
            raise ValueError(f"未找到模板 '{template_name}' 的配置")
        
        # 创建模板实例
        self.template = VideoTemplateFactory.create_template(
            template_name, draft_folder_path, project_name, self.style_config
        )
        
        print(f"🎬 已初始化模板工作流: {template_name}")
        print(f"📋 模板描述: {self.style_config.description}")
        print(f"🏷️  模板标签: {', '.join(self.style_config.tags)}")
    
    def process_workflow(self, inputs: Dict[str, Any]) -> str:
        """
        处理视频工作流
        
        Args:
            inputs: 输入参数，包含：
                - audio_url: 音频URL (必需)
                - title: 视频标题 (可选)
                - digital_video_url: 数字人视频URL (可选)
                - material_video_url: 素材视频URL (可选)
                - volcengine_appid: 火山引擎AppID (必需)
                - volcengine_access_token: 火山引擎访问令牌 (必需)
                - doubao_token: 豆包API令牌 (可选)
                - doubao_model: 豆包模型名称 (可选)
                - background_music_path: 背景音乐路径 (可选)
                - background_music_volume: 背景音乐音量 (可选)
                
        Returns:
            草稿保存路径
        """
        print(f"🎯 开始处理模板视频工作流: {self.template_name}")
        print(f"📋 使用模板: {self.style_config.description}")
        
        # 验证必需参数
        required_params = ['audio_url', 'volcengine_appid', 'volcengine_access_token']
        missing_params = [param for param in required_params if not inputs.get(param)]
        if missing_params:
            raise ValueError(f"缺少必需参数: {', '.join(missing_params)}")
        
        # 设置项目名称
        if not self.project_name:
            title = inputs.get('title', '')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if title:
                # 清理标题作为项目名称
                import re
                clean_title = re.sub(r'[^\w\u4e00-\u9fff]', '_', title)[:20]
                self.project_name = f"{clean_title}_{timestamp}"
            else:
                self.project_name = f"{self.template_name}_video_{timestamp}"
            
            # 重新创建模板实例
            self.template = VideoTemplateFactory.create_template(
                self.template_name, self.draft_folder_path, self.project_name, self.style_config
            )
        
        print(f"📁 项目名称: {self.project_name}")
        
        # 调用模板的工作流处理
        result = self.template.process_workflow(inputs)
        
        print(f"✅ 模板工作流处理完成: {result}")
        return result
    
    def get_template_info(self) -> Dict[str, Any]:
        """获取模板信息"""
        return VideoTemplateFactory.get_template_info(self.template_name)
    
    def change_template(self, new_template_name: str):
        """更换模板"""
        if new_template_name not in VideoTemplateFactory.list_templates():
            raise ValueError(f"不支持的模板: {new_template_name}")
        
        self.template_name = new_template_name
        self.style_config = style_config_manager.get_config(new_template_name)
        
        # 重新创建模板实例
        self.template = VideoTemplateFactory.create_template(
            new_template_name, self.draft_folder_path, self.project_name, self.style_config
        )
        
        print(f"🔄 已切换到模板: {new_template_name}")


def list_available_templates() -> List[Dict[str, Any]]:
    """列出所有可用模板"""
    templates = []
    for template_name in VideoTemplateFactory.list_templates():
        info = VideoTemplateFactory.get_template_info(template_name)
        templates.append(info)
    return templates


def create_workflow_with_template(draft_folder_path: str, template_name: str, 
                                project_name: str = None) -> TemplateBasedVideoWorkflow:
    """
    使用指定模板创建工作流
    
    Args:
        draft_folder_path: 剪映草稿文件夹路径
        template_name: 模板名称
        project_name: 项目名称
        
    Returns:
        工作流实例
    """
    return TemplateBasedVideoWorkflow(draft_folder_path, template_name, project_name)


# 示例使用函数
def demo_template_usage():
    """演示模板使用"""
    print("🎬 视频模板系统演示")
    print("=" * 50)
    
    # 列出所有可用模板
    templates = list_available_templates()
    print(f"📋 可用模板 ({len(templates)} 个):")
    for template in templates:
        print(f"   • {template['name']}: {template['description']}")
        print(f"     标签: {', '.join(template.get('tags', []))}")
        print(f"     字体: {template.get('caption_font', 'N/A')}")
        print()
    
    # 配置路径
    draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    # 测试不同模板
    test_templates = ["original", "tech", "warm", "business"]
    
    for template_name in test_templates:
        try:
            print(f"\n🧪 测试模板: {template_name}")
            
            # 创建工作流
            workflow = create_workflow_with_template(
                draft_folder_path, 
                template_name,
                f"demo_{template_name}"
            )
            
            # 获取模板信息
            template_info = workflow.get_template_info()
            print(f"   描述: {template_info.get('description', 'N/A')}")
            print(f"   标签: {', '.join(template_info.get('tags', []))}")
            
            print(f"   ✅ 模板 '{template_name}' 加载成功")
            
        except Exception as e:
            print(f"   ❌ 模板 '{template_name}' 加载失败: {e}")
    
    print("\n🎉 模板演示完成")


def create_custom_template_example():
    """创建自定义模板示例"""
    print("🎨 创建自定义模板示例")
    print("=" * 50)
    
    # 创建自定义样式配置
    from .style_config import VideoStyleConfig, CaptionStyleConfig, TitleStyleConfig, TextStyleConfig
    
    custom_config = VideoStyleConfig(
        description="自定义炫彩风格",
        tags=["自定义", "炫彩", "活泼"],
        caption_style=CaptionStyleConfig(
            base_style=TextStyleConfig(
                font_type="俪金黑",
                size=9.0,
                color=(1.0, 0.0, 1.0),  # 紫色
                bold=True,
                align=0,
                auto_wrapping=True,
                max_line_width=0.82,
                line_spacing=2,
                scale_x=1.3,
                scale_y=1.3
            ),
            highlight_style=HighlightStyleConfig(
                color=(1.0, 1.0, 0.0),  # 黄色
                size=11.0,
                bold=True
            ),
            background_style=TextBackgroundConfig(
                color="#FF00FF",  # 紫色
                alpha=0.7,
                height=0.25,
                width=0.14,
                horizontal_offset=0.5,
                vertical_offset=0.5,
                round_radius=15.0,
                style=1
            ),
            position="bottom",
            transform_y=-0.25
        ),
        title_style=TitleStyleConfig(
            base_style=TextStyleConfig(
                font_type="文轩体",
                size=18.0,
                color=(1.0, 0.5, 0.0),  # 橙色
                bold=True,
                align=1,
                auto_wrapping=True,
                max_line_width=0.8,
                line_spacing=6
            ),
            highlight_style=HighlightStyleConfig(
                color=(1.0, 1.0, 0.0),  # 黄色
                size=20.0,
                bold=True
            ),
            background_style=TextBackgroundConfig(
                color="#FFA500",  # 橙色
                alpha=0.6,
                height=0.48,
                width=1.0,
                horizontal_offset=0.5,
                vertical_offset=0.5,
                round_radius=20.0,
                style=1
            ),
            transform_y=0.75,
            line_count=3
        )
    )
    
    # 注册自定义模板
    style_config_manager.add_custom_config("custom_colorful", custom_config)
    
    print("✅ 自定义模板 'custom_colorful' 已创建")
    print("   描述: 自定义炫彩风格")
    print("   标签: 自定义, 炫彩, 活泼")
    print("   字幕颜色: 紫色")
    print("   高亮颜色: 黄色")
    print("   背景颜色: 紫色")
    
    # 测试自定义模板
    try:
        draft_folder_path = r"C:\Users\nrgc\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
        workflow = create_workflow_with_template(
            draft_folder_path,
            "custom_colorful",
            "demo_custom"
        )
        print("✅ 自定义模板测试成功")
    except Exception as e:
        print(f"❌ 自定义模板测试失败: {e}")


if __name__ == "__main__":
    # 运行演示
    demo_template_usage()
    create_custom_template_example()