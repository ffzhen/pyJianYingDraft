"""
素材管理器

负责素材的下载和管理
"""

import os
import requests
import tempfile
import uuid
import time
from typing import Optional
from ..core.base import BaseProcessor, WorkflowContext

class MaterialManager(BaseProcessor):
    """素材管理器"""
    
    def process(self, *args, **kwargs):
        """占位方法"""  
        pass
        
    def download_material(self, url: str, local_path: str) -> str:
        """下载网络素材到本地
        
        Args:
            url: 素材URL
            local_path: 本地保存路径
            
        Returns:
            本地文件路径（如果下载成功）或原始URL（如果下载失败）
        """
        if not url or url.startswith('file://') or os.path.exists(url):
            return url
            
        try:
            self._log("debug", f"尝试下载: {url} -> {local_path}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self._log("debug", f"下载成功: {local_path}")
            return local_path
        except Exception as e:
            self._log("debug", f"下载失败: {url}, 错误: {e}")
            self._log("debug", f"返回原始URL: {url}")
            return url  # 返回原URL，让用户处理
            
    def generate_unique_filename(self, prefix: str, extension: str = ".mp4") -> str:
        """生成唯一的文件名，避免不同项目之间的文件冲突
        
        Args:
            prefix: 文件名前缀
            extension: 文件扩展名
            
        Returns:
            唯一的文件路径
        """
        # 使用时间戳和UUID生成唯一文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]  # 使用UUID的前8位
        filename = f"{prefix}_{timestamp}_{unique_id}{extension}"
        
        # 确保temp_materials目录存在
        os.makedirs("temp_materials", exist_ok=True)
        
        return f"temp_materials/{filename}"
        
    def ensure_temp_dir(self, temp_dir: str = "temp_materials"):
        """确保临时目录存在"""
        os.makedirs(temp_dir, exist_ok=True)
        
    def cleanup_temp_files(self, file_paths: list):
        """清理临时文件"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path) and file_path.startswith("temp_materials/"):
                    os.unlink(file_path)
                    self._log("debug", f"清理临时文件: {file_path}")
            except Exception as e:
                self._log("warning", f"清理临时文件失败 {file_path}: {e}")