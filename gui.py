import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import sys
from main import run_tasks, TASKS
from utils import log
from text_redirector import TextRedirector

def start_gui():
    root = tk.Tk()
    root.title("任务执行器 GUI")
    root.geometry("1400x800")
    root.configure(bg="#f0f4f7")

    # ========== 左边：任务选择 ==========
    left_frame = tk.Frame(root, bg="#f0f4f7")
    left_frame.grid(row=0, column=0, sticky="nswe", padx=20, pady=20)

    tk.Label(left_frame, text="可选任务", font=("Microsoft YaHei", 14, "bold"), bg="#f0f4f7").pack()
    all_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE, width=30, height=15)
    for t in TASKS.keys():
        all_listbox.insert(tk.END, t)
    all_listbox.pack(pady=10)

    btn_frame = tk.Frame(left_frame, bg="#f0f4f7")
    btn_frame.pack()

    selected_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE, width=30, height=15)
    selected_listbox.pack(pady=10)

    def add_task():
        sel = all_listbox.curselection()
        if sel:
            task = all_listbox.get(sel)
            selected_listbox.insert(tk.END, task)

    def remove_task():
        sel = selected_listbox.curselection()
        if sel:
            selected_listbox.delete(sel)

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

    tk.Button(btn_frame, text="→ 添加", command=add_task).grid(row=0, column=0, padx=5, pady=2)
    tk.Button(btn_frame, text="← 移除", command=remove_task).grid(row=1, column=0, padx=5, pady=2)
    tk.Button(btn_frame, text="↑ 上移", command=move_up).grid(row=2, column=0, padx=5, pady=2)
    tk.Button(btn_frame, text="↓ 下移", command=move_down).grid(row=3, column=0, padx=5, pady=2)

    # ========== 右边：日志输出 ==========
    right_frame = tk.Frame(root, bg="#ffffff")
    right_frame.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)

    tk.Label(right_frame, text="运行日志", font=("Microsoft YaHei", 14, "bold"), bg="#ffffff").pack(anchor="w", pady=10)
    log_area = scrolledtext.ScrolledText(
        right_frame, wrap=tk.WORD, width=100, height=40,
        font=("Consolas", 12), bg="#1e1e1e", fg="#dcdcdc"
    )
    log_area.pack(fill="both", expand=True)

    # 重定向 stdout / stderr
    sys.stdout = TextRedirector(log_area, "stdout")
    sys.stderr = TextRedirector(log_area, "stderr")
    log_area.tag_configure("stderr", foreground="red")
    log_area.tag_configure("stdout", foreground="white")

    # ========== 底部按钮 ==========
    bottom_frame = tk.Frame(root, bg="#f0f4f7")
    bottom_frame.grid(row=1, column=0, columnspan=2, pady=20)

    def start_selected_tasks():
        tasks = [selected_listbox.get(i) for i in range(selected_listbox.size())]
        if not tasks:
            messagebox.showwarning("提示", "请至少选择一个任务")
            return

        def worker():
            run_tasks(tasks)

        threading.Thread(target=worker, daemon=True).start()
        log(f"开始执行任务: {tasks}")

    tk.Button(
        bottom_frame, text="▶ 启动", font=("Microsoft YaHei", 14),
        width=15, height=2, bg="#4CAF50", fg="white", relief="flat",
        command=start_selected_tasks
    ).pack(side="left", padx=20)

    tk.Button(
        bottom_frame, text="✖ 退出", font=("Microsoft YaHei", 14),
        width=15, height=2, bg="#E53935", fg="white", relief="flat",
        command=root.quit
    ).pack(side="left", padx=20)

    # 窗口布局拉伸
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=0)
    root.grid_columnconfigure(1, weight=1)

    root.mainloop()

if __name__ == '__main__': 
    start_gui()
