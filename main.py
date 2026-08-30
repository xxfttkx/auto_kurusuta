# main.py
import argparse
import ctypes
import time
from task_controller import TaskController
import torch
import game_logic
import sys
import keyboard
from utils import *
import asyncio
import threading
import task


# 可用任务映射表
current_controller = None  # 当前运行中的控制器，供 GUI 暂停/重启使用
TASKS = {
    "enter": task.EnterGameTask,
    "skip": task.SkipTask,
    "close": task.CloseTask,
    "reward": task.RewardTask,
    "daily": task.DailyTask,
    "daily_reward": task.DailyRewardTask,
    "receive_present": task.ReceivePresentTask,
    "auto_battle": task.AutoBattleTask,
    "tower": task.TowerTask,
    "battle_task": task.BattleTask,
    "daily_free_50": task.DailyFree50Task,
}

# 默认任务队列（唯一数据源，GUI 的预填队列也来自这里）
DEFAULT_TASKS = ["enter", "skip", "close", "reward", "daily", "daily_free_50", "tower"]

def main():
    parser = argparse.ArgumentParser(description="任务执行器")
    parser.add_argument("tasks", nargs="*", help="要执行的任务（留空则执行全部）")
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="列出所有可用任务"
    )
    args = parser.parse_args()
    if args.list:
        print("可用任务:")
        for key in TASKS.keys():
            print(f"  {key}")
        sys.exit(0)
    run_tasks(args.tasks)

def run_tasks(selected_tasks=None):
    log("CUDA 是否可用：", torch.cuda.is_available())
    if torch.cuda.is_available():
        log("GPU 名称：", torch.cuda.get_device_name(0))
    global current_controller
    target_window = find_target_window()
    while target_window is None:
        log("请先启动游戏")
        time.sleep(10)
        target_window = find_target_window()
        
    # screenshot_window(target_window)
    controller = TaskController(target_window)
    current_controller = controller
    keyboard.add_hotkey('/', controller.exit_program)

        # 根据参数添加任务
    if selected_tasks:
        for name in selected_tasks:
            task_cls = TASKS.get(name.lower())
            if task_cls:
                controller.add_task(task_cls, name)
            else:
                log(f"未知任务: {name}")
    else:
        # 没传参数，默认执行 DEFAULT_TASKS
        for name in DEFAULT_TASKS:
            controller.add_task(TASKS[name], name)
    controller.run_once()

if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    sys.stdout.reconfigure(encoding='utf-8')
    # pyautogui.FAILSAFE = False
    main()