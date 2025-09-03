import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from workflow.component.flow_python_implementation import VideoEditingWorkflow  # type: ignore


def get_default_draft_folder() -> str:
    # Jianying (CapCut) default draft folder on Windows
    user_profile = os.environ.get('USERPROFILE') or os.path.expanduser('~')
    default_path = os.path.join(
        user_profile,
        'AppData', 'Local', 'JianyingPro', 'User Data', 'Projects', 'com.lveditor.draft'
    )
    return default_path


class WorkflowGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('音频转录智能字幕工作流 - GUI')
        self.root.geometry('780x520')

        pad_x = 8
        pad_y = 6

        row = 0

        # Draft folder
        tk.Label(root, text='剪映草稿目录:').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.draft_folder_var = tk.StringVar(value=get_default_draft_folder())
        tk.Entry(root, textvariable=self.draft_folder_var, width=80).grid(row=row, column=1, sticky='w', padx=pad_x)
        tk.Button(root, text='选择', command=self._choose_draft_folder).grid(row=row, column=2, padx=pad_x)
        row += 1

        # Project name
        tk.Label(root, text='项目名称:').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.project_name_var = tk.StringVar(value='audio_transcription_demo')
        tk.Entry(root, textvariable=self.project_name_var, width=40).grid(row=row, column=1, sticky='w', padx=pad_x)
        row += 1

        # Audio URL/file
        tk.Label(root, text='音频URL或本地路径:').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.audio_url_var = tk.StringVar()
        tk.Entry(root, textvariable=self.audio_url_var, width=80).grid(row=row, column=1, sticky='w', padx=pad_x)
        tk.Button(root, text='选择文件', command=self._choose_audio_file).grid(row=row, column=2, padx=pad_x)
        row += 1

        # Digital human (optional)
        tk.Label(root, text='数字人视频URL(可选):').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.digital_url_var = tk.StringVar()
        tk.Entry(root, textvariable=self.digital_url_var, width=80).grid(row=row, column=1, sticky='w', padx=pad_x)
        row += 1

        # Title
        tk.Label(root, text='标题(可选):').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.title_var = tk.StringVar()
        tk.Entry(root, textvariable=self.title_var, width=80).grid(row=row, column=1, sticky='w', padx=pad_x)
        row += 1

        # Background music
        tk.Label(root, text='背景音乐(可选):').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.bgm_var = tk.StringVar()
        tk.Entry(root, textvariable=self.bgm_var, width=80).grid(row=row, column=1, sticky='w', padx=pad_x)
        tk.Button(root, text='选择文件', command=self._choose_bgm_file).grid(row=row, column=2, padx=pad_x)
        row += 1

        # Volcengine
        tk.Label(root, text='火山引擎 AppID:').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.appid_var = tk.StringVar()
        tk.Entry(root, textvariable=self.appid_var, width=40).grid(row=row, column=1, sticky='w', padx=pad_x)
        row += 1

        tk.Label(root, text='火山引擎 AccessToken:').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.token_var = tk.StringVar()
        tk.Entry(root, textvariable=self.token_var, width=80, show='*').grid(row=row, column=1, sticky='w', padx=pad_x)
        row += 1

        # Doubao
        tk.Label(root, text='豆包 Token(可选):').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.doubao_token_var = tk.StringVar()
        tk.Entry(root, textvariable=self.doubao_token_var, width=80).grid(row=row, column=1, sticky='w', padx=pad_x)
        row += 1

        tk.Label(root, text='豆包模型(可选):').grid(row=row, column=0, sticky='e', padx=pad_x, pady=pad_y)
        self.doubao_model_var = tk.StringVar(value='doubao-1-5-pro-32k-250115')
        tk.Entry(root, textvariable=self.doubao_model_var, width=60).grid(row=row, column=1, sticky='w', padx=pad_x)
        row += 1

        # Run button
        self.run_btn = tk.Button(root, text='运行工作流', width=20, command=self._run_workflow)
        self.run_btn.grid(row=row, column=1, pady=16)

        # Log box
        row += 1
        tk.Label(root, text='日志:').grid(row=row, column=0, sticky='ne', padx=pad_x, pady=pad_y)
        self.log_text = tk.Text(root, height=10, width=100)
        self.log_text.grid(row=row, column=1, columnspan=2, sticky='w', padx=pad_x)

    def _choose_draft_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.draft_folder_var.set(path)

    def _choose_audio_file(self) -> None:
        path = filedialog.askopenfilename(title='选择音频文件', filetypes=[('Audio', '*.mp3 *.wav *.m4a *.aac *.flac'), ('All', '*.*')])
        if path:
            self.audio_url_var.set(path)

    def _choose_bgm_file(self) -> None:
        path = filedialog.askopenfilename(title='选择背景音乐', filetypes=[('Audio', '*.mp3 *.wav'), ('All', '*.*')])
        if path:
            self.bgm_var.set(path)

    def _append_log(self, text: str) -> None:
        self.log_text.insert(tk.END, text + '\n')
        self.log_text.see(tk.END)

    def _run_workflow(self) -> None:
        draft_folder = self.draft_folder_var.get().strip()
        project_name = self.project_name_var.get().strip() or 'audio_transcription_demo'
        audio_url = self.audio_url_var.get().strip()
        digital_url = self.digital_url_var.get().strip()
        title = self.title_var.get().strip()
        bgm_path = self.bgm_var.get().strip()
        appid = self.appid_var.get().strip()
        token = self.token_var.get().strip()
        doubao_token = self.doubao_token_var.get().strip()
        doubao_model = self.doubao_model_var.get().strip()

        if not draft_folder:
            messagebox.showerror('错误', '请先选择剪映草稿目录')
            return
        if not audio_url:
            messagebox.showerror('错误', '请填写音频URL或选择本地音频文件')
            return
        if not appid or not token:
            messagebox.showerror('错误', '请填写火山引擎 AppID 与 AccessToken')
            return

        def _worker():
            try:
                self.run_btn.config(state=tk.DISABLED)
                self._append_log('开始运行工作流...')
                wf = VideoEditingWorkflow(draft_folder, project_name)
                inputs = {
                    'digital_video_url': digital_url or None,
                    'audio_url': audio_url,
                    'title': title or None,
                    'volcengine_appid': appid,
                    'volcengine_access_token': token,
                    'doubao_token': doubao_token or None,
                    'doubao_model': doubao_model or None,
                    'background_music_path': (bgm_path if os.path.exists(bgm_path) else None),
                    'background_music_volume': 0.25,
                }
                save_path = wf.process_workflow(inputs)
                self._append_log(f'完成，草稿已保存：{save_path}')
                messagebox.showinfo('完成', f'剪映项目已保存到：\n{save_path}')
            except Exception as e:
                self._append_log(f'运行失败：{e}')
                messagebox.showerror('失败', f'工作流执行失败：\n{e}')
            finally:
                self.run_btn.config(state=tk.NORMAL)

        threading.Thread(target=_worker, daemon=True).start()


def main() -> None:
    root = tk.Tk()
    app = WorkflowGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()


