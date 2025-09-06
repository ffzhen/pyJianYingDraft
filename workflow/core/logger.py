"""
日志系统

提供统一的日志记录功能
"""

import logging
import os
from datetime import datetime
from typing import Optional

class WorkflowLogger:
    """工作流日志记录器"""
    
    def __init__(self, project_name: str = "workflow", log_dir: str = "workflow_logs"):
        self.project_name = project_name
        self.log_dir = log_dir
        self.logger = None
        self.log_filename = None
        self._setup_logger()
        
    def _setup_logger(self):
        """设置日志记录器"""
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 生成日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"{self.log_dir}/workflow_{timestamp}.log"
        
        # 设置日志格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # 创建logger
        self.logger = logging.getLogger(f'VideoEditingWorkflow_{timestamp}')
        self.logger.setLevel(logging.DEBUG)
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.info(f"🚀 视频编辑工作流开始 - 项目: {self.project_name}")
        self.info(f"📝 日志保存至: {self.log_filename}")
        
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)
        
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
        
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)
        
    def error(self, message: str):
        """错误日志"""
        self.logger.error(message)
        
    def save_summary(self, summary_data: dict):
        """保存工作流摘要"""
        import json
        
        try:
            summary_filename = self.log_filename.replace('.log', '_summary.json')
            with open(summary_filename, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
            
            self.info(f"📊 工作流摘要已保存: {summary_filename}")
        except Exception as e:
            self.error(f"保存工作流摘要时出错: {e}")