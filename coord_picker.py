# coord_picker.py — 游戏坐标取点工具
# 用法：python coord_picker.py
# 把鼠标悬停到游戏内目标位置，按 F8 收集该点的 1280x720 逻辑坐标，
# 可直接复制成 self.controller.click(x, y) 或整组坐标列表。
import tkinter as tk
import ctypes
import sys

import pyautogui
import pygetwindow as gw
import win32gui
import keyboard

BASE_W, BASE_H = 1280, 720
CAPTURE_HOTKEY = "f8"
GAME_TITLE = "twinkle_starknightsX"

# 与 gui.py 一致的深色配色
C_BG       = "#151a23"
C_LIST     = "#1b2230"
C_BORDER   = "#262f40"
C_BTN      = "#2a3245"
C_BTN_H    = "#3a4661"
C_FG       = "#e6eaf2"
C_DIM      = "#7f8ba0"
C_ACCENT   = "#3d7bff"
C_ACCENT_D = "#2f63d0"
C_GREEN    = "#1f9d55"
C_GREEN_D  = "#178044"
FONT = "Microsoft YaHei UI"
MONO = "Consolas"


def make_button(parent, text, command, bg, hover_bg, font_size=10, padx=12, pady=5):
    btn = tk.Button(parent, text=text, command=command, bg=bg, fg="white",
                    activebackground=hover_bg, activeforeground="white",
                    relief="flat", bd=0, cursor="hand2", disabledforeground="#8a93a6",
                    font=(FONT, font_size), padx=padx, pady=pady)
    btn._bg, btn._hover = bg, hover_bg
    btn.bind("<Enter>", lambda e: btn.config(bg=btn._hover) if btn["state"] == "normal" else None)
    btn.bind("<Leave>", lambda e: btn.config(bg=btn._bg))
    return btn


class CoordPicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("取点工具")
        self.root.attributes("-topmost", True)
        self.root.configure(bg=C_BG)
        self.root.resizable(False, False)
        self.hwnd = None
        self.points = []
        self._build_ui()
        keyboard.add_hotkey(CAPTURE_HOTKEY, self._hotkey_capture)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll()

    # ---------- UI ----------
    def _build_ui(self):
        tk.Label(self.root, text="取点工具", font=(FONT, 13, "bold"),
                 bg=C_BG, fg=C_FG).pack(anchor="w", padx=14, pady=(12, 0))
        tk.Label(self.root, text=f"悬停游戏内目标位置，按 {CAPTURE_HOTKEY.upper()} 收集坐标",
                 font=(FONT, 9), bg=C_BG, fg=C_DIM).pack(anchor="w", padx=14)

        self.coord_label = tk.Label(self.root, text="( ---, --- )",
                                    font=(MONO, 20, "bold"), bg=C_BG, fg=C_DIM)
        self.coord_label.pack(pady=(6, 0))

        self.win_label = tk.Label(self.root, text="未找到游戏窗口，启动游戏后自动连接",
                                  font=(FONT, 9), bg=C_BG, fg=C_DIM)
        self.win_label.pack(pady=(0, 8))

        frame = tk.Frame(self.root, bg=C_BORDER, padx=1, pady=1)
        frame.pack(fill="both", expand=True, padx=14)
        self.listbox = tk.Listbox(frame, bg=C_LIST, fg=C_FG, width=30, height=8,
                                  selectbackground=C_ACCENT, selectforeground="#ffffff",
                                  relief="flat", bd=0, activestyle="none",
                                  highlightthickness=0, exportselection=False,
                                  font=(MONO, 10))
        sb = tk.Scrollbar(frame, command=self.listbox.yview, width=10,
                          bg=C_BORDER, troughcolor=C_LIST, activebackground=C_ACCENT)
        self.listbox.config(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.listbox.bind("<Double-Button-1>", lambda e: self._remove_selected())

        btn_row = tk.Frame(self.root, bg=C_BG)
        btn_row.pack(pady=10)
        make_button(btn_row, "复制代码", self._copy_selected, C_ACCENT, C_ACCENT_D).pack(side="left", padx=3)
        make_button(btn_row, "复制全部", self._copy_all, C_GREEN, C_GREEN_D).pack(side="left", padx=3)
        make_button(btn_row, "删除", self._remove_selected, C_BTN, C_BTN_H).pack(side="left", padx=3)
        make_button(btn_row, "清空", self._clear, C_BTN, C_BTN_H).pack(side="left", padx=3)

        self.hint_label = tk.Label(self.root, text="", font=(FONT, 9),
                                   bg=C_BG, fg=C_DIM, wraplength=280, justify="left")
        self.hint_label.pack(padx=14, pady=(0, 12))

    # ---------- 坐标换算：屏幕 → 游戏客户区 → 1280x720 逻辑坐标 ----------
    def _get_hwnd(self):
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            return self.hwnd
        for w in gw.getAllWindows():
            if w.title == GAME_TITLE:
                self.hwnd = w._hWnd
                self.win_label.config(text=f"已连接：{GAME_TITLE}", fg=C_GREEN)
                return self.hwnd
        self.hwnd = None
        self.win_label.config(text="未找到游戏窗口，启动游戏后自动连接", fg=C_DIM)
        return None

    def _to_logical(self):
        hwnd = self._get_hwnd()
        if not hwnd:
            return None
        sx, sy = pyautogui.position()
        cx, cy = win32gui.ScreenToClient(hwnd, (sx, sy))
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        w, h = right - left, bottom - top
        if w <= 0 or h <= 0:
            return None
        inside = 0 <= cx <= w and 0 <= cy <= h
        return round(cx * BASE_W / w), round(cy * BASE_H / h), inside

    # ---------- 实时刷新 ----------
    def _poll(self):
        result = self._to_logical()
        if result:
            lx, ly, inside = result
            self.coord_label.config(text=f"( {lx}, {ly} )",
                                    fg=C_FG if inside else C_DIM)
        else:
            self.coord_label.config(text="( ---, --- )", fg=C_DIM)
        self.root.after(100, self._poll)

    # ---------- 取点 ----------
    def _hotkey_capture(self):
        # 热键回调在键盘库线程执行，转交 Tk 主线程处理
        self.root.after(0, self._capture)

    def _capture(self):
        result = self._to_logical()
        if not result:
            self._set_hint("未找到游戏窗口，无法取点")
            return
        lx, ly, inside = result
        self.points.append((lx, ly))
        self.listbox.insert(tk.END, f"{len(self.points) - 1}: ({lx}, {ly})")
        self.listbox.see(tk.END)
        warn = "" if inside else "  ⚠ 当前鼠标不在游戏窗口内"
        self._set_hint(f"已收集 ({lx}, {ly}){warn}")

    # ---------- 列表操作 ----------
    def _set_hint(self, text):
        self.hint_label.config(text=text)

    def _copy(self, text, hint):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._set_hint(hint)

    def _copy_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            self._set_hint("请先在列表中选中一个点")
            return
        x, y = self.points[sel[0]]
        self._copy(f"self.controller.click({x}, {y})",
                   f"已复制: self.controller.click({x}, {y})")

    def _copy_all(self):
        if not self.points:
            self._set_hint("还没有收集任何点")
            return
        pts = "[" + ", ".join(f"({x}, {y})" for x, y in self.points) + "]"
        self._copy(pts, f"已复制 {len(self.points)} 个点: {pts}")

    def _remove_selected(self):
        sel = self.listbox.curselection()
        if sel:
            self.points.pop(sel[0])
            self._refresh_list()
            self._set_hint("已删除")

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for i, (x, y) in enumerate(self.points):
            self.listbox.insert(tk.END, f"{i}: ({x}, {y})")

    def _clear(self):
        self.points.clear()
        self.listbox.delete(0, tk.END)
        self._set_hint("已清空")

    # ---------- 生命周期 ----------
    def _on_close(self):
        keyboard.unhook_all()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    sys.stdout.reconfigure(encoding="utf-8")
    CoordPicker().run()
