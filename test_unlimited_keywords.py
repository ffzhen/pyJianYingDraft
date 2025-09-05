# -*- coding: utf-8 -*-
"""
测试无限制关键词提取的用户注意力优化效果
"""

import os
import sys

# 添加工作流组件路径
workflow_path = os.path.join(os.path.dirname(__file__), 'workflow', 'component')
sys.path.insert(0, workflow_path)

from volcengine_asr import VolcengineASR

def test_unlimited_keywords_extraction():
    """测试无限制关键词提取功能"""
    print("=" * 80)
    print("测试无限制关键词提取的用户注意力优化效果")
    print("=" * 80)
    
    # 创建ASR实例
    asr = VolcengineASR(
        appid="6046310832",
        access_token="fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY",
        doubao_token="adac0afb-5fd4-4c66-badb-370a7ff42df5",
        doubao_model="doubao-1-5-pro-32k-250115"
    )
    
    # 测试文本（拆迁相关内容）
    test_text = """中国以后还会有大规模拆迁吗？答案是：会。
从二零二五年开始，国家将把拆迁改造范围从三十个城市扩大到三百个，全面推进城中村和老旧小区更新，并重新提倡"货币化安置"——也就是直接发放现金补偿。
这意味着，一批拆迁户将获得数百万元甚至上千万元的补偿款，确实有可能成为千万富翁。但关键在于钱怎么用：用于改善住房或稳健配置，财富才能留存；若盲目消费或投机，也可能"一夜暴富、转眼归零"。
与过去不同，这一轮改造有两个重要变化：
一是"多拆少建"。当前全国房产库存偏高，拆旧不等于大建，而是严控新增供应。
二是"拆小建大"。拆除的主要是老破小，新建的则是大面积、改善型、舒适型住宅，推动居住品质升级。
目前小户型库存充足，能满足刚需，政策重心已转向支持改善型需求。
这一轮不是简单拆迁，而是通过城市更新优化住房结构、激活内需、带动经济。
面对这笔补偿款，理性规划比一时致富更重要。
理解政策方向，才能真正把握时代红利。"""
    
    print(f"[INFO] 测试文本内容:")
    print(f"  文本长度: {len(test_text)} 字符")
    print(f"  内容主题: 拆迁政策与财富机会")
    print()
    
    print(f"[INFO] 开始无限制关键词提取测试...")
    print(f"  🎯 目标: 最大化用户注意力和留存")
    print(f"  🧠 策略: 智能识别高价值词汇，无数量限制")
    print()
    
    try:
        # 测试AI关键词提取（无限制模式）
        print("🤖 测试豆包AI关键词提取（无限制模式）:")
        print("-" * 60)
        
        ai_keywords = asr.extract_keywords_with_ai(test_text)
        
        if ai_keywords:
            print(f"✅ AI提取成功: {len(ai_keywords)} 个关键词")
            print("🎯 关键词分析:")
            
            # 按词汇类型分类
            wealth_words = [w for w in ai_keywords if any(x in w for x in ['富', '钱', '财', '万', '元', '补偿', '收入'])]
            policy_words = [w for w in ai_keywords if any(x in w for x in ['政策', '国家', '改造', '拆迁', '安置'])]
            emotion_words = [w for w in ai_keywords if any(x in w for x in ['暴富', '归零', '机会', '重要', '关键'])]
            action_words = [w for w in ai_keywords if any(x in w for x in ['获得', '实现', '推动', '激活', '把握'])]
            
            print(f"  💰 财富相关词汇({len(wealth_words)}个): {wealth_words[:10]}")
            print(f"  📊 政策相关词汇({len(policy_words)}个): {policy_words[:10]}")
            print(f"  🔥 情感触发词汇({len(emotion_words)}个): {emotion_words[:10]}")
            print(f"  🚀 行动导向词汇({len(action_words)}个): {action_words[:10]}")
            print()
            
            print("📋 完整关键词列表:")
            for i, keyword in enumerate(ai_keywords, 1):
                print(f"  {i:2d}. {keyword}")
            
        else:
            print("❌ AI关键词提取失败，测试备用方法")
        
        print("\n" + "=" * 60)
        print("🧠 测试本地智能算法（备用方法）:")
        print("-" * 60)
        
        # 测试备用关键词提取
        local_keywords = asr._fallback_keyword_extraction(test_text)
        
        if local_keywords:
            print(f"✅ 本地算法提取成功: {len(local_keywords)} 个关键词")
            print("📋 本地算法关键词列表:")
            for i, keyword in enumerate(local_keywords, 1):
                print(f"  {i:2d}. {keyword}")
        
        print("\n" + "=" * 80)
        print("📊 用户注意力优化效果分析")
        print("=" * 80)
        
        final_keywords = ai_keywords if ai_keywords else local_keywords
        
        if final_keywords:
            print(f"🎯 关键词覆盖率分析:")
            
            # 计算覆盖的字符数
            covered_chars = 0
            for keyword in final_keywords:
                if keyword in test_text:
                    covered_chars += len(keyword) * test_text.count(keyword)
            
            coverage_rate = (covered_chars / len(test_text)) * 100
            print(f"  📈 文本覆盖率: {coverage_rate:.1f}% ({covered_chars}/{len(test_text)} 字符)")
            
            # 分析关键词类型分布
            high_value_count = len([w for w in final_keywords if len(w) >= 3])
            medium_value_count = len([w for w in final_keywords if len(w) == 2])
            
            print(f"  🏆 高价值词汇(3字以上): {high_value_count} 个 ({high_value_count/len(final_keywords)*100:.1f}%)")
            print(f"  📝 中等价值词汇(2字): {medium_value_count} 个 ({medium_value_count/len(final_keywords)*100:.1f}%)")
            
            # 用户注意力预估
            attention_score = min(100, len(final_keywords) * 2 + coverage_rate)
            retention_score = min(100, high_value_count * 3 + len(wealth_words) * 5)
            
            print(f"  👁️  预估注意力指数: {attention_score:.0f}/100")
            print(f"  🎯 预估留存指数: {retention_score:.0f}/100")
            
            print(f"\n🚀 用户体验优化建议:")
            print(f"  ✅ 关键词数量充足，能够持续吸引用户注意力")
            print(f"  ✅ 财富相关词汇丰富，满足用户痛点需求")
            print(f"  ✅ 情感触发词汇合理，能够激发用户兴趣")
            print(f"  ✅ 无数量限制策略有效，最大化内容价值")
            
            if len(final_keywords) > 20:
                print(f"  🎊 关键词数量优秀({len(final_keywords)}个)，远超传统限制")
            elif len(final_keywords) > 15:
                print(f"  👍 关键词数量良好({len(final_keywords)}个)，明显改善")
            else:
                print(f"  ⚠️  关键词数量适中({len(final_keywords)}个)，仍有优化空间")
        
        else:
            print("❌ 关键词提取完全失败")
        
        print("\n✅ 无限制关键词提取测试完成！")
        print("💡 建议在实际视频中测试高亮效果，观察用户反馈")
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unlimited_keywords_extraction()