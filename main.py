# main.py
import ctypes
import time

from task_controller import TaskController
ctypes.windll.shcore.SetProcessDpiAwareness(2) 
import torch
import game_logic
import sys
sys.stdout.reconfigure(encoding='utf-8')
import keyboard
from utils import *
import asyncio
import threading
import task

def main():
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
    sys.stdout.reconfigure(encoding='utf-8')
    pyautogui.FAILSAFE = False
    main()