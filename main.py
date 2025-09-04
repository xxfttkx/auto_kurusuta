# main.py
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
TASKS = {
    "enter": task.EnterGameTask,
    "skip": task.SkipTask,
    "close": task.CloseTask,
    "reward": task.RewardTask,
    "daily": task.DailyTask,
    "dailyreward": task.DailyRewardTask,
    "autobattle": task.AutoBattleTask,
}

def main(selected_tasks=None):
    target_window = find_target_window()
    while target_window is None:
        log("请先启动游戏")
        time.sleep(10)
        target_window = find_target_window()
        print("CUDA 是否可用：", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU 名称：", torch.cuda.get_device_name(0))
    # screenshot_window(target_window)
    controller = TaskController(target_window)
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
        # 没传参数，默认执行全部
        controller.add_task(task.EnterGameTask, "进入游戏")
        controller.add_task(task.SkipTask, "跳过奖励")
        controller.add_task(task.CloseTask, "关闭公告")
        controller.add_task(task.RewardTask, "领取奖励")
        controller.add_task(task.DailyTask, "日常")
        controller.add_task(task.DailyRewardTask, "领取日常奖励")

    
    # controller.add_task(task.AutoBattleTask, "自动战斗")
    controller.run_once()  # 先运行一次，初始化任务状态
    log("所有任务完成")

if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    sys.stdout.reconfigure(encoding='utf-8')
    # pyautogui.FAILSAFE = False
    args = sys.argv[1:]  # 读取命令行参数
    main(args)