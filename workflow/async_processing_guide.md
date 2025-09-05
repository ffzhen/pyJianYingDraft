# 异步Coze批量处理使用指南

## 🚀 核心优势

### 传统处理方式的问题：
- **串行等待**：提交Coze → 轮询等待 → 视频合成（每个任务顺序执行）
- **低效利用**：Coze API支持16并发，但传统方式只能2-3个并发
- **时间浪费**：轮询等待期间CPU完全空闲

### 异步处理的优势：
- **并发提交**：一次性提交16个Coze工作流
- **实时响应**：一旦Coze返回结果，立即开始视频合成
- **资源最大化**：Coze处理期间，CPU可以处理已完成的视频合成
- **效率提升**：预估提升3-5倍处理效率

## 📋 使用方法

### 1. 配置文件设置

首先需要在配置文件中添加Coze相关配置：

```json
{
  "workflow_config": {
    "coze_config": {
      "token": "你的Coze API Token",
      "workflow_id": "你的Coze工作流ID"
    },
    "max_coze_concurrent": 16,     // Coze最大并发数
    "max_synthesis_workers": 4,    // 视频合成最大并发数
    "poll_interval": 30            // 轮询间隔(秒)
  }
}
```

### 2. 运行异步批量处理

```bash
# 基本用法
python workflow/feishu_async_batch_workflow.py --config workflow/feishu_config_template.json

# 指定并发参数
python workflow/feishu_async_batch_workflow.py --config workflow/feishu_config_template.json --max-coze 16 --max-synthesis 4 --poll-interval 30

# 处理特定任务
python workflow/feishu_async_batch_workflow.py --config workflow/feishu_config_template.json --include task_id_1 task_id_2

# 排除特定任务
python workflow/feishu_async_batch_workflow.py --config workflow/feishu_config_template.json --exclude task_id_3 task_id_4
```

## 🔄 处理流程

### 阶段1: 批量提交Coze工作流
```
📤 同时提交16个Coze工作流请求
├── 任务1 → Coze API → execute_id_1
├── 任务2 → Coze API → execute_id_2
├── ...
└── 任务16 → Coze API → execute_id_16
```

### 阶段2: 智能监听和实时合成
```
👁️ 每30秒并发检查所有execute_id状态
├── execute_id_1 完成 → 立即触发视频合成
├── execute_id_5 完成 → 立即触发视频合成
├── execute_id_3 仍在运行中 → 继续等待
└── execute_id_7 完成 → 立即触发视频合成

🎬 多个视频并发合成（最多4个并发）
├── 任务1视频合成中...
├── 任务5视频合成中...
├── 任务7排队等待...
└── 任务12排队等待...
```

## 📊 效果对比

### 传统串行处理（假设20个任务）:
```
时间轴: 0-----5-----10----15----20----25----30分钟
任务1: [Coze等待5分钟][合成1分钟]
任务2:           [Coze等待5分钟][合成1分钟]
任务3:                     [Coze等待5分钟][合成1分钟]
...
总耗时: 20 * 6分钟 = 120分钟
```

### 异步并发处理:
```
时间轴: 0-----5-----10----15----20分钟
批量提交: [16个任务同时提交] <- 1分钟
Coze处理: [16个任务并发处理] <- 5分钟
实时合成: [陆续完成，立即合成] <- 8分钟
剩余4个: [第二批提交+处理] <- 6分钟
总耗时: 约20分钟
```

**效率提升: 120分钟 → 20分钟 = 6倍提升！**

## 🎯 最佳实践

### 1. 并发参数调优
- **max_coze_concurrent**: 建议设为16（Coze API上限）
- **max_synthesis_workers**: 根据CPU性能调整（建议4-8）
- **poll_interval**: 建议30-60秒（避免过于频繁的API调用）

### 2. 错误处理
- 自动重试机制：失败任务会自动重试3次
- 智能降级：如果Coze API达到限制，会自动排队等待
- 详细日志：所有处理过程都有详细日志记录

### 3. 监控和调试
```bash
# 实时查看处理进度
tail -f workflow_logs/workflow_*.log

# 查看详细结果
cat feishu_async_results_*.json
```

## ⚠️ 注意事项

1. **API限制**: Coze API有并发限制，超出会返回429错误
2. **内存使用**: 大量任务会占用较多内存，建议分批处理
3. **网络稳定**: 长时间运行需要稳定的网络连接
4. **存储空间**: 视频文件较大，确保有足够存储空间

## 🔧 故障排除

### 问题1: Coze API调用失败
```
解决方案:
1. 检查Coze Token是否有效
2. 检查工作流ID是否正确
3. 确认API配额是否充足
```

### 问题2: 视频合成失败
```
解决方案:
1. 检查剪映草稿文件夹路径
2. 确认本地存储空间充足
3. 检查视频合成参数配置
```

### 问题3: 内存占用过高
```
解决方案:
1. 减少max_coze_concurrent参数
2. 减少max_synthesis_workers参数
3. 分批处理大量任务
```

## 📈 性能监控指标

异步处理器会自动记录以下指标：
- **总任务数**: 批量处理的任务总数
- **成功率**: 成功完成的任务百分比
- **平均耗时**: 每个任务的平均处理时间
- **并发利用率**: API并发的实际利用情况
- **错误分布**: 各类错误的统计分析

通过这些指标，可以持续优化处理参数，达到最佳效果。