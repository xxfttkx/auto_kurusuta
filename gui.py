import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import sys
import ctypes
from main import run_tasks, TASKS
import main as main_mod
from task_controller import TaskStopped
from utils import log
from text_redirector import TextRedirector

# ========== 深色主题配色 ==========
C_BG       = "#0e1117"   # 窗口背景
C_PANEL    = "#151a23"   # 卡片背景
C_LIST     = "#1b2230"   # 列表/日志背景
C_BORDER   = "#262f40"   # 边框
C_BTN      = "#2a3245"   # 普通按钮
C_BTN_H    = "#3a4661"   # 普通按钮悬停
C_FG       = "#e6eaf2"   # 主文字
C_DIM      = "#7f8ba0"   # 次要文字
C_ACCENT   = "#3d7bff"   # 强调蓝
C_ACCENT_D = "#2f63d0"   # 强调蓝悬停
C_GREEN    = "#1f9d55"   # 启动按钮
C_GREEN_D  = "#178044"
C_RED      = "#d64545"   # 退出按钮
C_RED_D    = "#b83a3a"
C_WARN     = "#f0b429"   # 运行中状态色

FONT = "Microsoft YaHei UI"

DEFAULT_TASKS = ["enter", "skip", "close", "reward", "daily", "daily_free_50", "tower"]


def make_button(parent, text, command, bg, hover_bg, font_size=10, padx=14, pady=6):
    """扁平风格按钮，带悬停变色；禁用时悬停不变色"""
    btn = tk.Button(parent, text=text, command=command, bg=bg, fg="white",
                    activebackground=hover_bg, activeforeground="white",
                    relief="flat", bd=0, cursor="hand2",
                    disabledforeground="#8a93a6",
                    font=(FONT, font_size), padx=padx, pady=pady)
    btn._bg, btn._hover = bg, hover_bg
    btn.bind("<Enter>", lambda e: btn.config(bg=btn._hover) if btn["state"] == "normal" else None)
    btn.bind("<Leave>", lambda e: btn.config(bg=btn._bg))
    return btn


def make_listbox(parent, width=26, height=12):
    """带 1px 边框和滚动条的深色列表"""
    frame = tk.Frame(parent, bg=C_BORDER, padx=1, pady=1)
    lb = tk.Listbox(frame, bg=C_LIST, fg=C_FG, width=width, height=height,
                    selectbackground=C_ACCENT, selectforeground="#ffffff",
                    relief="flat", bd=0, activestyle="none",
                    highlightthickness=0, exportselection=False,
                    font=(FONT, 10))
    sb = tk.Scrollbar(frame, command=lb.yview, width=10,
                      bg=C_BORDER, troughcolor=C_LIST, activebackground=C_ACCENT)
    lb.config(yscrollcommand=sb.set)
    lb.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return frame, lb


def start_gui():
    root = tk.Tk()
    root.title("任务执行器")
    root.geometry("1360x820")
    root.minsize(1080, 640)
    root.configure(bg=C_BG)

    running = {"flag": False}
    paused = {"flag": False}
    restarting = {"flag": False}

    # ========== 顶部标题 ==========
    header = tk.Frame(root, bg=C_BG)
    header.pack(fill="x", padx=24, pady=(18, 12))
    tk.Label(header, text="任务执行器", font=(FONT, 18, "bold"),
             bg=C_BG, fg=C_FG).pack(side="left")
    tk.Label(header, text="  auto_kurusuta · 游戏日常自动化", font=(FONT, 10),
             bg=C_BG, fg=C_DIM).pack(side="left", pady=(7, 0))

    # ========== 中部：左任务区 + 右日志 ==========
    body = tk.Frame(root, bg=C_BG)
    body.pack(fill="both", expand=True, padx=24)
    body.grid_columnconfigure(0, weight=0)
    body.grid_columnconfigure(1, weight=1)
    body.grid_rowconfigure(0, weight=1)

    # ---- 左：任务选择 ----
    left = tk.Frame(body, bg=C_BG)
    left.grid(row=0, column=0, sticky="ns")

    card1 = tk.Frame(left, bg=C_PANEL, padx=12, pady=10)
    card1.pack(fill="both", expand=True)
    tk.Label(card1, text="可选任务", font=(FONT, 11, "bold"),
             bg=C_PANEL, fg=C_FG).pack(anchor="w", pady=(0, 8))
    wrap1, all_listbox = make_listbox(card1)
    wrap1.pack(fill="both", expand=True)
    for t in TASKS:
        all_listbox.insert(tk.END, t)

    btn_row = tk.Frame(left, bg=C_BG)
    btn_row.pack(pady=8)

    card2 = tk.Frame(left, bg=C_PANEL, padx=12, pady=10)
    card2.pack(fill="both", expand=True)
    queue_label = tk.Label(card2, text="执行队列", font=(FONT, 11, "bold"),
                           bg=C_PANEL, fg=C_FG)
    queue_label.pack(anchor="w", pady=(0, 8))
    wrap2, selected_listbox = make_listbox(card2)
    wrap2.pack(fill="both", expand=True)
    for t in DEFAULT_TASKS:
        if t in TASKS:
            selected_listbox.insert(tk.END, t)

    def refresh_queue_label():
        queue_label.config(text=f"执行队列（{selected_listbox.size()}）")

    def add_task():
        sel = all_listbox.curselection()
        if sel:
            selected_listbox.insert(tk.END, all_listbox.get(sel))
            refresh_queue_label()

    def remove_task():
        sel = selected_listbox.curselection()
        if sel:
            selected_listbox.delete(sel)
            refresh_queue_label()

    def move_up():
        sel = selected_listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            task = selected_listbox.get(idx)
            selected_listbox.delete(idx)
            selected_listbox.insert(idx - 1, task)
            selected_listbox.select_set(idx - 1)

    def move_down():
        sel = selected_listbox.curselection()
        if sel and sel[0] < selected_listbox.size() - 1:
            idx = sel[0]
            task = selected_listbox.get(idx)
            selected_listbox.delete(idx)
            selected_listbox.insert(idx + 1, task)
            selected_listbox.select_set(idx + 1)

    def clear_task():
        selected_listbox.delete(0, tk.END)
        refresh_queue_label()

    make_button(btn_row, "→ 添加", add_task, C_ACCENT, C_ACCENT_D, font_size=9, padx=10, pady=4).pack(side="left", padx=3)
    make_button(btn_row, "← 移除", remove_task, C_BTN, C_BTN_H, font_size=9, padx=10, pady=4).pack(side="left", padx=3)
    make_button(btn_row, "↑ 上移", move_up, C_BTN, C_BTN_H, font_size=9, padx=10, pady=4).pack(side="left", padx=3)
    make_button(btn_row, "↓ 下移", move_down, C_BTN, C_BTN_H, font_size=9, padx=10, pady=4).pack(side="left", padx=3)
    make_button(btn_row, "清空", clear_task, C_BTN, C_BTN_H, font_size=9, padx=10, pady=4).pack(side="left", padx=3)

    # 双击快捷操作
    all_listbox.bind("<Double-Button-1>", lambda e: add_task())
    selected_listbox.bind("<Double-Button-1>", lambda e: remove_task())

    refresh_queue_label()

    # ---- 右：日志 ----
    log_card = tk.Frame(body, bg=C_PANEL, padx=12, pady=10)
    log_card.grid(row=0, column=1, sticky="nswe", padx=(12, 0))
    tk.Label(log_card, text="运行日志", font=(FONT, 11, "bold"),
             bg=C_PANEL, fg=C_FG).pack(anchor="w", pady=(0, 8))
    log_area = scrolledtext.ScrolledText(
        log_card, wrap="word", relief="flat", bd=0,
        font=("Consolas", 11), bg=C_LIST, fg="#c9d1d9",
        insertbackground=C_FG, selectbackground=C_ACCENT,
        selectforeground="#ffffff",
    )
    log_area.pack(fill="both", expand=True)

    sys.stdout = TextRedirector(log_area, "stdout")
    sys.stderr = TextRedirector(log_area, "stderr")
    log_area.tag_configure("stdout", foreground="#c9d1d9")
    log_area.tag_configure("stderr", foreground="#ff6b6b")

    # ========== 底部：状态栏 + 操作按钮 ==========
    bottom = tk.Frame(root, bg=C_BG)
    bottom.pack(fill="x", padx=24, pady=(12, 18))

    status_dot = tk.Label(bottom, text="●", font=(FONT, 10), bg=C_BG, fg=C_GREEN)
    status_dot.pack(side="left")
    status_text = tk.Label(bottom, text="空闲", font=(FONT, 10), bg=C_BG, fg=C_DIM)
    status_text.pack(side="left", padx=(6, 0))

    def set_running(is_running, task_names=None):
        running["flag"] = is_running
        if is_running:
            paused["flag"] = False
            status_dot.config(fg=C_WARN)
            status_text.config(text=f"运行中：{'、'.join(task_names)}", fg=C_FG)
            start_btn._bg = C_BTN
            start_btn.config(state="disabled", text="运行中…", bg=C_BTN, cursor="arrow")
            pause_btn._bg = C_BTN
            pause_btn.config(state="normal", text="⏸ 暂停", bg=C_BTN, cursor="hand2")
            restart_btn._bg = C_ACCENT
            restart_btn.config(state="normal", bg=C_ACCENT, cursor="hand2")
        else:
            status_dot.config(fg=C_GREEN)
            status_text.config(text="空闲", fg=C_DIM)
            start_btn._bg = C_GREEN
            start_btn.config(state="normal", text="▶ 启动任务", bg=C_GREEN, cursor="hand2")
            pause_btn._bg = C_BTN
            pause_btn.config(state="disabled", text="⏸ 暂停", bg=C_BTN, cursor="arrow")
            restart_btn._bg = C_BTN
            restart_btn.config(state="disabled", bg=C_BTN, cursor="arrow")

    def toggle_pause():
        ctrl = main_mod.current_controller
        if not ctrl or not running["flag"]:
            return
        if paused["flag"]:
            ctrl.resume()
            paused["flag"] = False
            pause_btn._bg = C_BTN
            pause_btn.config(text="⏸ 暂停", bg=C_BTN)
            status_dot.config(fg=C_WARN)
            status_text.config(text="运行中…", fg=C_FG)
        else:
            ctrl.pause()
            paused["flag"] = True
            pause_btn._bg = C_ACCENT
            pause_btn.config(text="▶ 继续", bg=C_ACCENT)
            status_dot.config(fg=C_DIM)
            status_text.config(text="已暂停", fg=C_DIM)

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
        tasks = [selected_listbox.get(i) for i in range(selected_listbox.size())]
        if not tasks:
            messagebox.showwarning("提示", "请至少选择一个任务")
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

    make_button(bottom, "✖ 退出", root.quit, C_RED, C_RED_D,
                font_size=11, padx=24, pady=8).pack(side="right")
    restart_btn = make_button(bottom, "↻ 重启", restart_tasks, C_ACCENT, C_ACCENT_D,
                              font_size=11, padx=20, pady=8)
    restart_btn._bg = C_BTN
    restart_btn.config(state="disabled", bg=C_BTN)
    restart_btn.pack(side="right", padx=(0, 12))
    pause_btn = make_button(bottom, "⏸ 暂停", toggle_pause, C_BTN, C_BTN_H,
                            font_size=11, padx=20, pady=8)
    pause_btn.config(state="disabled")
    pause_btn.pack(side="right", padx=(0, 12))
    start_btn = make_button(bottom, "▶ 启动任务", start_selected_tasks, C_GREEN, C_GREEN_D,
                            font_size=11, padx=28, pady=8)
    start_btn.pack(side="right", padx=(0, 12))

    root.mainloop()


if __name__ == '__main__':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 高分屏不模糊
    except Exception:
        pass
    sys.stdout.reconfigure(encoding='utf-8')
    start_gui()
