import json

# 加载测试结果
with open('test_result_20250904_163636.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== 测试结果分析 ===")
print(f"测试时间: {data['test_time']}")
print(f"原始记录数: {data['statistics']['total_records']}")
print(f"有效任务数: {data['statistics']['valid_tasks']}")
print(f"账号缓存: {data['statistics']['account_cache']} 条")
print(f"音色缓存: {data['statistics']['voice_cache']} 个账号")
print(f"数字人缓存: {data['statistics']['digital_human_cache']} 个账号")

print("\n=== 生成的任务数据 ===")
for i, task in enumerate(data['sample_tasks']):
    print(f"\n任务 {i+1}:")
    print(f"  ID: {task['id']}")
    print(f"  标题: {task['title']}")
    print(f"  关联账号: {task['account_id']}")
    print(f"  音色ID: {task['voice_id']}")
    print(f"  数字人编号: {task['digital_no']}")
    print(f"  项目名称: {task['project_name']}")

print("\n=== 数据格式分析 ===")
print("标题格式:", type(data['sample_tasks'][0]['title']))
print("内容格式:", type(data['sample_tasks'][0]['content']))
print("数字人编号格式:", type(data['sample_tasks'][0]['digital_no']))

# 检查是否有文本内容需要提取
sample_task = data['sample_tasks'][0]
if isinstance(sample_task['title'], list) and sample_task['title']:
    print(f"\n标题是富文本格式，包含 {len(sample_task['title'])} 个文本块")
    for j, text_block in enumerate(sample_task['title'][:3]):
        print(f"  文本块 {j+1}: {text_block.get('text', '')[:50]}...")

if isinstance(sample_task['content'], list) and sample_task['content']:
    print(f"\n内容是富文本格式，包含 {len(sample_task['content'])} 个文本块")
    for j, text_block in enumerate(sample_task['content'][:3]):
        print(f"  文本块 {j+1}: {text_block.get('text', '')[:50]}...")