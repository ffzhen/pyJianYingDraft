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
import subprocess
import webbrowser

# 优先使用内置 ffmpeg（若随 EXE 打包在 bin\ffmpeg.exe）
try:
    _exe_dir = os.path.dirname(os.path.abspath(__file__))
    _ffmpeg_bin = os.path.join(_exe_dir, 'bin')
    if os.path.exists(os.path.join(_ffmpeg_bin, 'ffmpeg.exe')) and _ffmpeg_bin not in os.environ.get('PATH', ''):
        os.environ['PATH'] = _ffmpeg_bin + os.pathsep + os.environ.get('PATH', '')
except Exception:
    pass

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
    from workflow.feishu_async_batch_workflow import FeishuAsyncBatchWorkflow
except ImportError:
    WORKFLOW_DIR = os.path.join(PROJECT_ROOT, 'workflow')
    if WORKFLOW_DIR not in sys.path:
        sys.path.insert(0, WORKFLOW_DIR)
    from examples.coze_complete_video_workflow import CozeVideoWorkflow
    from component.flow_python_implementation import VideoEditingWorkflow
    from feishu_async_batch_workflow import FeishuAsyncBatchWorkflow

class VideoGeneratorGUI:
    """视频生成器GUI主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("视频生成器 - 智能视频制作工具")
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = min(1200, max(960, sw - 80))
            h = min(800, max(640, sh - 120))
            self.root.geometry(f"{w}x{h}")
            # 小屏幕上尽量最大化窗口，提高可视区域
            if sw < 1366 or sh < 768:
                try:
                    self.root.state('zoomed')
                except Exception:
                    pass
            self.root.minsize(900, 620)
        except Exception:
            self.root.geometry("1200x800")
        
        # 配置文件路径
        self.config_file = "config.json"
        self.workflows_file = "workflows.json"
        self.schedules_file = "schedules.json"
        self.templates_file = "templates.json"
        
        # 数据存储
        self.config = {}
        self.workflows = {}
        self.schedules = {}
        self.templates = {}
        self.running_threads = {}
        self.feishu_content_data = []  # 存储飞书内容数据
        self.current_session_id = None  # 当前运行会话ID
        self.session_logs = {}  # 存储各会话的日志
        self.logs_dir = os.path.join(os.path.dirname(__file__), 'workflow_logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        self.current_session_log_file = None
        
        # 加载配置
        self.load_config()
        # 应用可选 ffmpeg 路径
        self.apply_ffmpeg_path()
        self.load_workflows()
        self.load_schedules()
        self.load_templates()
        
        # 创建GUI
        self.create_gui()
        
        # 启动调度器
        self.start_scheduler()

    def apply_ffmpeg_path(self):
        """将配置中的 ffmpeg 路径加入 PATH（若存在）"""
        try:
            ffmpeg_path = ((self.config.get('tools') or {}).get('ffmpeg_path') or '').strip()
            if ffmpeg_path:
                ffmpeg_dir = ffmpeg_path if ffmpeg_path.lower().endswith('.exe') else ffmpeg_path
                if ffmpeg_dir.lower().endswith('.exe'):
                    ffmpeg_dir = os.path.dirname(ffmpeg_dir)
                if os.path.isdir(ffmpeg_dir) and ffmpeg_dir not in os.environ.get('PATH', ''):
                    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
        except Exception:
            pass

    def browse_ffmpeg_path(self):
        path = filedialog.askopenfilename(title="选择 ffmpeg.exe", filetypes=[("ffmpeg", "ffmpeg.exe"), ("所有文件", "*.*")])
        if path:
            self.ffmpeg_path_entry.delete(0, tk.END)
            self.ffmpeg_path_entry.insert(0, path)

    def browse_bgm_path(self):
        path = filedialog.askopenfilename(title="选择背景音乐文件", filetypes=[("音频文件", "*.mp3;*.wav;*.aac;*.m4a;*.flac"), ("所有文件", "*.*")])
        if path:
            self.bgm_path_entry.delete(0, tk.END)
            self.bgm_path_entry.insert(0, path)
    
    def create_gui(self):
        """创建GUI界面"""
        # 创建笔记本控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建各个标签页（先创建日志标签页，确保log_message可用）
        self.create_log_tab()
        self.create_feishu_async_tab()
        # self.create_simple_compose_tab()  # 隐藏简单合成
        # self.create_manual_tab()  # 隐藏手动合成
        self.create_workflow_tab()
        self.create_schedule_tab()
        self.create_templates_tab()
        self.create_config_tab()

        # 默认选中"飞书视频批量生成"标签
        try:
            for i in range(len(self.notebook.tabs())):
                tab_text = self.notebook.tab(i, option='text')
                if tab_text == "飞书视频批量生成" or tab_text == "飞书异步批量":
                    self.notebook.select(i)
                    break
        except Exception:
            pass

        # 首次加载时初始化工作流与定时任务列表
        try:
            if hasattr(self, 'refresh_workflow_list'):
                self.refresh_workflow_list()
            if hasattr(self, 'refresh_schedule_list'):
                self.refresh_schedule_list()
        except Exception as _init_list_err:
            self.log_message(f"初始化列表失败: {_init_list_err}")

    def get_current_template(self) -> dict:
        """获取当前生效的模板配置"""
        tmpl_key = ((self.config.get('template') or {}).get('active') or 'default')
        template_data = self.templates.get(tmpl_key) or self.templates.get('default') or {}
        return self.validate_template_data(template_data)
    
    def validate_template_data(self, template_data: dict) -> dict:
        """验证和修正模板数据
        
        Args:
            template_data: 原始模板数据
            
        Returns:
            验证后的模板数据
        """
        validated = {}
        
        # 验证标题配置
        validated['title_color'] = self._validate_color(template_data.get('title_color', '#FFFFFF'))
        validated['title_highlight_color'] = self._validate_color(template_data.get('title_highlight_color', '#FFD700'))
        # 兼容字符串形式的布尔值，例如 "true"/"false"
        _tbg = template_data.get('title_bg_enabled', True)
        if isinstance(_tbg, str):
            validated['title_bg_enabled'] = _tbg.strip().lower() in ['1', 'true', 'yes', 'y', 'on']
        else:
            validated['title_bg_enabled'] = bool(_tbg)
        validated['title_font'] = self._validate_font(template_data.get('title_font', '阳华体'))
        validated['title_font_size'] = self._validate_font_size(template_data.get('title_font_size', '24'))
        validated['title_scale'] = self._validate_scale(template_data.get('title_scale', '1.0'))
        validated['title_line_spacing'] = self._validate_scale(template_data.get('title_line_spacing', '1.0'))
        
        # 验证字幕配置
        validated['subtitle_color'] = self._validate_color(template_data.get('subtitle_color', '#FFFFFF'))
        validated['subtitle_highlight_color'] = self._validate_color(template_data.get('subtitle_highlight_color', '#00FFFF'))
        _sbg = template_data.get('subtitle_bg_enabled', True)
        if isinstance(_sbg, str):
            validated['subtitle_bg_enabled'] = _sbg.strip().lower() in ['1', 'true', 'yes', 'y', 'on']
        else:
            validated['subtitle_bg_enabled'] = bool(_sbg)
        validated['subtitle_font'] = self._validate_font(template_data.get('subtitle_font', '俪金黑'))
        validated['subtitle_font_size'] = self._validate_font_size(template_data.get('subtitle_font_size', '18'))
        validated['subtitle_scale'] = self._validate_scale(template_data.get('subtitle_scale', '1.0'))
        
        # 验证封面配置
        validated['cover_background'] = str(template_data.get('cover_background', '')).strip()
        validated['cover_title_font'] = self._validate_font(template_data.get('cover_title_font', '阳华体'))
        validated['cover_title_color'] = self._validate_color(template_data.get('cover_title_color', '#FFFFFF'))
        validated['cover_title_size'] = self._validate_font_size(template_data.get('cover_title_size', '24'))
        validated['cover_subtitle_font'] = self._validate_font(template_data.get('cover_subtitle_font', '俪金黑'))
        validated['cover_subtitle_color'] = self._validate_color(template_data.get('cover_subtitle_color', '#FFFFFF'))
        validated['cover_subtitle_size'] = self._validate_font_size(template_data.get('cover_subtitle_size', '18'))
        
        # 验证名称
        validated['name'] = str(template_data.get('name', '未命名模板')).strip() or '未命名模板'
        
        return validated
    
    def _validate_color(self, color: str) -> str:
        """验证颜色值"""
        if not color or not isinstance(color, str):
            return '#FFFFFF'
        
        color = color.strip()
        if color.startswith('#'):
            if len(color) == 7 and all(c in '0123456789ABCDEFabcdef' for c in color[1:]):
                return color.upper()
        return '#FFFFFF'
    
    def _validate_font(self, font: str) -> str:
        """验证字体"""
        valid_fonts = ['阳华体', '俪金黑', '思源黑体', '微软雅黑', '宋体', '黑体', '楷体', '仿宋']
        if font and font in valid_fonts:
            return font
        return '阳华体'
    
    def _validate_font_size(self, size: str) -> str:
        """验证字号"""
        try:
            size_val = float(size)
            if 8 <= size_val <= 100:
                return str(int(size_val))
        except (ValueError, TypeError):
            pass
        return '24'
    
    def _validate_scale(self, scale: str) -> str:
        """验证缩放值"""
        try:
            scale_val = float(scale)
            if 0.1 <= scale_val <= 5.0:
                return str(round(scale_val, 2))
        except (ValueError, TypeError):
            pass
        return '1.0'
    
    def refresh_feishu_template_list(self):
        """刷新飞书模板选择列表"""
        try:
            template_list = []
            for key, template in (self.templates or {}).items():
                template_name = template.get('name', key)
                template_list.append(f"{key} - {template_name}")
            
            self.feishu_template_combo['values'] = template_list
            
            # 设置默认选择
            if template_list and not self.feishu_template_var.get():
                # 优先选择当前激活的模板
                active_key = ((self.config.get('template') or {}).get('active') or 'default')
                for item in template_list:
                    if item.startswith(f"{active_key} -"):
                        self.feishu_template_var.set(item)
                        break
                else:
                    # 如果没有找到激活的模板，选择第一个
                    self.feishu_template_var.set(template_list[0])
            
            self.log_message(f"已刷新模板列表，共 {len(template_list)} 个模板")
        except Exception as e:
            self.log_message(f"刷新模板列表失败: {e}")
    
    def get_selected_feishu_template(self) -> dict:
        """获取选择的飞书模板配置"""
        try:
            selected = self.feishu_template_var.get()
            if not selected:
                # 如果没有选择，使用当前激活的模板
                return self.get_current_template()
            
            # 从选择项中提取模板key
            template_key = selected.split(' - ')[0]
            template_data = self.templates.get(template_key, {})
            
            if template_data:
                self.log_message(f"使用飞书模板: {template_data.get('name', template_key)}")
                return self.validate_template_data(template_data)
            else:
                self.log_message("未找到选择的模板，使用默认模板")
                return self.get_current_template()
                
        except Exception as e:
            self.log_message(f"获取飞书模板失败: {e}，使用默认模板")
            return self.get_current_template()

    def create_templates_tab(self):
        """创建模版管理标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="模版管理")

        top = ttk.Frame(tab)
        top.pack(fill='x', padx=20, pady=10)

        ttk.Label(top, text="模版列表", font=("Arial", 14, "bold")).pack(side='left')

        actions = ttk.Frame(tab)
        actions.pack(fill='x', padx=20, pady=5)

        self.template_list = ttk.Treeview(tab, columns=(
            'key','name','title_color','title_font','title_size','subtitle_color','subtitle_font','subtitle_size',
            'cover_background','cover_title_font','cover_subtitle_font'
        ), show='headings', height=10)
        for col, w in [
            ('key',120), ('name',120), ('title_color',100), ('title_font',120),
            ('title_size',80), ('subtitle_color',100), ('subtitle_font',120), ('subtitle_size',80),
            ('cover_background',150), ('cover_title_font',120), ('cover_subtitle_font',120)
        ]:
            self.template_list.heading(col, text=col)
            self.template_list.column(col, width=w)
        self.template_list.pack(fill='both', expand=True, padx=20, pady=10)

        btns = ttk.Frame(tab)
        btns.pack(fill='x', padx=20, pady=10)
        ttk.Button(btns, text="新增模版", command=self.add_template_dialog).pack(side='left', padx=5)
        ttk.Button(btns, text="编辑所选", command=self.edit_selected_template).pack(side='left', padx=5)
        ttk.Button(btns, text="删除所选", command=self.delete_selected_template).pack(side='left', padx=5)
        ttk.Button(btns, text="设为当前", command=self.set_active_template).pack(side='left', padx=5)
        ttk.Button(btns, text="测试模版", command=self.test_selected_template).pack(side='left', padx=5)

        self.refresh_template_list()

    def refresh_template_list(self):
        for item in self.template_list.get_children():
            self.template_list.delete(item)
        for key, t in (self.templates or {}).items():
            self.template_list.insert('', 'end', values=(
                key,
                t.get('name',''),
                t.get('title_color',''),
                t.get('title_font',''),
                t.get('title_font_size',''),
                t.get('subtitle_color',''),
                t.get('subtitle_font',''),
                t.get('subtitle_font_size',''),
                t.get('cover_background',''),
                t.get('cover_title_font',''),
                t.get('cover_subtitle_font','')
            ))

    def _template_form(self, parent, data: dict) -> dict:
        entries = {}
        
        # 创建滚动区域
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 定义字段分组
        field_groups = [
            {
                'title': '基本信息',
                'fields': [
                    ('name', '模版名称')
                ]
            },
            {
                'title': '标题样式',
                'fields': [
                    ('title_color', '标题颜色'),
                    ('title_highlight_color', '标题高亮色'),
                    ('title_bg_enabled', '标题背景'),
                    ('title_font', '标题字体'),
                    ('title_font_size', '标题字号'),
                    ('title_scale', '标题缩放'),
                    ('title_line_spacing', '标题行间距')
                ]
            },
            {
                'title': '字幕样式',
                'fields': [
                    ('subtitle_color', '字幕颜色'),
                    ('subtitle_highlight_color', '字幕高亮色'),
                    ('subtitle_bg_enabled', '字幕背景'),
                    ('subtitle_font', '字幕字体'),
                    ('subtitle_font_size', '字幕字号'),
                    ('subtitle_scale', '字幕缩放')
                ]
            },
            {
                'title': '封面配置',
                'fields': [
                    ('cover_background', '封面底图'),
                    ('cover_title_font', '封面标题字体'),
                    ('cover_title_color', '封面标题颜色'),
                    ('cover_title_size', '封面标题字号'),
                    ('cover_subtitle_font', '封面下方标题字体'),
                    ('cover_subtitle_color', '封面下方标题颜色'),
                    ('cover_subtitle_size', '封面下方标题字号')
                ]
            }
        ]
        
        row = 0
        for group in field_groups:
            # 添加分组标题
            group_frame = ttk.LabelFrame(scrollable_frame, text=group['title'], padding=10)
            group_frame.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
            row += 1
            
            # 添加分组内的字段
            for i, (key, label) in enumerate(group['fields']):
                ttk.Label(group_frame, text=f"{label}:").grid(row=i, column=0, sticky='w', padx=5, pady=3)
                
                if key.endswith('_enabled'):
                    var = tk.BooleanVar(value=bool(data.get(key, False)))
                    cb = ttk.Checkbutton(group_frame, variable=var)
                    cb.grid(row=i, column=1, sticky='w', padx=5, pady=3)
                    entries[key] = var
                elif key.endswith('_font'):
                    # 所有字体字段都使用输入框，支持任意字体名称
                    if key == 'title_font':
                        default_value = '阳华体'
                    elif key == 'subtitle_font':
                        default_value = '俪金黑'
                    elif key == 'cover_title_font':
                        default_value = '阳华体'
                    else:  # cover_subtitle_font
                        default_value = '俪金黑'
                    
                    e = ttk.Entry(group_frame, width=35)
                    e.insert(0, str(data.get(key, default_value)))
                    e.grid(row=i, column=1, sticky='ew', padx=5, pady=3)
                    entries[key] = e
                elif key == 'cover_background':
                    # 封面底图文件选择
                    frame = ttk.Frame(group_frame)
                    frame.grid(row=i, column=1, sticky='ew', padx=5, pady=3)
                    
                    e = ttk.Entry(frame, width=25)
                    e.insert(0, str(data.get(key, '')))
                    e.pack(side='left', fill='x', expand=True)
                    entries[key] = e
                    
                    def browse_cover():
                        from tkinter import filedialog
                        filename = filedialog.askopenfilename(
                            title="选择封面底图",
                            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif"), ("所有文件", "*.*")]
                        )
                        if filename:
                            e.delete(0, tk.END)
                            e.insert(0, filename)
                    
                    ttk.Button(frame, text="选择", command=browse_cover).pack(side='right', padx=(5, 0))
                elif key.endswith('_size') or key.endswith('_scale'):
                    # 数值输入框
                    if key.endswith('_size'):
                        default_value = '18'
                    else:  # _scale
                        default_value = '1.0'
                    
                    e = ttk.Entry(group_frame, width=35)
                    e.insert(0, str(data.get(key, default_value)))
                    e.grid(row=i, column=1, sticky='ew', padx=5, pady=3)
                    entries[key] = e
                else:
                    # 普通文本输入框
                    e = ttk.Entry(group_frame, width=35)
                    e.insert(0, str(data.get(key, '')))
                    e.grid(row=i, column=1, sticky='ew', padx=5, pady=3)
                    entries[key] = e
                
                # 配置列权重
                group_frame.columnconfigure(1, weight=1)
        
        # 配置滚动区域
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        return entries

    def add_template_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("新增模版")
        win.geometry("800x600")  # 设置更大的窗口尺寸
        
        # 主框架
        main_frame = ttk.Frame(win)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 创建双列布局
        left_frame = ttk.Frame(main_frame)
        right_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        # 配置列权重
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # 左侧列 - 基本信息
        basic_frame = ttk.LabelFrame(left_frame, text="基本信息", padding=10)
        basic_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        ttk.Label(basic_frame, text="模版Key (唯一标识):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        key_entry = ttk.Entry(basic_frame, width=30)
        key_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        basic_frame.columnconfigure(1, weight=1)
        
        # 右侧列 - 模板配置
        config_frame = ttk.LabelFrame(right_frame, text="模板配置", padding=10)
        config_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        form = self._template_form(config_frame, {})
        
        # 底部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        
        def on_save():
            key = key_entry.get().strip() or f"tpl_{int(time.time())}"
            if key in self.templates:
                messagebox.showerror("错误", "模版Key已存在")
                return
            t = {}
            for k, widget in form.items():
                if isinstance(widget, tk.BooleanVar):
                    t[k] = bool(widget.get())
                elif isinstance(widget, tk.StringVar):
                    t[k] = str(widget.get())
                else:
                    t[k] = str(widget.get())
            t['name'] = t.get('name') or key
            self.templates[key] = t
            self.save_templates()
            self.refresh_template_list()
            win.destroy()

        ttk.Button(button_frame, text="保存", command=on_save).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=win.destroy).pack(side='right')

    def _get_selected_template_key(self) -> Optional[str]:
        sel = self.template_list.selection()
        if not sel:
            return None
        vals = self.template_list.item(sel[0]).get('values') or []
        return vals[0] if vals else None

    def edit_selected_template(self):
        key = self._get_selected_template_key()
        if not key:
            messagebox.showwarning("提示", "请先选择一个模版")
            return
        data = dict(self.templates.get(key) or {})
        win = tk.Toplevel(self.root)
        win.title(f"编辑模版 - {key}")
        win.geometry("800x600")  # 设置更大的窗口尺寸
        
        # 主框架
        main_frame = ttk.Frame(win)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 创建双列布局
        left_frame = ttk.Frame(main_frame)
        right_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        # 配置列权重
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # 左侧列 - 基本信息
        basic_frame = ttk.LabelFrame(left_frame, text="基本信息", padding=10)
        basic_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        ttk.Label(basic_frame, text="模版Key:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Label(basic_frame, text=key, font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        # 右侧列 - 模板配置
        config_frame = ttk.LabelFrame(right_frame, text="模板配置", padding=10)
        config_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        form = self._template_form(config_frame, data)
        
        # 底部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)

        def on_save():
            t = {}
            for k, widget in form.items():
                if isinstance(widget, tk.BooleanVar):
                    t[k] = bool(widget.get())
                elif isinstance(widget, tk.StringVar):
                    t[k] = str(widget.get())
                else:
                    t[k] = str(widget.get())
            t['name'] = t.get('name') or key
            self.templates[key] = t
            self.save_templates()
            self.refresh_template_list()
            win.destroy()

        ttk.Button(button_frame, text="测试模版", command=lambda: self._test_template_from_dialog(win, form, key)).pack(side='left')
        ttk.Button(button_frame, text="保存", command=on_save).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=win.destroy).pack(side='right')

    def delete_selected_template(self):
        key = self._get_selected_template_key()
        if not key:
            messagebox.showwarning("提示", "请先选择一个模版")
            return
        if messagebox.askyesno("确认", f"确定删除模版 {key} 吗？"):
            try:
                if key in self.templates:
                    del self.templates[key]
                self.save_templates()
                self.refresh_template_list()
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}")

    def set_active_template(self):
        key = self._get_selected_template_key()
        if not key:
            messagebox.showwarning("提示", "请先选择一个模版")
            return
        cfg = self.config.get('template') or {}
        cfg['active'] = key
        if 'template' not in self.config:
            self.config['template'] = cfg
        else:
            self.config['template'].update(cfg)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"已设置当前模版: {key}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def test_selected_template(self):
        """测试选择的模板"""
        key = self._get_selected_template_key()
        if not key:
            messagebox.showwarning("提示", "请先选择一个模版")
            return
        
        template_data = self.templates.get(key, {})
        if not template_data:
            messagebox.showerror("错误", "模版数据不存在")
            return
        
        # 验证剪映路径
        if not self.jianying_path_entry.get():
            messagebox.showerror("错误", "请先在配置管理中设置剪映草稿文件夹路径")
            return
        
        # 确认测试
        template_name = template_data.get('name', key)
        if not messagebox.askyesno("确认", f"确定要测试模版 '{template_name}' 吗？\n\n这将创建一个测试视频来验证模版效果。"):
            return
        
        def run_test():
            try:
                self.log_message(f"开始测试模版: {template_name}")
                
                # 获取验证后的模板配置
                validated_template = self.validate_template_data(template_data)
                
                # 准备测试数据
                test_data = self._prepare_template_test_data()
                
                # 创建工作流实例
                wf = VideoEditingWorkflow(
                    draft_folder_path=self.jianying_path_entry.get().strip(),
                    project_name=f"模版测试_{template_name}_{int(time.time())}",
                    template_config=validated_template
                )
                
                # 准备输入参数（参考main函数）
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.join(current_dir, '..')
                background_music_path = os.path.join(project_root, 'resource', '华尔兹.mp3')
                
                inputs = {
                    'content': test_data['content'],
                    'digital_video_url': test_data['digital_video_url'],
                    'title': test_data['title'],
                    
                    # 火山引擎ASR配置（使用默认值）
                    'volcengine_appid': '6046310832',
                    'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',
                    
                    # 豆包API配置（使用默认值）
                    'doubao_token': 'adac0afb-5fd4-4c66-badb-370a7ff42df5',
                    'doubao_model': 'doubao-1-5-pro-32k-250115',
                    
                    # 背景音乐配置
                    'background_music_path': background_music_path,
                    'background_music_volume': 0.25,
                    
                    # 封面配置（使用默认值或模板配置）
                    'cover_short_title': validated_template.get('cover_config', {}).get('title_text', '测试标题'),
                    'cover_image_path': validated_template.get('cover_config', {}).get('background', 'resource/查封面.jpg'),
                    'cover_bottom_text': validated_template.get('cover_config', {}).get('subtitle_text', '测试副标题')
                }
                
                # 使用process_workflow方法（参考main函数）
                save_path = wf.process_workflow(inputs, template_config=validated_template)
                self.log_message(f"✅ 模版测试完成，草稿已保存到: {save_path}")
                
                # 显示结果
                self.root.after(0, lambda: messagebox.showinfo(
                    "测试完成", 
                    f"模版测试完成！\n\n模版: {template_name}\n草稿路径: {save_path}\n\n请在剪映中打开草稿查看效果。"
                ))
                
            except Exception as e:
                error_msg = f"模版测试失败: {e}"
                self.log_message(error_msg)
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        
        # 在后台线程中运行测试
        threading.Thread(target=run_test, daemon=True).start()
    
    def _prepare_template_test_data(self):
        """准备模板测试数据"""
        import random
        
        # 多种测试场景
        test_scenarios = [
            {
                'title': '半辈子追房涨跌年轻人安稳何在',
                'content': '没房子的时候，工资跑不过房价；\n咬牙买下之后，房价却开始回调，资产在不知不觉中缩水。\n曾经以为，买房就等于安稳，\n结果发现，压力才刚刚开始。\n\n拼了半辈子，竟追不上一套房的涨跌节奏。\n这不只是一个人的经历，\n而是一代人共同面对的现实。\n\n房价起落之间，承载着太多期待与无奈。\n这届年轻人，真的不容易。',
                'digital_video_url': 'https://oss.oemi.jdword.com/prod/order/video/202509/V20250909223211001.mp4'
            },
            {
                'title': '科技改变生活未来已来',
                'content': '人工智能正在重塑我们的世界，\n从智能手机到自动驾驶，\n从虚拟现实到元宇宙，\n科技的力量无处不在。\n\n每一次技术突破，\n都让我们的生活更加便利，\n也让我们的未来充满无限可能。\n\n拥抱变化，迎接未来，\n这就是我们的时代。',
                'digital_video_url': 'https://oss.oemi.jdword.com/prod/order/video/202509/V20250909223211001.mp4'
            },
            {
                'title': '健康生活从今天开始',
                'content': '身体是革命的本钱，\n健康是最大的财富。\n\n每天坚持运动，\n合理搭配饮食，\n保持良好作息，\n让健康成为习惯。\n\n投资健康，\n就是投资未来。\n\n从今天开始，\n让我们一起拥抱健康生活。',
                'digital_video_url': 'https://oss.oemi.jdword.com/prod/order/video/202509/V20250909223211001.mp4'
            }
        ]
        
        # 随机选择一个测试场景
        return random.choice(test_scenarios)
    
    def _test_template_from_dialog(self, dialog_window, form, template_key):
        """从编辑对话框测试模板"""
        try:
            # 验证剪映路径
            if not self.jianying_path_entry.get():
                messagebox.showerror("错误", "请先在配置管理中设置剪映草稿文件夹路径")
                return
            
            # 从表单获取当前模板数据
            template_data = {}
            for k, widget in form.items():
                if isinstance(widget, tk.BooleanVar):
                    template_data[k] = bool(widget.get())
                elif isinstance(widget, tk.StringVar):
                    template_data[k] = str(widget.get())
                else:
                    template_data[k] = str(widget.get())
            template_data['name'] = template_data.get('name') or template_key
            
            # 确认测试
            template_name = template_data.get('name', template_key)
            if not messagebox.askyesno("确认", f"确定要测试模版 '{template_name}' 吗？\n\n这将创建一个测试视频来验证模版效果。"):
                return
            
            def run_test():
                try:
                    self.log_message(f"开始测试模版: {template_name}")
                    
                    # 获取验证后的模板配置
                    validated_template = self.validate_template_data(template_data)
                    
                    # 准备测试数据
                    test_data = self._prepare_template_test_data()
                    
                    # 创建工作流实例
                    wf = VideoEditingWorkflow(
                        draft_folder_path=self.jianying_path_entry.get().strip(),
                        project_name=f"模版测试_{template_name}_{int(time.time())}",
                        template_config=validated_template
                    )
                    
                    # 准备输入参数（参考main函数）
                    import os
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.join(current_dir, '..')
                    background_music_path = os.path.join(project_root, 'resource', '华尔兹.mp3')
                    
                    inputs = {
                        'content': test_data['content'],
                        'digital_video_url': test_data['digital_video_url'],
                        'title': test_data['title'],
                        
                        # 火山引擎ASR配置（使用默认值）
                        'volcengine_appid': '6046310832',
                        'volcengine_access_token': 'fMotJVOsyk6K_dDRoqM14kGdMJYBrcJY',
                        
                        # 豆包API配置（使用默认值）
                        'doubao_token': 'adac0afb-5fd4-4c66-badb-370a7ff42df5',
                        'doubao_model': 'doubao-1-5-pro-32k-250115',
                        
                        # 背景音乐配置
                        'background_music_path': background_music_path,
                        'background_music_volume': 0.25,
                        
                        # 封面配置（使用默认值或模板配置）
                        'cover_short_title': validated_template.get('cover_config', {}).get('title_text', '测试标题'),
                        'cover_image_path': validated_template.get('cover_config', {}).get('background', 'resource/查封面.jpg'),
                        'cover_bottom_text': validated_template.get('cover_config', {}).get('subtitle_text', '测试副标题')
                    }
                    
                    # 使用process_workflow方法（参考main函数）
                    save_path = wf.process_workflow(inputs, template_config=validated_template)
                    self.log_message(f"✅ 模版测试完成，草稿已保存到: {save_path}")
                    
                    # 显示结果
                    self.root.after(0, lambda: messagebox.showinfo(
                        "测试完成", 
                        f"模版测试完成！\n\n模版: {template_name}\n草稿路径: {save_path}\n\n请在剪映中打开草稿查看效果。"
                    ))
                    
                except Exception as e:
                    error_msg = f"模版测试失败: {e}"
                    self.log_message(error_msg)
                    self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            
            # 在后台线程中运行测试
            threading.Thread(target=run_test, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("错误", f"测试模版失败: {e}")
    
    def create_config_tab(self):
        """创建配置标签页"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="配置管理")
        
        # 创建滚动区域
        canvas = tk.Canvas(config_frame)
        scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 配置表单
        ttk.Label(scrollable_frame, text="API配置", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Coze配置
        coze_frame = ttk.LabelFrame(scrollable_frame, text="Coze API配置")
        coze_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(coze_frame, text="Bearer Token:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.coze_token_entry = ttk.Entry(coze_frame, width=60)
        self.coze_token_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(coze_frame, text="Workflow ID:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.coze_workflow_id_entry = ttk.Entry(coze_frame, width=60)
        self.coze_workflow_id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 飞书配置
        feishu_frame = ttk.LabelFrame(scrollable_frame, text="飞书配置")
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
        volc_frame = ttk.LabelFrame(scrollable_frame, text="火山引擎ASR配置")
        volc_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(volc_frame, text="App ID:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.volc_appid_entry = ttk.Entry(volc_frame, width=60)
        self.volc_appid_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(volc_frame, text="Access Token:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.volc_token_entry = ttk.Entry(volc_frame, width=60)
        self.volc_token_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 豆包配置
        doubao_frame = ttk.LabelFrame(scrollable_frame, text="豆包API配置")
        doubao_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(doubao_frame, text="Token:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.doubao_token_entry = ttk.Entry(doubao_frame, width=60)
        self.doubao_token_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 剪映配置
        jianying_frame = ttk.LabelFrame(scrollable_frame, text="剪映配置")
        jianying_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(jianying_frame, text="草稿文件夹路径:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.jianying_path_entry = ttk.Entry(jianying_frame, width=60)
        self.jianying_path_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(jianying_frame, text="浏览", command=self.browse_jianying_path).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(jianying_frame, text="FFmpeg 路径(可选):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.ffmpeg_path_entry = ttk.Entry(jianying_frame, width=60)
        self.ffmpeg_path_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(jianying_frame, text="浏览", command=self.browse_ffmpeg_path).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(jianying_frame, text="背景音乐文件(可选):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.bgm_path_entry = ttk.Entry(jianying_frame, width=60)
        self.bgm_path_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(jianying_frame, text="浏览", command=self.browse_bgm_path).grid(row=2, column=2, padx=5, pady=5)
        
        # 网络代理配置
        proxy_frame = ttk.LabelFrame(scrollable_frame, text="网络代理配置")
        proxy_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(proxy_frame, text="HTTP_PROXY:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.http_proxy_entry = ttk.Entry(proxy_frame, width=60)
        self.http_proxy_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(proxy_frame, text="HTTPS_PROXY:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.https_proxy_entry = ttk.Entry(proxy_frame, width=60)
        self.https_proxy_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(proxy_frame, text="NO_PROXY:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.no_proxy_entry = ttk.Entry(proxy_frame, width=60)
        self.no_proxy_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # 飞书异步工作流配置
        feishu_async_frame = ttk.LabelFrame(scrollable_frame, text="飞书异步工作流配置")
        feishu_async_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(feishu_async_frame, text="App Token:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.feishu_app_token_entry = ttk.Entry(feishu_async_frame, width=60)
        self.feishu_app_token_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(feishu_async_frame, text="内容表ID:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.feishu_content_table_id_entry = ttk.Entry(feishu_async_frame, width=60)
        self.feishu_content_table_id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(feishu_async_frame, text="账号表ID:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.feishu_account_table_id_entry = ttk.Entry(feishu_async_frame, width=60)
        self.feishu_account_table_id_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(feishu_async_frame, text="声音表ID:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.feishu_voice_table_id_entry = ttk.Entry(feishu_async_frame, width=60)
        self.feishu_voice_table_id_entry.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(feishu_async_frame, text="数字人表ID:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.feishu_digital_table_id_entry = ttk.Entry(feishu_async_frame, width=60)
        self.feishu_digital_table_id_entry.grid(row=4, column=1, padx=5, pady=5)
        
        # 并发配置
        concurrent_frame = ttk.LabelFrame(scrollable_frame, text="并发配置")
        concurrent_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(concurrent_frame, text="Coze最大并发数:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.max_coze_concurrent_entry = ttk.Entry(concurrent_frame, width=20)
        self.max_coze_concurrent_entry.insert(0, "16")
        self.max_coze_concurrent_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(concurrent_frame, text="视频合成最大并发数:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.max_synthesis_workers_entry = ttk.Entry(concurrent_frame, width=20)
        self.max_synthesis_workers_entry.insert(0, "4")
        self.max_synthesis_workers_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(concurrent_frame, text="轮询间隔(秒):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.poll_interval_entry = ttk.Entry(concurrent_frame, width=20)
        self.poll_interval_entry.insert(0, "30")
        self.poll_interval_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="保存配置", command=self.save_config).pack(side='left', padx=5)
        ttk.Button(button_frame, text="导入模板配置", command=self.import_template_config).pack(side='left', padx=5)
        ttk.Button(button_frame, text="清空配置", command=self.clear_config).pack(side='left', padx=5)
        
        # 布局滚动区域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 加载现有配置
        self.load_config_to_gui()
        # 首次应用代理设置
        self.apply_proxy_config()
    
    
    def create_feishu_async_tab(self):
        """创建飞书异步批量工作流标签页"""
        # 创建可滚动容器，适配小屏幕
        _async_tab_outer = ttk.Frame(self.notebook)
        self.notebook.add(_async_tab_outer, text="飞书视频批量生成")
        _async_canvas = tk.Canvas(_async_tab_outer, highlightthickness=0)
        _async_scrollbar = ttk.Scrollbar(_async_tab_outer, orient="vertical", command=_async_canvas.yview)
        _async_inner = ttk.Frame(_async_canvas)
        _async_inner.bind("<Configure>", lambda e: _async_canvas.configure(scrollregion=_async_canvas.bbox("all")))
        _async_canvas.create_window((0, 0), window=_async_inner, anchor="nw")
        _async_canvas.configure(yscrollcommand=_async_scrollbar.set)
        _async_canvas.pack(side="left", fill="both", expand=True)
        _async_scrollbar.pack(side="right", fill="y")
        # 后续使用 async_frame 指向滚动区域内部容器
        async_frame = _async_inner
        
        ttk.Label(async_frame, text="飞书视频批量生成", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 工作流控制区域
        control_frame = ttk.LabelFrame(async_frame, text="工作流控制")
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # 过滤条件配置
        filter_frame = ttk.LabelFrame(control_frame, text="过滤条件")
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(filter_frame, text="状态过滤:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.status_filter_entry = ttk.Entry(filter_frame, width=40)
        self.status_filter_entry.insert(0, "视频草稿生成")
        self.status_filter_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="包含记录ID:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.include_ids_entry = ttk.Entry(filter_frame, width=40)
        self.include_ids_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(filter_frame, text="(用逗号分隔)").grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="排除记录ID:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.exclude_ids_entry = ttk.Entry(filter_frame, width=40)
        self.exclude_ids_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(filter_frame, text="(用逗号分隔)").grid(row=2, column=2, padx=5, pady=5)
        
        # 模板选择配置
        template_frame = ttk.LabelFrame(control_frame, text="模板配置")
        template_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(template_frame, text="选择模板:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.feishu_template_var = tk.StringVar()
        self.feishu_template_combo = ttk.Combobox(template_frame, textvariable=self.feishu_template_var, width=37, state='readonly')
        self.feishu_template_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # 刷新模板列表
        self.refresh_feishu_template_list()
        
        ttk.Button(template_frame, text="刷新模板", command=self.refresh_feishu_template_list).grid(row=0, column=2, padx=5, pady=5)
        
        # 操作按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="获取飞书内容", command=self.fetch_feishu_content).pack(side='left', padx=5)
        ttk.Button(button_frame, text="开始异步批量处理", command=self.start_feishu_async_batch).pack(side='left', padx=5)
        ttk.Button(button_frame, text="停止处理", command=self.stop_feishu_async_batch).pack(side='left', padx=5)
        
        # 内容预览区域
        preview_frame = ttk.LabelFrame(async_frame, text="飞书内容预览")
        preview_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 预览文本区域
        self.feishu_content_text = scrolledtext.ScrolledText(preview_frame, height=15, width=80)
        self.feishu_content_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 预览操作按钮
        preview_button_frame = ttk.Frame(preview_frame)
        preview_button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(preview_button_frame, text="清空预览", command=self.clear_feishu_content).pack(side='left', padx=5)
        ttk.Button(preview_button_frame, text="确认并开始批量处理", command=self.confirm_and_start_batch).pack(side='left', padx=5)
        
        # 进度显示区域
        progress_frame = ttk.LabelFrame(async_frame, text="实时进度监控")
        progress_frame.pack(fill='x', padx=20, pady=10)
        
        # 主要进度状态
        self.async_progress_label = ttk.Label(progress_frame, text="准备就绪", font=('Arial', 10, 'bold'))
        self.async_progress_label.pack(pady=5)
        
        # 进度条
        self.async_progress_bar = ttk.Progressbar(progress_frame, length=600, mode='determinate')
        self.async_progress_bar.pack(padx=10, pady=5)
        
        # 配置进度条样式
        self.style = ttk.Style()
        self.style.configure("Normal.Horizontal.TProgressbar", background='#4CAF50')  # 绿色
        self.style.configure("Error.Horizontal.TProgressbar", background='#F44336')   # 红色
        self.async_progress_bar.configure(style="Normal.Horizontal.TProgressbar")
        
        # 详细进度信息
        progress_info_frame = ttk.Frame(progress_frame)
        progress_info_frame.pack(fill='x', padx=10, pady=5)
        
        # 当前处理状态
        self.current_status_label = ttk.Label(progress_info_frame, text="状态: 待机")
        self.current_status_label.pack(side='left', padx=5)
        
        
        # 已运行时间
        self.runtime_label = ttk.Label(progress_info_frame, text="运行时间: 00:00:00")
        self.runtime_label.pack(side='left', padx=20)
        
        # 统计信息显示
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="任务统计: 0/0 (0% 完成)", font=('Arial', 10, 'bold'))
        self.stats_label.pack(side='left', padx=5)
        
        self.detailed_stats_label = ttk.Label(stats_frame, text="运行中: 0 | 失败: 0 | 成功: 0")
        self.detailed_stats_label.pack(side='left', padx=20)
        
        # 不需要任务列表，确保引用安全
        self.async_task_tree = None
        
        # 状态变量
        self.async_workflow = None
        self.async_running = False
        self.async_tasks = {}
        self.task_update_timer = None
    
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
        
        # 模板选择（仅对飞书异步批量工作流显示）
        ttk.Label(create_frame, text="模板选择:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.schedule_template_var = tk.StringVar()
        self.schedule_template_combo = ttk.Combobox(create_frame, textvariable=self.schedule_template_var, width=38, state='readonly')
        self.schedule_template_combo.grid(row=4, column=1, padx=5, pady=5)
        
        # 绑定工作流选择变化事件
        self.schedule_workflow_combo.bind('<<ComboboxSelected>>', self.on_schedule_workflow_changed)
        
        ttk.Button(create_frame, text="创建任务", command=self.create_schedule).grid(row=5, column=1, pady=10)
        
        # 任务列表
        list_frame = ttk.LabelFrame(schedule_frame, text="定时任务列表")
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        columns = ('名称', '工作流类型', '工作流', '执行时间', '重复周期', '状态', '下次执行')
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
    
    def on_schedule_workflow_changed(self, event=None):
        """定时任务工作流选择变化事件"""
        try:
            selected_workflow = self.schedule_workflow_combo.get()
            
            # 清空模板选择
            self.schedule_template_var.set('')
            self.schedule_template_combo['values'] = []
            
            # 如果是飞书异步批量工作流，显示模板选择
            if '飞书异步批量' in selected_workflow or 'feishu_async' in selected_workflow.lower():
                self.refresh_schedule_template_list()
                self.schedule_template_combo.grid()  # 显示模板选择框
            else:
                self.schedule_template_combo.grid_remove()  # 隐藏模板选择框
                
        except Exception as e:
            self.log_message(f"工作流选择变化处理失败: {e}")
    
    def refresh_schedule_template_list(self):
        """刷新定时任务模板选择列表"""
        try:
            template_list = []
            for key, template in (self.templates or {}).items():
                template_name = template.get('name', key)
                template_list.append(f"{key} - {template_name}")
            
            self.schedule_template_combo['values'] = template_list
            
            # 设置默认选择
            if template_list and not self.schedule_template_var.get():
                # 优先选择当前激活的模板
                active_key = ((self.config.get('template') or {}).get('active') or 'default')
                for item in template_list:
                    if item.startswith(f"{active_key} -"):
                        self.schedule_template_var.set(item)
                        break
                else:
                    # 如果没有找到激活的模板，选择第一个
                    self.schedule_template_var.set(template_list[0])
            
        except Exception as e:
            self.log_message(f"刷新定时任务模板列表失败: {e}")
    
    def create_log_tab(self):
        """创建日志标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="运行日志")
        
        # 顶部控制区域
        control_frame = ttk.LabelFrame(log_frame, text="日志控制")
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # 会话选择区域
        session_frame = ttk.Frame(control_frame)
        session_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(session_frame, text="选择会话:").pack(side='left', padx=5)
        self.session_var = tk.StringVar()
        self.session_combo = ttk.Combobox(session_frame, textvariable=self.session_var, width=30, state='readonly')
        self.session_combo.pack(side='left', padx=5)
        self.session_combo.bind('<<ComboboxSelected>>', self.on_session_selected)
        
        ttk.Button(session_frame, text="刷新会话", command=self.refresh_sessions).pack(side='left', padx=5)
        
        # 操作按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).pack(side='left', padx=5)
        ttk.Button(button_frame, text="导出当前日志", command=self.export_log).pack(side='left', padx=5)
        ttk.Button(button_frame, text="导出选中会话", command=self.export_session_log).pack(side='left', padx=5)
        ttk.Button(button_frame, text="导出所有日志", command=self.export_all_logs).pack(side='left', padx=5)
        ttk.Button(button_frame, text="打开日志目录", command=self.open_logs_dir).pack(side='left', padx=5)
        
        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=100)
        self.log_text.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 初始化会话列表
        self.refresh_sessions()
    
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
        # 可选工具与音频
        self.config['tools'] = {
            'ffmpeg_path': self.ffmpeg_path_entry.get()
        }
        self.config['audio'] = {
            'bgm_path': self.bgm_path_entry.get()
        }
        self.config['proxy'] = {
            'http_proxy': self.http_proxy_entry.get(),
            'https_proxy': self.https_proxy_entry.get(),
            'no_proxy': self.no_proxy_entry.get()
        }
        self.config['feishu_async'] = {
            'app_token': self.feishu_app_token_entry.get(),
            'content_table_id': self.feishu_content_table_id_entry.get(),
            'account_table_id': self.feishu_account_table_id_entry.get(),
            'voice_table_id': self.feishu_voice_table_id_entry.get(),
            'digital_table_id': self.feishu_digital_table_id_entry.get()
        }
        self.config['concurrent'] = {
            'max_coze_concurrent': int(self.max_coze_concurrent_entry.get() or 16),
            'max_synthesis_workers': int(self.max_synthesis_workers_entry.get() or 4),
            'poll_interval': int(self.poll_interval_entry.get() or 30)
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "配置保存成功")
            self.log_message("配置保存成功")
            # 应用代理
            self.apply_proxy_config()
            # 应用 ffmpeg 路径
            self.apply_ffmpeg_path()
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
        if 'tools' in self.config:
            self.ffmpeg_path_entry.insert(0, self.config['tools'].get('ffmpeg_path', ''))
        if 'audio' in self.config:
            self.bgm_path_entry.insert(0, self.config['audio'].get('bgm_path', ''))
        
        # 代理配置
        if 'proxy' in self.config:
            self.http_proxy_entry.insert(0, self.config['proxy'].get('http_proxy', ''))
            self.https_proxy_entry.insert(0, self.config['proxy'].get('https_proxy', ''))
            self.no_proxy_entry.insert(0, self.config['proxy'].get('no_proxy', ''))
        
        if 'feishu_async' in self.config:
            self.feishu_app_token_entry.insert(0, self.config['feishu_async'].get('app_token', ''))
            self.feishu_content_table_id_entry.insert(0, self.config['feishu_async'].get('content_table_id', ''))
            self.feishu_account_table_id_entry.insert(0, self.config['feishu_async'].get('account_table_id', ''))
            self.feishu_voice_table_id_entry.insert(0, self.config['feishu_async'].get('voice_table_id', ''))
            self.feishu_digital_table_id_entry.insert(0, self.config['feishu_async'].get('digital_table_id', ''))
        
        if 'concurrent' in self.config:
            self.max_coze_concurrent_entry.delete(0, tk.END)
            self.max_coze_concurrent_entry.insert(0, str(self.config['concurrent'].get('max_coze_concurrent', 16)))
            self.max_synthesis_workers_entry.delete(0, tk.END)
            self.max_synthesis_workers_entry.insert(0, str(self.config['concurrent'].get('max_synthesis_workers', 4)))
            self.poll_interval_entry.delete(0, tk.END)
            self.poll_interval_entry.insert(0, str(self.config['concurrent'].get('poll_interval', 30)))
    
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
            # 首次无文件时，写入一个默认的"飞书视频批量生成"工作流
            self.workflows = {
                "feishu_async_default": {
                    "id": "feishu_async_default",
                    "name": "飞书视频批量生成",
                    "type": "feishu_async_batch",
                    "created_at": datetime.now().isoformat()
                }
            }
            try:
                with open(self.workflows_file, 'w', encoding='utf-8') as f:
                    json.dump(self.workflows, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.log_message(f"初始化默认工作流失败: {e}")
    
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

    def load_templates(self):
        """加载模板数据"""
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            else:
                # 初始化一个默认模板
                self.templates = {
                    'default': {
                        'name': '默认模版',
                        'title_color': '#FFFFFF',
                        'title_highlight_color': '#FFD700',
                        'title_bg_enabled': True,
                        'title_font': '阳华体',
                        'title_font_size': '24',
                        'title_scale': '1.0',
                        'title_line_spacing': '1.0',
                        'subtitle_color': '#FFFFFF',
                        'subtitle_highlight_color': '#00FFFF',
                        'subtitle_bg_enabled': True,
                        'subtitle_font': '俪金黑',
                        'subtitle_font_size': '18',
                        'subtitle_scale': '1.0',
                        'cover_background': '',
                        'cover_title_font': '阳华体',
                        'cover_title_color': '#FFFFFF',
                        'cover_title_size': '24',
                        'cover_subtitle_font': '俪金黑',
                        'cover_subtitle_color': '#FFFFFF',
                        'cover_subtitle_size': '18'
                    }
                }
                self.save_templates()
        except Exception as e:
            self.log_message(f"加载模板数据失败: {e}")
            self.templates = {}

    def save_templates(self):
        """保存模板数据"""
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"保存模板数据失败: {e}")
    
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
                    self.config['feishu']['app_secret'],
                    self.config['feishu_async']['app_token']  # 使用异步配置中的app_token
                )
                
                data = feishu_client.get_table_data(self.config['feishu_async']['content_table_id'])
                
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
            
            # 获取模板配置（仅对飞书异步批量工作流）
            template_config = None
            if '飞书异步批量' in workflow_id or 'feishu_async' in workflow_id.lower():
                selected_template = self.schedule_template_var.get()
                if selected_template:
                    template_key = selected_template.split(' - ')[0]
                    template_data = self.templates.get(template_key, {})
                    if template_data:
                        template_config = self.validate_template_data(template_data)
                        self.log_message(f"定时任务使用模板: {template_data.get('name', template_key)}")
            
            # 创建定时任务
            schedule_id = str(uuid.uuid4())
            self.schedules[schedule_id] = {
                'id': schedule_id,
                'name': name,
                'workflow_id': workflow_id,
                'time': time_str,
                'repeat': repeat,
                'enabled': True,
                'template_config': template_config,
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
                '',
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

    def create_simple_compose_tab(self):
        """创建简单合成标签页：输入数字人视频URL、BGM、标题、文案，直接合成"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="简单合成")

        ttk.Label(tab, text="数字人视频直合", font=("Arial", 14, "bold")).pack(pady=10)
        form = ttk.LabelFrame(tab, text="参数")
        form.pack(fill='x', padx=20, pady=10)

        ttk.Label(form, text="数字人视频URL:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.simple_dh_url = ttk.Entry(form, width=80)
        self.simple_dh_url.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="背景音乐(可选):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.simple_bgm = ttk.Entry(form, width=80)
        self.simple_bgm.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(form, text="浏览", command=self.browse_simple_bgm).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(form, text="标题:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.simple_title = ttk.Entry(form, width=80)
        self.simple_title.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form, text="文案内容:").grid(row=3, column=0, sticky='nw', padx=5, pady=5)
        self.simple_content = scrolledtext.ScrolledText(form, width=60, height=6)
        self.simple_content.grid(row=3, column=1, padx=5, pady=5)

        btns = ttk.Frame(tab)
        btns.pack(fill='x', padx=20, pady=10)
        ttk.Button(btns, text="开始合成", command=self.start_simple_compose).pack(side='left', padx=5)

    def browse_simple_bgm(self):
        path = filedialog.askopenfilename(title="选择背景音乐", filetypes=[("音频文件", "*.mp3;*.wav;*.aac;*.m4a;*.flac"), ("所有文件", "*.*")])
        if path:
            self.simple_bgm.delete(0, tk.END)
            self.simple_bgm.insert(0, path)

    def start_simple_compose(self):
        """简单合成：下载数字人视频(或直接使用URL)，可选叠加BGM，生成剪映草稿并保存"""
        if not self.jianying_path_entry.get():
            messagebox.showerror("错误", "请先在配置管理中设置剪映草稿文件夹路径")
            return
        url = self.simple_dh_url.get().strip()
        if not url:
            messagebox.showerror("错误", "请填写数字人视频URL")
            return
        title = self.simple_title.get().strip() or "直合视频"
        content = self.simple_content.get(1.0, tk.END).strip()
        bgm = self.simple_bgm.get().strip() or (self.config.get('audio') or {}).get('bgm_path', '')

        def run():
            try:
                self.log_message("开始简单合成…")
                # 获取当前模板配置
                template_config = self.get_current_template()
                self.log_message(f"使用模板: {template_config.get('name', '默认模板')}")
                
                # 构建工作流配置
                wf = VideoEditingWorkflow(
                    draft_folder_path=self.jianying_path_entry.get().strip(),
                    project_name=title,
                    template_config=template_config
                )
                
                # 创建草稿
                wf.create_draft()
                
                # 添加数字人主视频
                wf.add_digital_human_video(url, project_name=title)
                
                # 可选添加BGM
                if bgm:
                    try:
                        wf.add_background_music(bgm, volume=0.3)
                    except Exception as e:
                        self.log_message(f"[WARN] 背景音乐添加失败: {e}")
                
                # 添加标题（如果提供）
                if title:
                    try:
                        wf.add_three_line_title(title)
                        self.log_message(f"已添加标题: {title}")
                    except Exception as e:
                        self.log_message(f"[WARN] 标题添加失败: {e}")
                
                # 添加字幕（如果提供）
                if content:
                    try:
                        # 将文案按句分割作为字幕
                        sentences = [s.strip() for s in content.split('。') if s.strip()]
                        if sentences:
                            # 创建字幕数据
                            caption_data = []
                            current_time = 0.0
                            for sentence in sentences:
                                caption_data.append({
                                    'text': sentence,
                                    'start': current_time,
                                    'end': current_time + 3.0  # 每句3秒
                                })
                                current_time += 3.0
                            
                            wf.add_captions(caption_data)
                            self.log_message(f"已添加字幕: {len(sentences)} 句")
                    except Exception as e:
                        self.log_message(f"[WARN] 字幕添加失败: {e}")
                
                # 保存草稿
                save_path = wf.save_project()
                self.log_message(f"简单合成完成，草稿已保存到: {save_path}")
                messagebox.showinfo("完成", f"合成完成，草稿已保存到: {save_path}")
            except Exception as e:
                self.log_message(f"简单合成失败: {e}")
                messagebox.showerror("错误", f"简单合成失败: {e}")

        threading.Thread(target=run, daemon=True).start()
    
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
            
            # 根据工作流对象的类型执行
            workflow_type = (workflow or {}).get('type', '')
            if workflow_type == 'manual':
                result = self.generate_video_from_content(
                    workflow.get('content', ''),
                    workflow.get('digital_no'),
                    workflow.get('voice_id')
                )
            elif workflow_type == 'feishu_async_batch':
                # 执行飞书异步批量工作流
                self.log_message(f"开始执行飞书视频批量生成定时任务: {schedule.get('name')}")
                
                # 检查配置
                if not self.check_feishu_async_config():
                    self.log_message("飞书视频批量生成配置不完整，跳过执行")
                    return
                
                # 构建配置
                config = self.build_feishu_async_config()
                
                # 如果定时任务中有模板配置，使用定时任务的模板
                template_config = schedule.get('template_config')
                if template_config:
                    config['template_config'] = template_config
                    self.log_message(f"定时任务使用模板: {template_config.get('name', '未知模板')}")
                
                # 创建工作流实例
                async_workflow = FeishuAsyncBatchWorkflow(config)
                
                # 执行异步批量处理
                result = async_workflow.process_async_batch(
                    filter_condition=self.build_filter_condition(),
                    include_ids=None,
                    exclude_ids=None,
                    save_results=True
                )
                
                if result.get('success'):
                    success_rate = result.get('success_rate', 0)
                    total_tasks = result.get('total_tasks', 0)
                    finished_tasks = result.get('finished_tasks', 0)
                    self.log_message(f"飞书异步批量定时任务完成！成功率: {success_rate:.1f}% ({finished_tasks}/{total_tasks})")
                else:
                    self.log_message(f"飞书异步批量定时任务失败: {result.get('message', '未知错误')}")
            else:
                self.log_message(f"不支持的工作流类型: {workflow_type}")
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
        session_info = f"[会话:{self.current_session_id}]" if self.current_session_id else "[系统]"
        log_entry = f"[{timestamp}] {session_info} {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 存储到当前会话日志
        if self.current_session_id:
            if self.current_session_id not in self.session_logs:
                self.session_logs[self.current_session_id] = []
            self.session_logs[self.current_session_id].append(log_entry.strip())
            # 追加写入原始日志文件
            try:
                if not self.current_session_log_file:
                    self.current_session_log_file = os.path.join(self.logs_dir, f"{self.current_session_id}.log")
                with open(self.current_session_log_file, 'a', encoding='utf-8') as lf:
                    lf.write(log_entry)
            except Exception:
                pass
        
        # 限制日志长度
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 1000:
            self.log_text.delete(1.0, f"{len(lines)-1000}.0")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("日志已清空")
    
    def refresh_sessions(self):
        """刷新会话列表"""
        sessions = list(self.session_logs.keys())
        if self.current_session_id and self.current_session_id not in sessions:
            sessions.append(self.current_session_id)
        sessions.sort(reverse=True)  # 按时间倒序
        self.session_combo['values'] = sessions
        if sessions and not self.session_var.get():
            self.session_var.set(sessions[0])
    
    def on_session_selected(self, event=None):
        """选择会话时的处理"""
        selected_session = self.session_var.get()
        if selected_session and selected_session in self.session_logs:
            # 显示选中会话的日志
            self.log_text.delete(1.0, tk.END)
            for log_entry in self.session_logs[selected_session]:
                self.log_text.insert(tk.END, log_entry + '\n')
        elif selected_session == "当前日志":
            # 显示当前所有日志
            pass  # 保持当前显示
    
    def export_log(self):
        """导出当前显示的日志"""
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
    
    def export_session_log(self):
        """导出选中会话的日志"""
        selected_session = self.session_var.get()
        if not selected_session or selected_session not in self.session_logs:
            messagebox.showwarning("警告", "请先选择一个会话")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialvalue=f"log_{selected_session}.txt"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    for log_entry in self.session_logs[selected_session]:
                        f.write(log_entry + '\n')
                messagebox.showinfo("成功", f"会话日志已导出到: {filename}")
                self.log_message(f"会话 {selected_session} 日志已导出到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出会话日志失败: {e}")
    
    def export_all_logs(self):
        """导出所有日志"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialvalue=f"all_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== 所有会话日志 ===\n\n")
                    for session_id, logs in sorted(self.session_logs.items()):
                        f.write(f"=== 会话: {session_id} ===\n")
                        for log_entry in logs:
                            f.write(log_entry + '\n')
                        f.write("\n")
                messagebox.showinfo("成功", f"所有日志已导出到: {filename}")
                self.log_message(f"所有日志已导出到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出所有日志失败: {e}")
    
    def open_logs_dir(self):
        """打开日志目录"""
        try:
            os.makedirs(self.logs_dir, exist_ok=True)
            if sys.platform.startswith('win'):
                os.startfile(self.logs_dir)
            else:
                webbrowser.open(self.logs_dir)
        except Exception as e:
            messagebox.showerror("错误", f"打开日志目录失败: {e}")

    def apply_proxy_config(self):
        """应用代理配置到进程环境与requests默认环境"""
        try:
            proxy_cfg = self.config.get('proxy', {})
            http_proxy = (self.http_proxy_entry.get() if hasattr(self, 'http_proxy_entry') else '') or proxy_cfg.get('http_proxy', '')
            https_proxy = (self.https_proxy_entry.get() if hasattr(self, 'https_proxy_entry') else '') or proxy_cfg.get('https_proxy', '')
            no_proxy = (self.no_proxy_entry.get() if hasattr(self, 'no_proxy_entry') else '') or proxy_cfg.get('no_proxy', '')
            
            # 设置/清理环境变量
            for key, val in [('HTTP_PROXY', http_proxy), ('HTTPS_PROXY', https_proxy), ('NO_PROXY', no_proxy)]:
                if val:
                    os.environ[key] = val
                    os.environ[key.lower()] = val
                else:
                    os.environ.pop(key, None)
                    os.environ.pop(key.lower(), None)
            
            self.log_message("代理配置已应用")
        except Exception as e:
            self.log_message(f"代理配置应用失败: {e}")
    
    def fetch_feishu_content(self):
        """获取飞书内容并预览（应用过滤条件）"""
        def fetch_content():
            try:
                self.log_message("开始获取飞书内容...")
                
                # 检查飞书配置
                if 'feishu_async' not in self.config or not self.config['feishu_async'].get('app_token'):
                    raise ValueError("请先配置飞书异步工作流参数")
                
                # 创建飞书客户端
                feishu_client = FeishuClient(
                    self.config['feishu']['app_id'],
                    self.config['feishu']['app_secret'],
                    self.config['feishu_async']['app_token']
                )
                
                # 构建过滤条件
                status_filter = self.status_filter_entry.get().strip()
                include_ids = self.include_ids_entry.get().strip()
                exclude_ids = self.exclude_ids_entry.get().strip()
                
                filter_condition = feishu_client.build_filter_condition(
                    status_filter, include_ids, exclude_ids
                )
                
                # 记录过滤条件信息
                filter_info = []
                if status_filter:
                    filter_info.append(f"状态: {status_filter}")
                if include_ids:
                    filter_info.append(f"包含ID: {include_ids}")
                if exclude_ids:
                    filter_info.append(f"排除ID: {exclude_ids}")
                
                if filter_info:
                    self.log_message(f"应用过滤条件: {', '.join(filter_info)}")
                else:
                    self.log_message("未设置过滤条件，获取所有记录")
                
                # 获取内容表数据（应用过滤条件）
                content_table_id = self.config['feishu_async']['content_table_id']
                data = feishu_client.get_table_data(content_table_id, filter_condition)
                
                # 存储数据
                self.feishu_content_data = data
                
                # 在GUI中显示数据
                self.root.after(0, self.display_feishu_content, data)
                self.log_message(f"成功获取飞书内容，共{len(data)}条记录（已应用过滤条件）")
                
            except Exception as e:
                error_msg = f"获取飞书内容失败: {e}"
                self.root.after(0, self.log_message, error_msg)
                messagebox.showerror("错误", error_msg)
        
        threading.Thread(target=fetch_content, daemon=True).start()
    
    def display_feishu_content(self, data):
        """显示飞书内容预览"""
        self.feishu_content_text.delete(1.0, tk.END)
        
        # 显示过滤条件信息
        filter_info = []
        status_filter = self.status_filter_entry.get().strip()
        include_ids = self.include_ids_entry.get().strip()
        exclude_ids = self.exclude_ids_entry.get().strip()
        
        if status_filter:
            filter_info.append(f"状态: {status_filter}")
        if include_ids:
            filter_info.append(f"包含ID: {include_ids}")
        if exclude_ids:
            filter_info.append(f"排除ID: {exclude_ids}")
        
        if filter_info:
            self.feishu_content_text.insert(tk.END, f"过滤条件: {', '.join(filter_info)}\n")
            self.feishu_content_text.insert(tk.END, "=" * 50 + "\n\n")
        else:
            self.feishu_content_text.insert(tk.END, "过滤条件: 无（显示所有记录）\n")
            self.feishu_content_text.insert(tk.END, "=" * 50 + "\n\n")
        
        if not data:
            self.feishu_content_text.insert(tk.END, "没有获取到符合条件的数据")
            return
        
        self.feishu_content_text.insert(tk.END, f"共找到 {len(data)} 条记录:\n\n")
        
        for i, record in enumerate(data):
            self.feishu_content_text.insert(tk.END, f"记录 {i+1}:\n")
            for key, value in record.items():
                # 限制显示长度，避免内容过长
                display_value = str(value)
                if len(display_value) > 100:
                    display_value = display_value[:100] + "..."
                self.feishu_content_text.insert(tk.END, f"  {key}: {display_value}\n")
            self.feishu_content_text.insert(tk.END, "\n")
    
    def clear_feishu_content(self):
        """清空飞书内容预览"""
        self.feishu_content_text.delete(1.0, tk.END)
        self.feishu_content_data = []
        self.log_message("清空飞书内容预览")
    
    def confirm_and_start_batch(self):
        """确认并开始批量处理"""
        if not self.feishu_content_data:
            messagebox.showwarning("警告", "请先获取飞书内容")
            return
        
        # 显示确认对话框
        record_count = len(self.feishu_content_data)
        result = messagebox.askyesno(
            "确认批量处理", 
            f"即将开始处理 {record_count} 条记录，是否继续？\n\n"
            f"过滤条件：\n"
            f"- 状态过滤: {self.status_filter_entry.get()}\n"
            f"- 包含记录ID: {self.include_ids_entry.get() or '无'}\n"
            f"- 排除记录ID: {self.exclude_ids_entry.get() or '无'}"
        )
        
        if result:
            self.log_message(f"用户确认开始批量处理 {record_count} 条记录")
            self.start_feishu_async_batch()
    
    def start_feishu_async_batch(self):
        """开始飞书异步批量处理"""
        def run_async_batch():
            try:
                self.log_message("开始飞书异步批量处理...")
                
                # 检查配置
                if not self.check_feishu_async_config():
                    return
                
                # 生成新的会话ID
                self.current_session_id = f"feishu_async_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # 记录开始时间
                self.start_time = datetime.now()
                
                # 更新UI状态
                self.root.after(0, self.update_async_progress, "正在初始化工作流...")
                self.root.after(0, self.reset_progress_bar_style)
                self.root.after(0, self.async_progress_bar.config, {'value': 0})
                
                # 构建配置
                config = self.build_feishu_async_config()
                
                # 创建工作流实例
                self.async_workflow = FeishuAsyncBatchWorkflow(config)
                self.async_running = True
                
                # 获取过滤条件
                filter_condition = self.build_filter_condition()
                include_ids = self.get_include_ids()
                exclude_ids = self.get_exclude_ids()
                
                # 开始处理
                self.root.after(0, self.update_async_progress, "正在处理任务...")
                
                # 启动实时任务状态更新
                self.start_task_status_monitor()
                
                result = self.async_workflow.process_async_batch(
                    filter_condition=filter_condition,
                    include_ids=include_ids,
                    exclude_ids=exclude_ids,
                    save_results=True
                )
                
                # 处理完成
                self.async_running = False
                self.root.after(0, self.async_progress_bar.config, {'value': 100})
                self.root.after(0, self.stop_task_status_monitor)
                self.root.after(0, self.refresh_sessions)
                
                if result.get('success'):
                    # 以实际任务最终状态为准重新计算指标
                    total_tasks = 0
                    completed_tasks = 0
                    failed_tasks = 0
                    try:
                        tasks_data = getattr(self.async_workflow, 'async_processor', None)
                        tasks_dict = tasks_data.tasks if tasks_data else {}
                        total_tasks = len(tasks_dict)
                        for t in tasks_dict.values():
                            status = t.status.value if hasattr(t.status, 'value') else str(t.status)
                            if status in ['finished', 'completed']:
                                completed_tasks += 1
                            elif status in ['failed']:
                                failed_tasks += 1
                    except Exception:
                        pass
                    finished_tasks = completed_tasks + failed_tasks if total_tasks else result.get('finished_tasks', 0)
                    success_rate = (completed_tasks / total_tasks * 100) if total_tasks else result.get('success_rate', 0)
                    
                    self.root.after(0, self.update_async_progress, 
                                  f"处理完成！成功率: {success_rate:.1f}% ({finished_tasks}/{total_tasks})")
                    self.log_message(f"飞书异步批量处理完成！成功率: {success_rate:.1f}%")
                    messagebox.showinfo("成功", f"批量处理完成！\n成功率: {success_rate:.1f}%\n完成任务: {finished_tasks}/{total_tasks}")
                else:
                    self.root.after(0, self.clear_task_info_on_failure)
                    self.root.after(0, self.update_async_progress, "处理失败")
                    self.root.after(0, self.refresh_sessions)
                    self.log_message(f"飞书异步批量处理失败: {result.get('message', '未知错误')}")
                    messagebox.showerror("错误", f"批量处理失败: {result.get('message', '未知错误')}")
                
            except Exception as e:
                self.async_running = False
                self.root.after(0, self.stop_task_status_monitor)
                self.root.after(0, self.clear_task_info_on_failure)
                self.root.after(0, self.refresh_sessions)
                error_msg = f"飞书异步批量处理失败: {e}"
                self.root.after(0, self.update_async_progress, "处理失败")
                self.root.after(0, self.log_message, error_msg)
                messagebox.showerror("错误", error_msg)
        
        if self.async_running:
            messagebox.showwarning("提示", "异步批量处理正在运行中，请先停止当前任务")
            return
        
        threading.Thread(target=run_async_batch, daemon=True).start()
    
    def stop_feishu_async_batch(self):
        """停止飞书异步批量处理"""
        if not self.async_running:
            messagebox.showwarning("提示", "当前没有运行中的异步批量处理任务")
            return
        
        self.async_running = False
        self.reset_progress_bar_style()
        self.async_progress_bar.config({'value': 0})
        self.stop_task_status_monitor()
        self.update_async_progress("已停止处理")
        self.log_message("用户停止了飞书异步批量处理")
        messagebox.showinfo("提示", "已停止异步批量处理")
    
    def view_async_task_status(self):
        """查看异步任务状态"""
        if not self.async_workflow or not self.async_workflow.async_processor:
            messagebox.showwarning("提示", "没有运行中的异步任务")
            return
        
        # 使用实时更新逻辑
        self.update_task_list()
        
        # 获取任务统计信息
        tasks_data = self.async_workflow.async_processor.tasks
        if tasks_data:
            self.log_message(f"更新了 {len(tasks_data)} 个任务的状态")
        else:
            messagebox.showinfo("提示", "没有任务数据")
    
    def _calculate_task_progress(self, task) -> int:
        """计算任务进度"""
        if task.status.value == 'pending':
            return 0
        elif task.status.value == 'submitted':
            return 20
        elif task.status.value == 'running':
            return 50
        elif task.status.value == 'completed':
            return 80
        elif task.status.value == 'synthesizing':
            return 90
        elif task.status.value == 'finished':
            return 100
        elif task.status.value == 'failed':
            return 0
        else:
            return 0
    
    def check_feishu_async_config(self) -> bool:
        """检查飞书异步工作流配置"""
        required_configs = [
            ('feishu', 'app_id', '飞书App ID'),
            ('feishu', 'app_secret', '飞书App Secret'),
            ('feishu_async', 'app_token', '飞书App Token'),
            ('feishu_async', 'content_table_id', '内容表ID'),
            ('coze', 'bearer_token', 'Coze Bearer Token'),
            ('coze', 'workflow_id', 'Coze Workflow ID'),
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
    
    def build_feishu_async_config(self) -> Dict[str, Any]:
        """构建飞书异步工作流配置"""
        config = {
            'api_config': {
                'app_id': self.config['feishu']['app_id'],
                'app_secret': self.config['feishu']['app_secret'],
                'app_token': self.config['feishu_async']['app_token']
            },
            'tables': {
                'content_table': {
                    'table_id': self.config['feishu_async']['content_table_id'],
                    'field_mapping': {
                        'title': '仿写标题',
                        'content': '仿写文案',
                        'digital_no': '数字人编号',
                        'voice_id': '声音ID',
                        'project_name': '项目名称',
                        'account': '关联账号',
                        'status': '状态',
                        'result ': '返回结果'
                    }
                },
                'account_table': {
                    'table_id': self.config['feishu_async']['account_table_id'],
                    'account_field': '账号',
                    'name_field': '名称'
                },
                'voice_table': {
                    'table_id': self.config['feishu_async']['voice_table_id'],
                    'account_field': '关联账号',
                    'voice_id_field': '音色ID'
                },
                'digital_human_table': {
                    'table_id': self.config['feishu_async']['digital_table_id'],
                    'account_field': '关联账号',
                    'digital_no_field': '数字人编号'
                }
            },
            'workflow_config': {
                'draft_folder_path': self.config['jianying']['draft_folder_path'],
                'coze_config': {
                    'token': self.config['coze']['bearer_token'],
                    'workflow_id': self.config['coze']['workflow_id']
                },
                'max_coze_concurrent': self.config['concurrent']['max_coze_concurrent'],
                'max_synthesis_workers': self.config['concurrent']['max_synthesis_workers'],
                'poll_interval': self.config['concurrent']['poll_interval']
            },
            'template_config': self.get_selected_feishu_template()
        }
        # 注入可选背景音乐
        bgm_path = (self.config.get('audio') or {}).get('bgm_path')
        if bgm_path:
            config['workflow_config']['background_music_path'] = bgm_path
        return config

    
    def build_filter_condition(self) -> Dict[str, Any]:
        """构建过滤条件"""
        status = self.status_filter_entry.get().strip()
        if not status:
            status = "视频草稿生成"
        
        return {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": "状态",
                    "operator": "is",
                    "value": [status]
                }
            ]
        }
    
    def get_include_ids(self) -> Optional[List[str]]:
        """获取包含的记录ID列表"""
        include_text = self.include_ids_entry.get().strip()
        if not include_text:
            return None
        
        return [id.strip() for id in include_text.split(',') if id.strip()]
    
    def get_exclude_ids(self) -> Optional[List[str]]:
        """获取排除的记录ID列表"""
        exclude_text = self.exclude_ids_entry.get().strip()
        if not exclude_text:
            return None
        
        return [id.strip() for id in exclude_text.split(',') if id.strip()]
    
    def update_async_progress(self, message: str):
        """更新异步处理进度"""
        self.async_progress_label['text'] = message
    
    def start_task_status_monitor(self):
        """启动任务状态实时监控"""
        if self.task_update_timer:
            self.root.after_cancel(self.task_update_timer)
        
        # 立即更新一次
        self.update_task_list()
        
        # 设置定时更新（每2秒更新一次）
        self.task_update_timer = self.root.after(2000, self.schedule_next_update)
    
    def schedule_next_update(self):
        """安排下一次更新"""
        if self.async_running and self.async_workflow and self.async_workflow.async_processor:
            self.update_task_list()
            # 继续安排下一次更新
            self.task_update_timer = self.root.after(2000, self.schedule_next_update)
        else:
            self.task_update_timer = None
    
    def stop_task_status_monitor(self):
        """停止任务状态监控"""
        if self.task_update_timer:
            self.root.after_cancel(self.task_update_timer)
            self.task_update_timer = None
    
    def clear_task_info_on_failure(self):
        """处理失败时清空任务信息"""
        # 清空任务列表（若存在）
        if self.async_task_tree:
            for item in self.async_task_tree.get_children():
                self.async_task_tree.delete(item)
        
        # 重置统计信息
        self.stats_label['text'] = "任务统计: 0/0 (0% 完成)"
        self.detailed_stats_label['text'] = "运行中: 0 | 失败: 0 | 成功: 0 | 待处理: 0"
        
        # 重置进度信息
        self.current_status_label['text'] = "状态: 处理失败"
        self.runtime_label['text'] = "运行时间: 00:00:00"
        
        # 设置进度条为红色并重置为0
        self.async_progress_bar.configure(style="Error.Horizontal.TProgressbar")
        self.async_progress_bar['value'] = 0
        
        # 清空飞书内容数据
        self.feishu_content_data = []
        self.feishu_content_text.delete(1.0, tk.END)
    
    def reset_progress_bar_style(self):
        """重置进度条样式为正常状态"""
        self.async_progress_bar.configure(style="Normal.Horizontal.TProgressbar")
    
    def update_task_list(self):
        """更新任务列表显示"""
        if not self.async_task_tree:
            # 已移除任务列表，直接退回并仅更新统计与进度
            if self.async_workflow and getattr(self.async_workflow, 'async_processor', None):
                tasks_data = self.async_workflow.async_processor.tasks
                self.update_task_statistics(tasks_data)
                self.update_detailed_progress(tasks_data)
            return
        if not self.async_workflow or not self.async_workflow.async_processor:
            return
        
        # 获取任务状态
        tasks_data = self.async_workflow.async_processor.tasks
        if not tasks_data:
            return
        
        # 清空任务列表（若存在）
        if self.async_task_tree:
            for item in self.async_task_tree.get_children():
                self.async_task_tree.delete(item)
        
        # 添加任务到列表
        for task_id, task in tasks_data.items():
            # AsyncCozeTask 是 dataclass，直接访问属性
            status = task.status.value if hasattr(task.status, 'value') else str(task.status)
            progress = self._calculate_task_progress(task)
            start_time = task.submit_time.strftime('%H:%M:%S') if task.submit_time else ''
            end_time = task.complete_time.strftime('%H:%M:%S') if task.complete_time else ''
            title = task.title or task_id
            
            # 计算耗时
            duration = ''
            if task.submit_time and task.complete_time:
                duration_seconds = (task.complete_time - task.submit_time).total_seconds()
                duration = f"{int(duration_seconds//60)}m{int(duration_seconds%60)}s"
            elif task.submit_time:
                duration_seconds = (datetime.now() - task.submit_time).total_seconds()
                duration = f"{int(duration_seconds//60)}m{int(duration_seconds%60)}s"
            
            # 重试次数
            retry_count = getattr(task, 'retry_count', 0)
            
            # 根据状态设置不同的颜色标识
            status_display = self._format_status_display(status, progress)
            
            self.async_task_tree.insert('', 'end', values=(
                task_id[:8] + '...',
                title[:20] + '...' if len(title) > 20 else title,
                status_display,
                f"{progress}%",
                start_time,
                end_time,
                duration,
                str(retry_count)
            ))
        
        # 自动滚动到最新任务
        self.auto_scroll_to_latest()
        
        # 更新统计信息
        self.update_task_statistics(tasks_data)
        
        # 更新详细进度信息
        self.update_detailed_progress(tasks_data)
    
    def _format_status_display(self, status: str, progress: int) -> str:
        """格式化状态显示"""
        status_icons = {
            'pending': '⏳ 待处理',
            'submitted': '📤 已提交',
            'running': '🔄 执行中',
            'completed': '✅ 已完成',
            'synthesizing': '🎬 合成中',
            'finished': '🎉 全部完成',
            'failed': '❌ 失败'
        }
        
        return status_icons.get(status, f'❓ {status}')
    
    def on_task_double_click(self, event):
        """任务双击事件处理"""
        if not self.async_task_tree:
            return
        selection = self.async_task_tree.selection()
        if not selection:
            return
        
        # 获取选中的任务信息
        item = self.async_task_tree.item(selection[0])
        values = item['values']
        
        task_id = values[0]
        title = values[1]
        status = values[2]
        progress = values[3]
        start_time = values[4]
        end_time = values[5]
        duration = values[6]
        retry_count = values[7]
        
        # 显示任务详情
        detail = f"任务详情:\n\n"
        detail += f"任务ID: {task_id}\n"
        detail += f"标题: {title}\n"
        detail += f"状态: {status}\n"
        detail += f"进度: {progress}\n"
        detail += f"开始时间: {start_time}\n"
        detail += f"完成时间: {end_time}\n"
        detail += f"耗时: {duration}\n"
        detail += f"重试次数: {retry_count}\n"
        
        # 如果有异步工作流，获取更详细的信息
        if self.async_workflow and self.async_workflow.async_processor:
            full_task_id = task_id.replace('...', '')
            for tid, task in self.async_workflow.async_processor.tasks.items():
                if tid.startswith(full_task_id):
                    detail += f"\n详细信息:\n"
                    detail += f"数字人编号: {getattr(task, 'digital_no', 'N/A')}\n"
                    detail += f"声音ID: {getattr(task, 'voice_id', 'N/A')}\n"
                    detail += f"项目名称: {getattr(task, 'project_name', 'N/A')}\n"
                    detail += f"记录ID: {getattr(task, 'record_id', 'N/A')}\n"
                    if hasattr(task, 'error_message') and task.error_message:
                        detail += f"错误信息: {task.error_message}\n"
                    if hasattr(task, 'video_path') and task.video_path:
                        detail += f"视频路径: {task.video_path}\n"
                    break
        
        # 弹出任务详情，并打开实时日志窗口
        try:
            self.open_task_log_viewer(task_id, title)
        except Exception:
            pass
        messagebox.showinfo("任务详情", detail)

    def open_task_log_viewer(self, short_task_id: str, title: str):
        """打开任务实时日志窗口（基于当前会话日志实时追踪）"""
        if not self.current_session_log_file or not os.path.exists(self.current_session_log_file):
            messagebox.showwarning("提示", "当前没有可用的会话日志。请先开始一次批量处理。")
            return

        win = tk.Toplevel(self.root)
        win.title(f"任务实时日志 - {title}")
        win.geometry("900x520")

        # 顶部操作栏
        toolbar = ttk.Frame(win)
        toolbar.pack(fill='x', padx=8, pady=6)

        open_sys_btn = ttk.Button(toolbar, text="打开系统终端查看", command=self.open_session_log_in_terminal)
        open_sys_btn.pack(side='right')

        info_lbl = ttk.Label(toolbar, text=f"会话日志: {os.path.basename(self.current_session_log_file)}  |  任务ID匹配: {short_task_id}")
        info_lbl.pack(side='left')

        # 文本区域
        text = scrolledtext.ScrolledText(win, wrap='word', height=28)
        text.pack(fill='both', expand=True, padx=8, pady=6)
        text.insert('end', f"[实时跟踪] {datetime.now().strftime('%H:%M:%S')} 开始追踪日志...\n")
        text.configure(state='disabled')

        # 追踪位置
        state = {"pos": 0}

        def tail_log():
            try:
                with open(self.current_session_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(state["pos"])
                    lines = f.readlines()
                    state["pos"] = f.tell()
                if lines:
                    # 仅显示包含任务短ID或通用关键信息的行
                    filtered = []
                    for line in lines:
                        if short_task_id.replace('...', '') in line or '任务' in line or 'ERROR' in line or 'INFO' in line or 'WARN' in line:
                            filtered.append(line)
                    if filtered:
                        text.configure(state='normal')
                        text.insert('end', ''.join(filtered))
                        text.see('end')
                        text.configure(state='disabled')
            except Exception:
                pass
            finally:
                # 继续轮询
                if win.winfo_exists():
                    win.after(800, tail_log)

        tail_log()

    def open_session_log_in_terminal(self):
        """在系统 PowerShell 中实时查看当前会话日志"""
        if not self.current_session_log_file or not os.path.exists(self.current_session_log_file):
            messagebox.showwarning("提示", "当前没有可用的会话日志。请先开始一次批量处理。")
            return
        try:
            log_path = os.path.abspath(self.current_session_log_file)
            # 使用 PowerShell 实时追踪日志
            cmd = [
                'powershell', '-NoExit', '-Command',
                f"Get-Content -Path '{log_path}' -Wait -Encoding UTF8"
            ]
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as e:
            messagebox.showerror("错误", f"打开系统终端失败: {e}")
    
    def auto_scroll_to_latest(self):
        """自动滚动到最新任务"""
        if not self.async_task_tree:
            return
        children = self.async_task_tree.get_children()
        if children:
            self.async_task_tree.see(children[-1])
            self.async_task_tree.selection_set(children[-1])
    
    def update_task_statistics(self, tasks_data):
        """更新任务统计信息"""
        if not tasks_data:
            self.stats_label['text'] = "任务统计: 0/0 (0% 完成)"
            self.detailed_stats_label['text'] = "运行中: 0 | 失败: 0 | 成功: 0"
            return
        
        total_tasks = len(tasks_data)
        completed_tasks = 0  # 成功
        failed_tasks = 0
        running_tasks = 0
        pending_tasks = 0
        
        for task in tasks_data.values():
            status = task.status.value if hasattr(task.status, 'value') else str(task.status)
            if status in ['finished', 'completed']:
                completed_tasks += 1
            elif status in ['failed']:
                failed_tasks += 1
            elif status in ['running', 'submitted', 'synthesizing']:
                running_tasks += 1
            else:
                pending_tasks += 1
        
        finished = completed_tasks + failed_tasks
        finished_pct = (finished / total_tasks * 100) if total_tasks > 0 else 0
        
        stats_text = f"任务统计: {finished}/{total_tasks} ({finished_pct:.1f}% 完成) | 成功率: {(completed_tasks/total_tasks*100 if total_tasks else 0):.1f}%"
        self.stats_label['text'] = stats_text
        
        detailed_text = f"运行中: {running_tasks} | 失败: {failed_tasks} | 成功: {completed_tasks} | 待处理: {pending_tasks}"
        self.detailed_stats_label['text'] = detailed_text
    
    def update_detailed_progress(self, tasks_data):
        """更新详细进度信息"""
        if not tasks_data:
            self.current_status_label['text'] = "状态: 待机"
            self.runtime_label['text'] = "运行时间: 00:00:00"
            self.async_progress_bar['value'] = 0
            return
        
        # 计算当前状态
        running_count = 0
        completed_count = 0
        failed_count = 0
        pending_count = 0
        
        for task in tasks_data.values():
            status = task.status.value if hasattr(task.status, 'value') else str(task.status)
            if status in ['running', 'submitted', 'synthesizing']:
                running_count += 1
            elif status in ['finished', 'completed']:
                completed_count += 1
            elif status in ['failed']:
                failed_count += 1
            else:
                pending_count += 1
        
        total_tasks = len(tasks_data)
        
        # 更新进度条
        if total_tasks > 0:
            progress_percentage = int((completed_count / total_tasks) * 100)
            self.async_progress_bar['value'] = progress_percentage
        else:
            self.async_progress_bar['value'] = 0
        
        # 更新当前状态
        if running_count > 0:
            self.current_status_label['text'] = f"状态: 处理中 ({running_count} 个任务运行中)"
        elif completed_count > 0 and pending_count == 0:
            self.current_status_label['text'] = "状态: 全部完成"
        elif failed_count > 0:
            self.current_status_label['text'] = f"状态: 部分失败 ({failed_count} 个失败)"
        else:
            self.current_status_label['text'] = "状态: 待机"
        
        # 计算运行时间
        if hasattr(self, 'start_time') and self.start_time:
            elapsed_time = datetime.now() - self.start_time
            hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            runtime_text = f"运行时间: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            self.runtime_label['text'] = runtime_text
        else:
            self.runtime_label['text'] = "运行时间: 00:00:00"
    
    def import_template_config(self):
        """导入模板配置文件（支持选择任意JSON文件）"""
        try:
            # 先弹窗让用户选择文件，默认定位到项目内模板
            default_path = os.path.join(PROJECT_ROOT, 'workflow')
            file_path = filedialog.askopenfilename(
                title="选择模板配置文件",
                initialdir=default_path,
                filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
            )
            # 若未选择，则回退到默认模板
            template_path = file_path or os.path.join(PROJECT_ROOT, 'workflow', 'feishu_config_template.json')
            
            if not os.path.exists(template_path):
                messagebox.showerror("错误", f"模板配置文件不存在: {template_path}")
                return
            
            # 读取模板配置
            with open(template_path, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
            
            # 清空当前配置
            self.clear_config_fields()
            
            # 导入飞书配置
            api_config = template_config.get('api_config', {})
            self.feishu_app_id_entry.insert(0, api_config.get('app_id', ''))
            self.feishu_app_secret_entry.insert(0, api_config.get('app_secret', ''))
            self.feishu_app_token_entry.insert(0, api_config.get('app_token', ''))
            
            # 导入表格配置
            tables_config = template_config.get('tables', {})
            content_table = tables_config.get('content_table', {})
            self.feishu_content_table_id_entry.insert(0, content_table.get('table_id', ''))
            
            account_table = tables_config.get('account_table', {})
            self.feishu_account_table_id_entry.insert(0, account_table.get('table_id', ''))
            
            voice_table = tables_config.get('voice_table', {})
            self.feishu_voice_table_id_entry.insert(0, voice_table.get('table_id', ''))
            
            digital_table = tables_config.get('digital_human_table', {})
            self.feishu_digital_table_id_entry.insert(0, digital_table.get('table_id', ''))
            
            # 导入工作流配置
            workflow_config = template_config.get('workflow_config', {})
            
            # Coze配置
            coze_config = workflow_config.get('coze_config', {})
            self.coze_token_entry.insert(0, coze_config.get('token', ''))
            self.coze_workflow_id_entry.insert(0, coze_config.get('workflow_id', ''))
            
            # 火山引擎配置
            self.volc_appid_entry.insert(0, workflow_config.get('volcengine_appid', ''))
            self.volc_token_entry.insert(0, workflow_config.get('volcengine_access_token', ''))
            
            # 豆包配置
            self.doubao_token_entry.insert(0, workflow_config.get('doubao_token', ''))
            
            # 剪映配置
            self.jianying_path_entry.insert(0, workflow_config.get('draft_folder_path', ''))
            
            # 并发配置
            self.max_coze_concurrent_entry.delete(0, tk.END)
            self.max_coze_concurrent_entry.insert(0, str(workflow_config.get('max_coze_concurrent', 16)))
            
            self.max_synthesis_workers_entry.delete(0, tk.END)
            self.max_synthesis_workers_entry.insert(0, str(workflow_config.get('max_synthesis_workers', 4)))
            
            self.poll_interval_entry.delete(0, tk.END)
            self.poll_interval_entry.insert(0, str(workflow_config.get('poll_interval', 30)))
            
            messagebox.showinfo("成功", "模板配置导入成功！")
            self.log_message("已导入模板配置文件")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入模板配置失败: {e}")
            self.log_message(f"导入模板配置失败: {e}")
    
    def clear_config(self):
        """清空所有配置"""
        if messagebox.askyesno("确认", "确定要清空所有配置吗？"):
            self.clear_config_fields()
            messagebox.showinfo("成功", "配置已清空")
            self.log_message("已清空所有配置")
    
    def clear_config_fields(self):
        """清空所有配置字段"""
        # 清空所有输入框
        self.coze_token_entry.delete(0, tk.END)
        self.coze_workflow_id_entry.delete(0, tk.END)
        self.feishu_app_id_entry.delete(0, tk.END)
        self.feishu_app_secret_entry.delete(0, tk.END)
        self.feishu_table_id_entry.delete(0, tk.END)
        self.volc_appid_entry.delete(0, tk.END)
        self.volc_token_entry.delete(0, tk.END)
        self.doubao_token_entry.delete(0, tk.END)
        self.jianying_path_entry.delete(0, tk.END)
        self.feishu_app_token_entry.delete(0, tk.END)
        self.feishu_content_table_id_entry.delete(0, tk.END)
        self.feishu_account_table_id_entry.delete(0, tk.END)
        self.feishu_voice_table_id_entry.delete(0, tk.END)
        self.feishu_digital_table_id_entry.delete(0, tk.END)
        
        # 重置并发配置为默认值
        self.max_coze_concurrent_entry.delete(0, tk.END)
        self.max_coze_concurrent_entry.insert(0, "16")
        self.max_synthesis_workers_entry.delete(0, tk.END)
        self.max_synthesis_workers_entry.insert(0, "4")
        self.poll_interval_entry.delete(0, tk.END)
        self.poll_interval_entry.insert(0, "30")
    
    def on_workflow_type_changed(self, event):
        """工作流类型改变事件处理"""
        workflow_type = self.schedule_workflow_type_combo.get()
        
        if workflow_type == '手动生成':
            # 显示手动生成的工作流
            workflow_names = [wf.get('name', '') for wf in self.workflows.values() if wf.get('type') == 'manual']
            self.schedule_workflow_combo['values'] = workflow_names
        elif workflow_type == '飞书异步批量':
            # 显示飞书异步批量工作流（使用固定名称）
            self.schedule_workflow_combo['values'] = ['飞书异步批量工作流']
            self.schedule_workflow_combo.set('飞书异步批量工作流')
        else:
            self.schedule_workflow_combo['values'] = []


class FeishuClient:
    """飞书客户端"""
    
    def __init__(self, app_id: str, app_secret: str, app_token: str = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
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
    
    def get_table_data(self, table_id: str, filter_condition: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """获取表格数据
        
        Args:
            table_id: 表格ID
            filter_condition: 过滤条件
        """
        if not table_id:
            raise ValueError("表格ID不能为空")
        
        access_token = self.get_access_token()
        
        # 如果有过滤条件，使用搜索API；否则使用普通获取API
        if filter_condition:
            url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/search"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "page_size": 100,
                "filter": filter_condition
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 0:
                data = result.get('data', {})
                records = data.get('items', [])
            else:
                raise ValueError(f"搜索记录失败: {result.get('msg')}")
        else:
            url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 0:
                data = result.get('data', {})
                records = data.get('items', [])
            else:
                raise ValueError(f"获取表格数据失败: {result.get('msg')}")
        
        # 转换bitable记录格式
        converted_records = []
        for record in records:
            fields = record.get('fields', {})
            converted_record = {
                'record_id': record.get('record_id', ''),
                **fields
            }
            converted_records.append(converted_record)
        
        return converted_records
    
    def build_filter_condition(self, status_filter: str, include_ids: str, exclude_ids: str) -> Optional[Dict]:
        """构建过滤条件
        
        Args:
            status_filter: 状态过滤条件
            include_ids: 包含的记录ID（逗号分隔）
            exclude_ids: 排除的记录ID（逗号分隔）
            
        Returns:
            过滤条件字典
        """
        filter_conditions = []
        
        # 状态过滤
        if status_filter.strip():
            filter_conditions.append({
                "field_name": "状态",
                "operator": "is",
                "value": [status_filter.strip()]
            })
        
        # 包含记录ID过滤
        if include_ids.strip():
            include_list = [id.strip() for id in include_ids.split(',') if id.strip()]
            if include_list:
                filter_conditions.append({
                    "field_name": "record_id",
                    "operator": "isOneOf",
                    "value": include_list
                })
        
        # 排除记录ID过滤
        if exclude_ids.strip():
            exclude_list = [id.strip() for id in exclude_ids.split(',') if id.strip()]
            if exclude_list:
                filter_conditions.append({
                    "field_name": "record_id",
                    "operator": "isNotOneOf",
                    "value": exclude_list
                })
        
        if filter_conditions:
            return {
                "conjunction": "and",
                "conditions": filter_conditions
            }
        
        return None


def main():
    """主函数"""
    root = tk.Tk()
    app = VideoGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()