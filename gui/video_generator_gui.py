#!/usr/bin/env python3
"""
视频生成器GUI应用

主要功能：
1. 从飞书获取数据并循环生成视频
2. 支持输入文案自动生成视频
3. 配置环境变量和API信息
4. 定时触发工作流
5. 工作流管理和扩展
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import threading
import time
from datetime import datetime, timedelta
import schedule
import requests
from typing import Dict, List, Any, Optional
import uuid

# 添加项目根目录到路径
import sys
# 将项目根目录的绝对路径加入 sys.path，确保可导入 workflow 包
# 项目根目录是当前文件上一级目录（gui 的父级）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 兼容导入：优先按包路径导入，失败则直接将 workflow 目录加入路径后相对导入
try:
    from workflow.examples.coze_complete_video_workflow import CozeVideoWorkflow
    from workflow.component.flow_python_implementation import VideoEditingWorkflow
except ImportError:
    WORKFLOW_DIR = os.path.join(PROJECT_ROOT, 'workflow')
    if WORKFLOW_DIR not in sys.path:
        sys.path.insert(0, WORKFLOW_DIR)
    from examples.coze_complete_video_workflow import CozeVideoWorkflow
    from component.flow_python_implementation import VideoEditingWorkflow

class VideoGeneratorGUI:
    """视频生成器GUI主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("视频生成器 - 智能视频制作工具")
        self.root.geometry("1200x800")
        
        # 配置文件路径
        self.config_file = "config.json"
        self.workflows_file = "workflows.json"
        self.schedules_file = "schedules.json"
        
        # 数据存储
        self.config = {}
        self.workflows = {}
        self.schedules = {}
        self.running_threads = {}
        
        # 加载配置
        self.load_config()
        self.load_workflows()
        self.load_schedules()
        
        # 创建GUI
        self.create_gui()
        
        # 启动调度器
        self.start_scheduler()
    
    def create_gui(self):
        """创建GUI界面"""
        # 创建笔记本控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建各个标签页
        self.create_config_tab()
        self.create_feishu_tab()
        self.create_manual_tab()
        self.create_workflow_tab()
        self.create_schedule_tab()
        self.create_log_tab()
    
    def create_config_tab(self):
        """创建配置标签页"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="配置管理")
        
        # 配置表单
        ttk.Label(config_frame, text="API配置", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Coze配置
        coze_frame = ttk.LabelFrame(config_frame, text="Coze API配置")
        coze_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(coze_frame, text="Bearer Token:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.coze_token_entry = ttk.Entry(coze_frame, width=60)
        self.coze_token_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(coze_frame, text="Workflow ID:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.coze_workflow_id_entry = ttk.Entry(coze_frame, width=60)
        self.coze_workflow_id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 飞书配置
        feishu_frame = ttk.LabelFrame(config_frame, text="飞书配置")
        feishu_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(feishu_frame, text="App ID:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.feishu_app_id_entry = ttk.Entry(feishu_frame, width=60)
        self.feishu_app_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(feishu_frame, text="App Secret:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.feishu_app_secret_entry = ttk.Entry(feishu_frame, width=60, show="*")
        self.feishu_app_secret_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(feishu_frame, text="Table ID:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.feishu_table_id_entry = ttk.Entry(feishu_frame, width=60)
        self.feishu_table_id_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # 火山引擎配置
        volc_frame = ttk.LabelFrame(config_frame, text="火山引擎ASR配置")
        volc_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(volc_frame, text="App ID:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.volc_appid_entry = ttk.Entry(volc_frame, width=60)
        self.volc_appid_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(volc_frame, text="Access Token:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.volc_token_entry = ttk.Entry(volc_frame, width=60)
        self.volc_token_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 豆包配置
        doubao_frame = ttk.LabelFrame(config_frame, text="豆包API配置")
        doubao_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(doubao_frame, text="Token:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.doubao_token_entry = ttk.Entry(doubao_frame, width=60)
        self.doubao_token_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 剪映配置
        jianying_frame = ttk.LabelFrame(config_frame, text="剪映配置")
        jianying_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(jianying_frame, text="草稿文件夹路径:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.jianying_path_entry = ttk.Entry(jianying_frame, width=60)
        self.jianying_path_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(jianying_frame, text="浏览", command=self.browse_jianying_path).grid(row=0, column=2, padx=5, pady=5)
        
        # 保存按钮
        ttk.Button(config_frame, text="保存配置", command=self.save_config).pack(pady=20)
        
        # 加载现有配置
        self.load_config_to_gui()
    
    def create_feishu_tab(self):
        """创建飞书数据标签页"""
        feishu_frame = ttk.Frame(self.notebook)
        self.notebook.add(feishu_frame, text="飞书数据")
        
        # 飞书数据获取
        ttk.Label(feishu_frame, text="飞书数据获取", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 数据预览区域
        preview_frame = ttk.LabelFrame(feishu_frame, text="数据预览")
        preview_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.feishu_data_text = scrolledtext.ScrolledText(preview_frame, height=20, width=80)
        self.feishu_data_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 操作按钮
        button_frame = ttk.Frame(feishu_frame)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="获取飞书数据", command=self.fetch_feishu_data).pack(side='left', padx=5)
        ttk.Button(button_frame, text="批量生成视频", command=self.batch_generate_from_feishu).pack(side='left', padx=5)
        ttk.Button(button_frame, text="清空数据", command=self.clear_feishu_data).pack(side='left', padx=5)
    
    def create_manual_tab(self):
        """创建手动生成标签页"""
        manual_frame = ttk.Frame(self.notebook)
        self.notebook.add(manual_frame, text="手动生成")
        
        ttk.Label(manual_frame, text="手动视频生成", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 输入表单
        input_frame = ttk.LabelFrame(manual_frame, text="视频参数")
        input_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(input_frame, text="文案内容:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.content_text = scrolledtext.ScrolledText(input_frame, height=5, width=60)
        self.content_text.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="数字编号:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.digital_no_entry = ttk.Entry(input_frame, width=60)
        self.digital_no_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="语音ID:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.voice_id_entry = ttk.Entry(input_frame, width=60)
        self.voice_id_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # 生成按钮
        ttk.Button(manual_frame, text="生成视频", command=self.manual_generate_video).pack(pady=20)
        
        # 进度显示
        self.progress_frame = ttk.LabelFrame(manual_frame, text="生成进度")
        self.progress_frame.pack(fill='x', padx=20, pady=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(padx=10, pady=10)
        
        self.progress_label = ttk.Label(self.progress_frame, text="准备就绪")
        self.progress_label.pack(pady=5)
    
    def create_workflow_tab(self):
        """创建工作流管理标签页"""
        workflow_frame = ttk.Frame(self.notebook)
        self.notebook.add(workflow_frame, text="工作流管理")
        
        ttk.Label(workflow_frame, text="工作流管理", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 工作流列表
        list_frame = ttk.LabelFrame(workflow_frame, text="工作流列表")
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 创建表格
        columns = ('ID', '名称', '类型', '状态', '创建时间')
        self.workflow_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.workflow_tree.heading(col, text=col)
            self.workflow_tree.column(col, width=150)
        
        self.workflow_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 操作按钮
        button_frame = ttk.Frame(workflow_frame)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_workflow_list).pack(side='left', padx=5)
        ttk.Button(button_frame, text="查看详情", command=self.view_workflow_detail).pack(side='left', padx=5)
        ttk.Button(button_frame, text="删除工作流", command=self.delete_workflow).pack(side='left', padx=5)
    
    def create_schedule_tab(self):
        """创建定时任务标签页"""
        schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(schedule_frame, text="定时任务")
        
        ttk.Label(schedule_frame, text="定时任务管理", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 创建定时任务
        create_frame = ttk.LabelFrame(schedule_frame, text="创建定时任务")
        create_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(create_frame, text="任务名称:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.schedule_name_entry = ttk.Entry(create_frame, width=40)
        self.schedule_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(create_frame, text="工作流:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.schedule_workflow_combo = ttk.Combobox(create_frame, width=38)
        self.schedule_workflow_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(create_frame, text="执行时间:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.schedule_time_entry = ttk.Entry(create_frame, width=40)
        self.schedule_time_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(create_frame, text="(格式: HH:MM)").grid(row=2, column=2, padx=5, pady=5)
        
        ttk.Label(create_frame, text="重复周期:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.schedule_repeat_combo = ttk.Combobox(create_frame, values=['每天', '每周', '每月'], width=38)
        self.schedule_repeat_combo.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Button(create_frame, text="创建任务", command=self.create_schedule).grid(row=4, column=1, pady=10)
        
        # 任务列表
        list_frame = ttk.LabelFrame(schedule_frame, text="定时任务列表")
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        columns = ('名称', '工作流', '执行时间', '重复周期', '状态', '下次执行')
        self.schedule_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.schedule_tree.heading(col, text=col)
            self.schedule_tree.column(col, width=120)
        
        self.schedule_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 操作按钮
        button_frame = ttk.Frame(schedule_frame)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_schedule_list).pack(side='left', padx=5)
        ttk.Button(button_frame, text="启用/禁用", command=self.toggle_schedule).pack(side='left', padx=5)
        ttk.Button(button_frame, text="删除任务", command=self.delete_schedule).pack(side='left', padx=5)
    
    def create_log_tab(self):
        """创建日志标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="运行日志")
        
        ttk.Label(log_frame, text="系统日志", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(log_frame, height=30, width=100)
        self.log_text.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 操作按钮
        button_frame = ttk.Frame(log_frame)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).pack(side='left', padx=5)
        ttk.Button(button_frame, text="导出日志", command=self.export_log).pack(side='left', padx=5)
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                self.log_message(f"加载配置文件失败: {e}")
                self.config = {}
        else:
            self.config = {}
    
    def save_config(self):
        """保存配置文件"""
        self.config['coze'] = {
            'bearer_token': self.coze_token_entry.get(),
            'workflow_id': self.coze_workflow_id_entry.get()
        }
        self.config['feishu'] = {
            'app_id': self.feishu_app_id_entry.get(),
            'app_secret': self.feishu_app_secret_entry.get(),
            'table_id': self.feishu_table_id_entry.get()
        }
        self.config['volcengine'] = {
            'appid': self.volc_appid_entry.get(),
            'access_token': self.volc_token_entry.get()
        }
        self.config['doubao'] = {
            'token': self.doubao_token_entry.get()
        }
        self.config['jianying'] = {
            'draft_folder_path': self.jianying_path_entry.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "配置保存成功")
            self.log_message("配置保存成功")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
            self.log_message(f"保存配置失败: {e}")
    
    def load_config_to_gui(self):
        """加载配置到GUI"""
        if 'coze' in self.config:
            self.coze_token_entry.insert(0, self.config['coze'].get('bearer_token', ''))
            self.coze_workflow_id_entry.insert(0, self.config['coze'].get('workflow_id', ''))
        
        if 'feishu' in self.config:
            self.feishu_app_id_entry.insert(0, self.config['feishu'].get('app_id', ''))
            self.feishu_app_secret_entry.insert(0, self.config['feishu'].get('app_secret', ''))
            self.feishu_table_id_entry.insert(0, self.config['feishu'].get('table_id', ''))
        
        if 'volcengine' in self.config:
            self.volc_appid_entry.insert(0, self.config['volcengine'].get('appid', ''))
            self.volc_token_entry.insert(0, self.config['volcengine'].get('access_token', ''))
        
        if 'doubao' in self.config:
            self.doubao_token_entry.insert(0, self.config['doubao'].get('token', ''))
        
        if 'jianying' in self.config:
            self.jianying_path_entry.insert(0, self.config['jianying'].get('draft_folder_path', ''))
    
    def load_workflows(self):
        """加载工作流数据"""
        if os.path.exists(self.workflows_file):
            try:
                with open(self.workflows_file, 'r', encoding='utf-8') as f:
                    self.workflows = json.load(f)
            except Exception as e:
                self.log_message(f"加载工作流数据失败: {e}")
                self.workflows = {}
        else:
            self.workflows = {}
    
    def save_workflows(self):
        """保存工作流数据"""
        try:
            with open(self.workflows_file, 'w', encoding='utf-8') as f:
                json.dump(self.workflows, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"保存工作流数据失败: {e}")
    
    def load_schedules(self):
        """加载定时任务数据"""
        if os.path.exists(self.schedules_file):
            try:
                with open(self.schedules_file, 'r', encoding='utf-8') as f:
                    self.schedules = json.load(f)
            except Exception as e:
                self.log_message(f"加载定时任务数据失败: {e}")
                self.schedules = {}
        else:
            self.schedules = {}
    
    def save_schedules(self):
        """保存定时任务数据"""
        try:
            with open(self.schedules_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"保存定时任务数据失败: {e}")
    
    def browse_jianying_path(self):
        """浏览剪映草稿文件夹"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.jianying_path_entry.delete(0, tk.END)
            self.jianying_path_entry.insert(0, folder_path)
    
    def fetch_feishu_data(self):
        """获取飞书数据"""
        def fetch_data():
            try:
                self.log_message("开始获取飞书数据...")
                
                # 检查飞书配置
                if 'feishu' not in self.config or not self.config['feishu'].get('app_id'):
                    raise ValueError("请先配置飞书App ID")
                
                # 模拟获取飞书数据
                feishu_client = FeishuClient(
                    self.config['feishu']['app_id'],
                    self.config['feishu']['app_secret']
                )
                
                data = feishu_client.get_table_data(self.config['feishu']['table_id'])
                
                # 在GUI中显示数据
                self.root.after(0, self.display_feishu_data, data)
                self.log_message(f"成功获取飞书数据，共{len(data)}条记录")
                
            except Exception as e:
                error_msg = f"获取飞书数据失败: {e}"
                self.root.after(0, self.log_message, error_msg)
                messagebox.showerror("错误", error_msg)
        
        threading.Thread(target=fetch_data, daemon=True).start()
    
    def display_feishu_data(self, data):
        """显示飞书数据"""
        self.feishu_data_text.delete(1.0, tk.END)
        
        for i, record in enumerate(data):
            self.feishu_data_text.insert(tk.END, f"记录 {i+1}:\n")
            for key, value in record.items():
                self.feishu_data_text.insert(tk.END, f"  {key}: {value}\n")
            self.feishu_data_text.insert(tk.END, "\n")
    
    def clear_feishu_data(self):
        """清空飞书数据"""
        self.feishu_data_text.delete(1.0, tk.END)
        self.log_message("清空飞书数据")
    
    def batch_generate_from_feishu(self):
        """从飞书数据批量生成视频"""
        def batch_generate():
            try:
                self.log_message("开始批量生成视频...")
                
                # 获取飞书数据
                feishu_data = self.get_feishu_data_from_text()
                if not feishu_data:
                    raise ValueError("请先获取飞书数据")
                
                # 检查配置
                if not self.check_config():
                    return
                
                total_count = len(feishu_data)
                success_count = 0
                
                for i, record in enumerate(feishu_data):
                    try:
                        self.root.after(0, self.update_progress, i+1, total_count, f"正在处理第{i+1}/{total_count}条记录...")
                        
                        # 获取仿写文案字段
                        content = record.get('仿写文案', '') or record.get('content', '')
                        if not content:
                            self.log_message(f"记录{i+1}没有仿写文案字段，跳过")
                            continue
                        
                        # 生成视频
                        result = self.generate_video_from_content(content)
                        if result:
                            success_count += 1
                            self.log_message(f"记录{i+1}视频生成成功: {result}")
                        else:
                            self.log_message(f"记录{i+1}视频生成失败")
                        
                    except Exception as e:
                        self.log_message(f"处理记录{i+1}时出错: {e}")
                
                self.root.after(0, self.update_progress, total_count, total_count, f"批量生成完成，成功{success_count}/{total_count}条")
                self.log_message(f"批量生成完成，成功{success_count}/{total_count}条")
                
            except Exception as e:
                error_msg = f"批量生成失败: {e}"
                self.root.after(0, self.log_message, error_msg)
                messagebox.showerror("错误", error_msg)
        
        threading.Thread(target=batch_generate, daemon=True).start()
    
    def get_feishu_data_from_text(self):
        """从文本框获取飞书数据"""
        text = self.feishu_data_text.get(1.0, tk.END)
        if not text.strip():
            return []
        
        # 简单解析文本数据
        records = []
        current_record = {}
        
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('记录'):
                if current_record:
                    records.append(current_record)
                current_record = {}
            elif ':' in line:
                key, value = line.split(':', 1)
                current_record[key.strip()] = value.strip()
        
        if current_record:
            records.append(current_record)
        
        return records
    
    def manual_generate_video(self):
        """手动生成视频"""
        def generate():
            try:
                self.log_message("开始手动生成视频...")
                
                # 获取输入参数
                content = self.content_text.get(1.0, tk.END).strip()
                digital_no = self.digital_no_entry.get().strip()
                voice_id = self.voice_id_entry.get().strip()
                
                if not content:
                    raise ValueError("请输入文案内容")
                
                if not digital_no:
                    digital_no = f"D{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                if not voice_id:
                    voice_id = f"AA{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # 检查配置
                if not self.check_config():
                    return
                
                # 更新进度
                self.root.after(0, self.update_progress, 0, 100, "正在生成视频...")
                
                # 生成视频
                result = self.generate_video_from_content(content, digital_no, voice_id)
                
                if result:
                    self.root.after(0, self.update_progress, 100, 100, "视频生成成功")
                    self.log_message(f"视频生成成功: {result}")
                    messagebox.showinfo("成功", f"视频生成成功:\n{result}")
                else:
                    self.root.after(0, self.update_progress, 100, 100, "视频生成失败")
                    self.log_message("视频生成失败")
                    messagebox.showerror("错误", "视频生成失败")
                
            except Exception as e:
                error_msg = f"手动生成失败: {e}"
                self.root.after(0, self.log_message, error_msg)
                self.root.after(0, self.update_progress, 100, 100, "生成失败")
                messagebox.showerror("错误", error_msg)
        
        threading.Thread(target=generate, daemon=True).start()
    
    def generate_video_from_content(self, content: str, digital_no: str = None, voice_id: str = None) -> Optional[str]:
        """根据内容生成视频"""
        try:
            if not digital_no:
                digital_no = f"D{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            if not voice_id:
                voice_id = f"AA{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 获取剪映路径
            jianying_path = self.config.get('jianying', {}).get('draft_folder_path')
            if not jianying_path:
                raise ValueError("请先配置剪映草稿文件夹路径")
            
            # 创建工作流实例
            workflow = CozeVideoWorkflow(jianying_path, f"manual_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # 运行工作流
            result = workflow.run_complete_workflow(content, digital_no, voice_id)
            
            # 保存工作流记录
            workflow_id = str(uuid.uuid4())
            self.workflows[workflow_id] = {
                'id': workflow_id,
                'name': f"手动生成_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                'type': 'manual',
                'content': content,
                'digital_no': digital_no,
                'voice_id': voice_id,
                'result': result,
                'status': 'completed' if result else 'failed',
                'create_time': datetime.now().isoformat()
            }
            self.save_workflows()
            
            return result
            
        except Exception as e:
            self.log_message(f"生成视频失败: {e}")
            return None
    
    def check_config(self) -> bool:
        """检查配置是否完整"""
        required_configs = [
            ('coze', 'bearer_token', 'Coze Bearer Token'),
            ('coze', 'workflow_id', 'Coze Workflow ID'),
            ('volcengine', 'appid', '火山引擎App ID'),
            ('volcengine', 'access_token', '火山引擎Access Token'),
            ('jianying', 'draft_folder_path', '剪映草稿文件夹路径')
        ]
        
        missing_configs = []
        
        for section, key, name in required_configs:
            if section not in self.config or not self.config[section].get(key):
                missing_configs.append(name)
        
        if missing_configs:
            messagebox.showerror("配置错误", f"以下配置缺失:\n" + "\n".join(missing_configs))
            return False
        
        return True
    
    def update_progress(self, current: int, total: int, message: str):
        """更新进度条"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar['value'] = percentage
        self.progress_label['text'] = message
    
    def refresh_workflow_list(self):
        """刷新工作流列表"""
        # 清空列表
        for item in self.workflow_tree.get_children():
            self.workflow_tree.delete(item)
        
        # 添加工作流
        for workflow_id, workflow in self.workflows.items():
            self.workflow_tree.insert('', 'end', values=(
                workflow_id[:8] + '...',
                workflow.get('name', ''),
                workflow.get('type', ''),
                workflow.get('status', ''),
                workflow.get('create_time', '')
            ))
    
    def view_workflow_detail(self):
        """查看工作流详情"""
        selection = self.workflow_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择一个工作流")
            return
        
        # 获取工作流ID
        item = self.workflow_tree.item(selection[0])
        workflow_name = item['values'][1]
        
        # 查找完整的工作流信息
        workflow = None
        for wf in self.workflows.values():
            if wf.get('name') == workflow_name:
                workflow = wf
                break
        
        if workflow:
            detail = f"工作流详情:\n\n"
            detail += f"名称: {workflow.get('name', '')}\n"
            detail += f"类型: {workflow.get('type', '')}\n"
            detail += f"状态: {workflow.get('status', '')}\n"
            detail += f"创建时间: {workflow.get('create_time', '')}\n"
            detail += f"内容: {workflow.get('content', '')}\n"
            detail += f"结果: {workflow.get('result', '')}"
            
            messagebox.showinfo("工作流详情", detail)
    
    def delete_workflow(self):
        """删除工作流"""
        selection = self.workflow_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择一个工作流")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的工作流吗？"):
            # 获取工作流ID
            item = self.workflow_tree.item(selection[0])
            workflow_name = item['values'][1]
            
            # 查找并删除工作流
            to_delete = []
            for workflow_id, workflow in self.workflows.items():
                if workflow.get('name') == workflow_name:
                    to_delete.append(workflow_id)
            
            for workflow_id in to_delete:
                del self.workflows[workflow_id]
            
            self.save_workflows()
            self.refresh_workflow_list()
            self.log_message(f"删除工作流: {workflow_name}")
    
    def create_schedule(self):
        """创建定时任务"""
        try:
            name = self.schedule_name_entry.get().strip()
            workflow_id = self.schedule_workflow_combo.get()
            time_str = self.schedule_time_entry.get().strip()
            repeat = self.schedule_repeat_combo.get()
            
            if not all([name, workflow_id, time_str, repeat]):
                raise ValueError("请填写所有必填字段")
            
            # 验证时间格式
            try:
                datetime.strptime(time_str, '%H:%M')
            except ValueError:
                raise ValueError("时间格式错误，请使用HH:MM格式")
            
            # 创建定时任务
            schedule_id = str(uuid.uuid4())
            self.schedules[schedule_id] = {
                'id': schedule_id,
                'name': name,
                'workflow_id': workflow_id,
                'time': time_str,
                'repeat': repeat,
                'enabled': True,
                'create_time': datetime.now().isoformat()
            }
            
            self.save_schedules()
            self.refresh_schedule_list()
            
            # 清空输入框
            self.schedule_name_entry.delete(0, tk.END)
            self.schedule_time_entry.delete(0, tk.END)
            self.schedule_repeat_combo.set('')
            
            messagebox.showinfo("成功", "定时任务创建成功")
            self.log_message(f"创建定时任务: {name}")
            
        except Exception as e:
            messagebox.showerror("错误", f"创建定时任务失败: {e}")
    
    def refresh_schedule_list(self):
        """刷新定时任务列表"""
        # 清空列表
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # 更新工作流下拉框
        workflow_names = [wf.get('name', '') for wf in self.workflows.values()]
        self.schedule_workflow_combo['values'] = workflow_names
        
        # 添加定时任务
        for schedule_id, schedule in self.schedules.items():
            next_run = self.calculate_next_run(schedule['time'], schedule['repeat'])
            self.schedule_tree.insert('', 'end', values=(
                schedule.get('name', ''),
                schedule.get('workflow_id', ''),
                schedule.get('time', ''),
                schedule.get('repeat', ''),
                '启用' if schedule.get('enabled', False) else '禁用',
                next_run
            ))
    
    def calculate_next_run(self, time_str: str, repeat: str) -> str:
        """计算下次运行时间"""
        try:
            now = datetime.now()
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            if repeat == '每天':
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
            elif repeat == '每周':
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=7)
            else:  # 每月
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=30)
            
            return next_run.strftime('%Y-%m-%d %H:%M')
        except:
            return '计算错误'
    
    def toggle_schedule(self):
        """启用/禁用定时任务"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择一个定时任务")
            return
        
        item = self.schedule_tree.item(selection[0])
        schedule_name = item['values'][0]
        
        # 查找并切换状态
        for schedule in self.schedules.values():
            if schedule.get('name') == schedule_name:
                schedule['enabled'] = not schedule.get('enabled', False)
                break
        
        self.save_schedules()
        self.refresh_schedule_list()
        self.log_message(f"切换定时任务状态: {schedule_name}")
    
    def delete_schedule(self):
        """删除定时任务"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择一个定时任务")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的定时任务吗？"):
            item = self.schedule_tree.item(selection[0])
            schedule_name = item['values'][0]
            
            # 查找并删除
            to_delete = []
            for schedule_id, schedule in self.schedules.items():
                if schedule.get('name') == schedule_name:
                    to_delete.append(schedule_id)
            
            for schedule_id in to_delete:
                del self.schedules[schedule_id]
            
            self.save_schedules()
            self.refresh_schedule_list()
            self.log_message(f"删除定时任务: {schedule_name}")
    
    def start_scheduler(self):
        """启动调度器"""
        def scheduler_loop():
            while True:
                try:
                    # 检查定时任务
                    now = datetime.now()
                    current_time = now.strftime('%H:%M')
                    
                    for schedule_id, schedule in self.schedules.items():
                        if schedule.get('enabled', False) and schedule.get('time') == current_time:
                            # 检查是否已经运行过
                            last_run = schedule.get('last_run')
                            should_run = True
                            
                            if last_run:
                                last_run_time = datetime.fromisoformat(last_run)
                                if schedule.get('repeat') == '每天':
                                    should_run = (now - last_run_time).days >= 1
                                elif schedule.get('repeat') == '每周':
                                    should_run = (now - last_run_time).days >= 7
                                elif schedule.get('repeat') == '每月':
                                    should_run = (now - last_run_time).days >= 30
                            
                            if should_run:
                                self.run_scheduled_task(schedule_id)
                    
                    time.sleep(60)  # 每分钟检查一次
                
                except Exception as e:
                    self.log_message(f"调度器错误: {e}")
                    time.sleep(60)
        
        threading.Thread(target=scheduler_loop, daemon=True).start()
        self.log_message("调度器已启动")
    
    def run_scheduled_task(self, schedule_id: str):
        """运行定时任务"""
        try:
            schedule = self.schedules.get(schedule_id)
            if not schedule:
                return
            
            workflow_name = schedule.get('workflow_id')
            
            # 查找工作流
            workflow = None
            for wf in self.workflows.values():
                if wf.get('name') == workflow_name:
                    workflow = wf
                    break
            
            if not workflow:
                self.log_message(f"未找到工作流: {workflow_name}")
                return
            
            self.log_message(f"开始执行定时任务: {schedule.get('name')}")
            
            # 根据工作流类型执行
            if workflow.get('type') == 'manual':
                result = self.generate_video_from_content(
                    workflow.get('content', ''),
                    workflow.get('digital_no'),
                    workflow.get('voice_id')
                )
            else:
                self.log_message(f"不支持的工作流类型: {workflow.get('type')}")
                return
            
            # 更新最后运行时间
            schedule['last_run'] = datetime.now().isoformat()
            self.save_schedules()
            
            self.log_message(f"定时任务执行完成: {schedule.get('name')}")
            
        except Exception as e:
            self.log_message(f"定时任务执行失败: {e}")
    
    def log_message(self, message: str):
        """记录日志消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 限制日志长度
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 1000:
            self.log_text.delete(1.0, f"{len(lines)-1000}.0")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("日志已清空")
    
    def export_log(self):
        """导出日志"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("成功", f"日志已导出到: {filename}")
                self.log_message(f"日志已导出到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出日志失败: {e}")


class FeishuClient:
    """飞书客户端"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.base_url = "https://open.feishu.cn/open-apis"
    
    def get_access_token(self) -> str:
        """获取访问令牌"""
        if not self.access_token:
            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 0:
                self.access_token = result.get('tenant_access_token')
            else:
                raise ValueError(f"获取访问令牌失败: {result.get('msg')}")
        
        return self.access_token
    
    def get_table_data(self, table_id: str) -> List[Dict[str, Any]]:
        """获取表格数据"""
        access_token = self.get_access_token()
        url = f"{self.base_url}/sheets/v2/spreadsheets/{table_id}/values"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        if result.get('code') == 0:
            data = result.get('data', {})
            values = data.get('values', [])
            
            # 转换为记录格式
            records = []
            if values:
                headers = values[0]  # 第一行作为表头
                for row in values[1:]:  # 从第二行开始为数据
                    record = {}
                    for i, value in enumerate(row):
                        if i < len(headers):
                            record[headers[i]] = value
                    records.append(record)
            
            return records
        else:
            raise ValueError(f"获取表格数据失败: {result.get('msg')}")


def main():
    """主函数"""
    root = tk.Tk()
    app = VideoGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()