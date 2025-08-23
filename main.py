# main.py
import ctypes
import time
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

class TaskController:
    def __init__(self, target_window):
        self.target_window = target_window
        self.tasks = []
        self.current_task_index = 0

    def add_task(self, task_class, name):
        """注册任务，保持顺序"""
        self.tasks.append(task_class(name, self))

    def run_once(self):
        """每帧只运行当前任务"""
        if self.current_task_index >= len(self.tasks):
            return  # 全部任务完成

        current_task = self.tasks[self.current_task_index]
        finished = current_task.check_and_run()

        if finished:  # 返回 True 表示任务完成
            self.current_task_index += 1

    def click(self, x, y):
        click_window(self.target_window, x, y)

    def activate_target_window(self):
        """激活目标窗口"""
        try:
            self.target_window.activate()
        except Exception as e:
            log(f"激活窗口失败: {e}")

    def exit_program(self):
        log("检测到 / 键，退出程序")
        self.stop_all()
        os._exit(0)



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
    # controller.add_task(task.EnterGameTask, "进入游戏")
    # controller.add_task(task.SkipTask, "跳过奖励")
    # controller.add_task(task.CloseTask, "关闭公告")
    # controller.add_task(task.RewardTask, "领取奖励")
    # controller.add_task(task.DailyTask, "日常")
    controller.add_task(task.DailyRewardTask, "领取日常奖励")
    controller.run_once()  # 先运行一次，初始化任务状态
    log("所有任务完成")

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()