import sys
import os
import threading
import ctypes

# 优先加载项目内 libs 目录的 customtkinter（避免依赖系统环境）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs"))

import customtkinter as ctk
from main import run_tasks, TASKS
import main as main_mod
from task_controller import TaskStopped
from utils import log
from text_redirector import TextRedirector

# ========== 主题 ==========
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C_BG       = "#0e1117"   # 窗口背景
C_PANEL    = "#151a23"   # 卡片背景
C_LIST     = "#1b2230"   # 列表/日志背景
C_ROW_H    = "#202940"   # 列表行悬停
C_BTN      = "#2a3245"   # 普通按钮
C_BTN_H    = "#3a4661"   # 普通按钮悬停
C_FG       = "#e6eaf2"   # 主文字
C_DIM      = "#7f8ba0"   # 次要文字
C_ACCENT   = "#3d7bff"   # 强调蓝
C_ACCENT_D = "#2f63d0"
C_GREEN    = "#1f9d55"   # 启动按钮
C_GREEN_D  = "#178044"
C_RED      = "#d64545"   # 退出按钮
C_RED_D    = "#b83a3a"
C_WARN     = "#f0b429"   # 运行中状态色

FONT = "Microsoft YaHei UI"
MONO = "Consolas"

DEFAULT_TASKS = ["enter", "skip", "close", "reward", "daily", "daily_free_50", "tower"]


def F(size, bold=False):
    return ctk.CTkFont(family=FONT, size=size, weight="bold" if bold else "normal")


class TaskList(ctk.CTkScrollableFrame):
    """深色任务列表：单行点击选中，双击触发回调"""
    def __init__(self, master, width=250, height=220, on_double_click=None, **kw):
        super().__init__(master, width=width, height=height,
                         fg_color=C_LIST, corner_radius=8, **kw)
        self._items = []
        self._selected = None
        self._rows = []
        self._on_double_click = on_double_click

    def items(self):
        return list(self._items)

    def size(self):
        return len(self._items)

    def selected_index(self):
        return self._selected

    def set_items(self, items, select=None):
        self._items = list(items)
        if select is not None and 0 <= select < len(self._items):
            self._selected = select
        elif self._selected is not None:
            self._selected = (len(self._items) - 1) if self._selected >= len(self._items) else self._selected
            if not self._items:
                self._selected = None
        self._render()

    def _select(self, idx):
        self._selected = idx
        self._render()

    def _render(self):
        for row in self._rows:
            row.destroy()
        self._rows = []
        for i, item in enumerate(self._items):
            is_sel = (i == self._selected)
            row = ctk.CTkLabel(self, text=item, anchor="w", height=28,
                               font=F(11), corner_radius=6, padx=8,
                               fg_color=C_ACCENT if is_sel else "transparent",
                               text_color="#ffffff" if is_sel else C_FG)
            row.pack(fill="x", padx=4, pady=1)
            row.bind("<Button-1>", lambda e, idx=i: self._select(idx))
            row.bind("<Double-Button-1>",
                     lambda e, idx=i: self._on_double_click(idx) if self._on_double_click else None)
            row.bind("<Enter>", lambda e, w=row, idx=i:
                     w.configure(fg_color=C_ACCENT if idx == self._selected else C_ROW_H))
            row.bind("<Leave>", lambda e, w=row, idx=i:
                     w.configure(fg_color=C_ACCENT if idx == self._selected else "transparent"))
            self._rows.append(row)


def start_gui():
    root = ctk.CTk()
    root.title("任务执行器")
    root.geometry("1360x820")
    root.configure(fg_color=C_BG)

    running = {"flag": False}
    paused = {"flag": False}
    restarting = {"flag": False}

    # 底部操作栏最先打包：窗口缩小时优先保住按钮不被挤掉
    bottom = ctk.CTkFrame(root, fg_color="transparent")
    bottom.pack(side="bottom", fill="x", padx=24, pady=(12, 18))

    # ========== 顶部标题 ==========
    header = ctk.CTkFrame(root, fg_color="transparent")
    header.pack(fill="x", padx=24, pady=(18, 12))
    ctk.CTkLabel(header, text="任务执行器", font=F(20, True),
                 text_color=C_FG).pack(side="left")
    ctk.CTkLabel(header, text="  auto_kurusuta · 游戏日常自动化", font=F(11),
                 text_color=C_DIM).pack(side="left", pady=(8, 0))

    # ========== 中部：左任务区 + 右日志 ==========
    body = ctk.CTkFrame(root, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24)
    body.grid_columnconfigure(0, weight=0)
    body.grid_columnconfigure(1, weight=1)
    body.grid_rowconfigure(0, weight=1)

    # ---- 左：任务选择 ----
    left = ctk.CTkFrame(body, fg_color="transparent")
    left.grid(row=0, column=0, sticky="ns")

    card1 = ctk.CTkFrame(left, fg_color=C_PANEL, corner_radius=10)
    card1.pack(fill="both", expand=True)
    ctk.CTkLabel(card1, text="可选任务", font=F(12, True),
                 text_color=C_FG).pack(anchor="w", padx=12, pady=(10, 6))
    all_list = TaskList(card1, on_double_click=lambda idx: add_task_idx(idx))
    all_list.pack(fill="both", expand=True, padx=8, pady=(0, 10))
    all_list.set_items(list(TASKS.keys()))

    btn_row = ctk.CTkFrame(left, fg_color="transparent")
    btn_row.pack(pady=8)

    card2 = ctk.CTkFrame(left, fg_color=C_PANEL, corner_radius=10)
    card2.pack(fill="both", expand=True)
    queue_label = ctk.CTkLabel(card2, text="执行队列", font=F(12, True),
                               text_color=C_FG)
    queue_label.pack(anchor="w", padx=12, pady=(10, 6))
    selected_list = TaskList(card2, on_double_click=lambda idx: remove_task_idx(idx))
    selected_list.pack(fill="both", expand=True, padx=8, pady=(0, 10))
    selected_list.set_items([t for t in DEFAULT_TASKS if t in TASKS])

    def refresh_queue_label():
        queue_label.configure(text=f"执行队列（{selected_list.size()}）")

    def add_task_idx(idx=None):
        if idx is None:
            idx = all_list.selected_index()
        if idx is None:
            return
        items = selected_list.items() + [all_list.items()[idx]]
        selected_list.set_items(items, select=len(items) - 1)
        refresh_queue_label()

    def add_task():
        add_task_idx()

    def remove_task_idx(idx=None):
        if idx is None:
            idx = selected_list.selected_index()
        if idx is None:
            return
        items = selected_list.items()
        items.pop(idx)
        new_sel = min(idx, len(items) - 1) if items else None
        selected_list.set_items(items, select=new_sel)
        refresh_queue_label()

    def remove_task():
        remove_task_idx()

    def move(delta):
        idx = selected_list.selected_index()
        if idx is None:
            return
        items = selected_list.items()
        j = idx + delta
        if 0 <= j < len(items):
            items[idx], items[j] = items[j], items[idx]
            selected_list.set_items(items, select=j)
            refresh_queue_label()

    def move_up():
        move(-1)

    def move_down():
        move(1)

    def clear_task():
        selected_list.set_items([])
        refresh_queue_label()

    def small_btn(text, cmd, fg, hover):
        return ctk.CTkButton(btn_row, text=text, command=cmd, width=60, height=28,
                             font=F(11), corner_radius=6,
                             fg_color=fg, hover_color=hover,
                             text_color_disabled="#8a93a6")

    small_btn("→ 添加", add_task, C_ACCENT, C_ACCENT_D).pack(side="left", padx=3)
    small_btn("← 移除", remove_task, C_BTN, C_BTN_H).pack(side="left", padx=3)
    small_btn("↑ 上移", move_up, C_BTN, C_BTN_H).pack(side="left", padx=3)
    small_btn("↓ 下移", move_down, C_BTN, C_BTN_H).pack(side="left", padx=3)
    small_btn("清空", clear_task, C_BTN, C_BTN_H).pack(side="left", padx=3)

    refresh_queue_label()

    # ---- 右：日志 ----
    log_card = ctk.CTkFrame(body, fg_color=C_PANEL, corner_radius=10)
    log_card.grid(row=0, column=1, sticky="nswe", padx=(12, 0))
    ctk.CTkLabel(log_card, text="运行日志", font=F(12, True),
                 text_color=C_FG).pack(anchor="w", padx=12, pady=(10, 6))
    log_area = ctk.CTkTextbox(
        log_card, wrap="word",
        font=ctk.CTkFont(family=MONO, size=12),
        fg_color=C_LIST, text_color="#c9d1d9", corner_radius=8,
    )
    log_area.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    sys.stdout = TextRedirector(log_area, "stdout")
    sys.stderr = TextRedirector(log_area, "stderr")
    try:
        log_area.tag_config("stdout", foreground="#c9d1d9")
        log_area.tag_config("stderr", foreground="#ff6b6b")
    except Exception:
        pass  # 旧版 customtkinter 无 tag_config，仅丢失错误红色显示

    # ========== 底部：状态栏 + 操作按钮（bottom 已在开头打包）==========
    # 状态栏只创建、暂不打包：等按钮打包完再排，窗口变窄时优先牺牲文字
    status_dot = ctk.CTkLabel(bottom, text="●", font=F(12), text_color=C_GREEN)
    status_text = ctk.CTkLabel(bottom, text="空闲", font=F(11), text_color=C_DIM)

    def set_running(is_running, task_names=None):
        running["flag"] = is_running
        if is_running:
            paused["flag"] = False
            status_dot.configure(text_color=C_WARN)
            status_text.configure(text=f"运行中：{'、'.join(task_names)}", text_color=C_FG)
            start_btn.configure(state="disabled", text="运行中…",
                                fg_color=C_BTN, hover_color=C_BTN)
            pause_btn.configure(state="normal", text="⏸ 暂停",
                                fg_color=C_BTN, hover_color=C_BTN_H)
            restart_btn.configure(state="normal",
                                  fg_color=C_ACCENT, hover_color=C_ACCENT_D)
        else:
            status_dot.configure(text_color=C_GREEN)
            status_text.configure(text="空闲", text_color=C_DIM)
            start_btn.configure(state="normal", text="▶ 启动任务",
                                fg_color=C_GREEN, hover_color=C_GREEN_D)
            pause_btn.configure(state="disabled", text="⏸ 暂停",
                                fg_color=C_BTN, hover_color=C_BTN)
            restart_btn.configure(state="disabled",
                                  fg_color=C_BTN, hover_color=C_BTN)

    def toggle_pause():
        ctrl = main_mod.current_controller
        if not ctrl or not running["flag"]:
            return
        if paused["flag"]:
            ctrl.resume()
            paused["flag"] = False
            pause_btn.configure(text="⏸ 暂停", fg_color=C_BTN, hover_color=C_BTN_H)
            status_dot.configure(text_color=C_WARN)
            status_text.configure(text="运行中…", text_color=C_FG)
        else:
            ctrl.pause()
            paused["flag"] = True
            pause_btn.configure(text="▶ 继续", fg_color=C_ACCENT, hover_color=C_ACCENT_D)
            status_dot.configure(text_color=C_DIM)
            status_text.configure(text="已暂停", text_color=C_DIM)

    def start_worker(tasks):
        def worker():
            try:
                run_tasks(tasks)
                log("任务线程结束")
            except TaskStopped:
                log("任务已停止")
            except Exception as e:
                log(f"任务线程异常退出: {e}")
            finally:
                def after_stop():
                    set_running(False)
                    if restarting["flag"]:
                        restarting["flag"] = False
                        log("正在重启任务…")
                        start_worker(tasks)
                root.after(0, after_stop)

        threading.Thread(target=worker, daemon=True).start()
        set_running(True, tasks)

    def start_selected_tasks():
        if running["flag"]:
            return
        tasks = selected_list.items()
        if not tasks:
            log("请至少选择一个任务")
            return
        log(f"开始执行任务: {tasks}")
        start_worker(tasks)

    def restart_tasks():
        if not running["flag"]:
            return
        ctrl = main_mod.current_controller
        if ctrl:
            restarting["flag"] = True
            log("收到重启请求，正在停止当前任务…")
            ctrl.request_stop()

    def main_btn(text, cmd, fg, hover, width=96):
        return ctk.CTkButton(bottom, text=text, command=cmd, width=width, height=36,
                             font=F(12), corner_radius=8,
                             fg_color=fg, hover_color=hover,
                             text_color_disabled="#8a93a6")

    main_btn("✖ 退出", root.quit, C_RED, C_RED_D).pack(side="right")
    restart_btn = main_btn("↻ 重启", restart_tasks, C_BTN, C_BTN_H)
    restart_btn.configure(state="disabled")
    restart_btn.pack(side="right", padx=(0, 12))
    pause_btn = main_btn("⏸ 暂停", toggle_pause, C_BTN, C_BTN_H)
    pause_btn.configure(state="disabled")
    pause_btn.pack(side="right", padx=(0, 12))
    start_btn = main_btn("▶ 启动任务", start_selected_tasks, C_GREEN, C_GREEN_D, width=130)
    start_btn.pack(side="right", padx=(0, 12))

    # 按钮占完空间后再排状态文字
    status_dot.pack(side="left")
    status_text.pack(side="left", padx=(6, 0))

    root.mainloop()


if __name__ == '__main__':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 高分屏不模糊
    except Exception:
        pass
    sys.stdout.reconfigure(encoding='utf-8')
    start_gui()
