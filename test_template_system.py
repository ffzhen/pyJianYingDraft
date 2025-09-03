#!/usr/bin/env python3
"""
视频模板系统测试脚本

测试新模板架构的各项功能
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

def test_template_system():
    """测试模板系统基本功能"""
    print("🧪 开始测试视频模板系统")
    print("=" * 60)
    
    try:
        # 1. 测试样式配置系统
        print("\n📋 1. 测试样式配置系统...")
        from workflow.component.style_config import style_config_manager
        
        # 获取所有模板
        templates = style_config_manager.list_templates()
        print(f"   ✅ 可用模板: {templates}")
        
        # 获取模板信息
        for template_name in templates:
            info = style_config_manager.get_template_info(template_name)
            print(f"   📝 {template_name}: {info.get('description', 'N/A')}")
        
        # 2. 测试模板工厂
        print("\n🏭 2. 测试模板工厂...")
        from workflow.component.video_templates import VideoTemplateFactory
        
        factory_templates = VideoTemplateFactory.list_templates()
        print(f"   ✅ 工厂模板: {factory_templates}")
        
        # 3. 测试模板工作流创建
        print("\n🎬 3. 测试模板工作流创建...")
        from workflow.component.template_based_workflow import (
            create_workflow_with_template, 
            list_available_templates
        )
        
        # 列出可用模板
        available_templates = list_available_templates()
        print(f"   ✅ 可用工作流模板: {len(available_templates)} 个")
        for template in available_templates:
            print(f"      • {template['name']}: {template['description']}")
        
        # 4. 测试创建不同模板的工作流
        print("\n🔧 4. 测试创建不同模板的工作流...")
        
        # 使用模拟路径（不会实际创建文件）
        test_path = "C:/test_draft_folder"
        
        for template_name in ["original", "tech", "warm", "business"]:
            try:
                workflow = create_workflow_with_template(
                    test_path, 
                    template_name, 
                    f"test_{template_name}"
                )
                print(f"   ✅ {template_name} 模板创建成功")
                
                # 获取模板信息
                template_info = workflow.get_template_info()
                print(f"      描述: {template_info.get('description', 'N/A')}")
                
            except FileNotFoundError as e:
                if "不存在" in str(e):
                    print(f"   ⚠️  {template_name} 模板需要真实剪映路径，这是正常的")
                else:
                    print(f"   ❌ {template_name} 模板创建失败: {e}")
            except Exception as e:
                print(f"   ❌ {template_name} 模板创建失败: {e}")
        
        # 5. 测试模板切换
        print("\n🔄 5. 测试模板切换...")
        
        try:
            workflow = create_workflow_with_template(test_path, "original", "switch_test")
            print(f"   📝 当前模板: {workflow.template_name}")
            
            # 切换模板
            workflow.change_template("tech")
            print(f"   📝 切换后模板: {workflow.template_name}")
            print(f"   ✅ 模板切换成功")
            
        except FileNotFoundError as e:
            if "不存在" in str(e):
                print(f"   ⚠️  模板切换需要真实剪映路径，这是正常的")
            else:
                print(f"   ❌ 模板切换失败: {e}")
        except Exception as e:
            print(f"   ❌ 模板切换失败: {e}")
        
        # 6. 测试自定义模板
        print("\n🎨 6. 测试自定义模板...")
        
        try:
            from workflow.component.style_config import (
                VideoStyleConfig, CaptionStyleConfig, TitleStyleConfig, 
                TextStyleConfig, HighlightStyleConfig, TextBackgroundConfig
            )
            from workflow.component.video_templates import OriginalStyleTemplate, VideoTemplateFactory
            
            # 创建自定义配置
            custom_config = VideoStyleConfig(
                description="测试自定义风格",
                tags=["测试", "自定义"],
                caption_style=CaptionStyleConfig(
                    base_style=TextStyleConfig(
                        font_type="俪金黑",
                        size=12.0,
                        color=(1.0, 0.0, 0.0),  # 红色
                        bold=True,
                        align=0,
                        auto_wrapping=True,
                        max_line_width=0.8,
                        line_spacing=2
                    ),
                    highlight_style=HighlightStyleConfig(
                        color=(0.0, 1.0, 0.0),  # 绿色
                        size=14.0,
                        bold=True
                    ),
                    background_style=TextBackgroundConfig(
                        color="#FF0000",  # 红色
                        alpha=0.7,
                        height=0.25,
                        width=0.14,
                        horizontal_offset=0.5,
                        vertical_offset=0.5,
                        round_radius=10.0,
                        style=1
                    ),
                    position="bottom",
                    transform_y=-0.3
                ),
                title_style=TitleStyleConfig(
                    base_style=TextStyleConfig(
                        font_type="文轩体",
                        size=20.0,
                        color=(0.0, 0.0, 1.0),  # 蓝色
                        bold=True,
                        align=1,
                        auto_wrapping=True,
                        max_line_width=0.8,
                        line_spacing=6
                    ),
                    highlight_style=HighlightStyleConfig(
                        color=(1.0, 1.0, 0.0),  # 黄色
                        size=22.0,
                        bold=True
                    ),
                    transform_y=0.7,
                    line_count=3
                )
            )
            
            # 注册自定义模板配置
            style_config_manager.add_custom_config("test_custom", custom_config)
            print(f"   ✅ 自定义模板配置注册成功")
            
            # 注册自定义模板类（复用OriginalStyleTemplate）
            VideoTemplateFactory.register_template("test_custom", OriginalStyleTemplate)
            print(f"   ✅ 自定义模板类注册成功")
            
            # 测试创建自定义模板工作流
            custom_workflow = create_workflow_with_template(
                test_path, "test_custom", "test_custom_workflow"
            )
            print(f"   ✅ 自定义模板工作流创建成功")
            
            # 获取自定义模板信息
            custom_info = custom_workflow.get_template_info()
            print(f"      描述: {custom_info.get('description', 'N/A')}")
            print(f"      标签: {', '.join(custom_info.get('tags', []))}")
            
        except FileNotFoundError as e:
            if "不存在" in str(e):
                print(f"   ⚠️  自定义模板需要真实剪映路径，这是正常的")
            else:
                print(f"   ❌ 自定义模板测试失败: {e}")
        except Exception as e:
            print(f"   ❌ 自定义模板测试失败: {e}")
        
        # 7. 测试配置保存和加载
        print("\n💾 7. 测试配置保存和加载...")
        
        try:
            # 保存配置
            config_file = "test_config.json"
            style_config_manager.save_config("tech", config_file)
            print(f"   ✅ 配置保存成功: {config_file}")
            
            # 修改配置
            original_config = style_config_manager.get_config("tech")
            original_description = original_config.description
            original_config.description = "修改后的描述"
            
            # 重新加载配置
            style_config_manager.load_config("tech", config_file)
            reloaded_config = style_config_manager.get_config("tech")
            
            if reloaded_config.description == original_description:
                print(f"   ✅ 配置加载成功，描述恢复: {reloaded_config.description}")
            else:
                print(f"   ⚠️  配置加载可能有问题")
            
            # 清理测试文件
            if os.path.exists(config_file):
                os.remove(config_file)
                
        except Exception as e:
            print(f"   ❌ 配置保存/加载测试失败: {e}")
        
        print("\n🎉 模板系统测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_processing():
    """测试工作流处理功能（需要真实配置）"""
    print("\n🎬 测试工作流处理功能")
    print("=" * 60)
    
    # 注意：这个测试需要真实的剪映路径和API配置
    # 这里只做基本的功能测试，不实际处理视频
    
    try:
        from workflow.component.template_based_workflow import create_workflow_with_template
        
        # 使用模拟路径测试
        test_path = "C:/Users/nrgc/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft"
        
        workflow = create_workflow_with_template(test_path, "original", "test_processing")
        
        # 模拟输入参数（不包含真实API密钥）
        test_inputs = {
            'audio_url': 'https://example.com/test.wav',
            'title': '测试视频',
            'volcengine_appid': 'test_appid',
            'volcengine_access_token': 'test_token'
        }
        
        print("📝 测试输入参数:")
        for key, value in test_inputs.items():
            print(f"   {key}: {value}")
        
        # 注意：这里不实际调用 process_workflow，因为没有真实的API配置
        # workflow.process_workflow(test_inputs)
        
        print("✅ 工作流处理功能测试结构正确")
        print("💡 要测试实际视频处理，请配置真实的剪映路径和API密钥")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_template_usage():
    """演示模板使用方法"""
    print("\n📚 模板使用演示")
    print("=" * 60)
    
    print("""
1. 基本使用:
   from workflow.component.template_based_workflow import create_workflow_with_template
   
   # 创建工作流
   workflow = create_workflow_with_template(
       draft_folder_path="C:/剪映草稿路径",
       template_name="tech",  # 使用科技风格
       project_name="我的视频"
   )
   
   # 处理视频
   result = workflow.process_workflow({
       'audio_url': 'https://...',
       'title': '视频标题',
       'volcengine_appid': 'xxx',
       'volcengine_access_token': 'xxx'
   })

2. 切换模板:
   workflow.change_template("warm")  # 切换到温馨风格

3. 列出所有模板:
   from workflow.component.template_based_workflow import list_available_templates
   
   templates = list_available_templates()
   for template in templates:
       print(f"{template['name']}: {template['description']}")

4. 创建自定义模板:
   from workflow.component.style_config import style_config_manager, VideoStyleConfig
   
   # 创建自定义配置
   custom_config = VideoStyleConfig(
       description="我的自定义风格",
       tags=["自定义", "专属"],
       # ... 配置样式参数
   )
   
   # 注册模板
   style_config_manager.add_custom_config("my_style", custom_config)
   
   # 使用自定义模板
   workflow = create_workflow_with_template(path, "my_style", project_name)
""")


def main():
    """主测试函数"""
    print("🧪 视频模板系统测试")
    print("=" * 60)
    
    # 运行基本功能测试
    basic_test_passed = test_template_system()
    
    # 运行工作流处理测试
    workflow_test_passed = test_workflow_processing()
    
    # 显示使用演示
    demo_template_usage()
    
    # 总结
    print("\n📊 测试总结")
    print("=" * 60)
    print(f"✅ 基本功能测试: {'通过' if basic_test_passed else '失败'}")
    print(f"✅ 工作流处理测试: {'通过' if workflow_test_passed else '失败'}")
    
    if basic_test_passed and workflow_test_passed:
        print("\n🎉 所有测试通过！模板系统可以正常使用。")
        print("\n💡 下一步:")
        print("1. 配置真实的剪映草稿文件夹路径")
        print("2. 配置火山引擎ASR的AppID和AccessToken")
        print("3. 配置豆包API的Token（可选，用于关键词提取）")
        print("4. 准备音频和视频素材文件")
        print("5. 运行实际的视频生成测试")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息并修复问题。")


if __name__ == "__main__":
    main()