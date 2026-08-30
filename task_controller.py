import os
import threading
import time

from utils import *

# 保存原始 sleep，避免控制器重建时重复包装
_ORIGINAL_SLEEP = time.sleep


class TaskStopped(Exception):
    """用户请求停止任务时抛出"""
    pass


class TaskController:
    def __init__(self, target_window):
        self.target_window = target_window
        self.tasks = []
        self.current_task_index = 0
        self.width, self.height = self.get_default_size()
        self.is_testing = False  # 是否为测试模式
        # 暂停/停止控制：pause_event 置位 = 运行，清除 = 暂停
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.stop_event = threading.Event()
        # 接管 time.sleep：任务里所有 sleep 都可暂停 / 打断
        time.sleep = self._pausable_sleep

    def _pausable_sleep(self, seconds):
        """可暂停的 sleep：暂停时阻塞等待恢复，停止时抛出 TaskStopped"""
        if self.stop_event.is_set():
            raise TaskStopped()
        deadline = time.time() + seconds
        while True:
            self.pause_event.wait()  # 暂停时在此阻塞
            if self.stop_event.is_set():
                raise TaskStopped()
            remaining = deadline - time.time()
            if remaining <= 0:
                return
            _ORIGINAL_SLEEP(min(0.2, remaining))

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

    def request_stop(self):
        self.stop_event.set()
        self.pause_event.set()  # 唤醒暂停中的线程以便退出

    def get_default_size(self):
        return (1280, 720)

    def get_point(self, x_ratio, y_ratio):
        """根据窗口大小和比例获取坐标"""
        x = int(self.width * x_ratio)
        y = int(self.height * y_ratio)
        return x,y

    def add_task(self, task_class, name):
        """注册任务，保持顺序"""
        self.tasks.append(task_class(name, self))

    def run_once(self):
        """依次运行所有任务"""
        while True:
            if self.current_task_index >= len(self.tasks):
                log("所有任务完成")
                return
            self.pause_event.wait()  # 任务间隙也响应暂停
            if self.stop_event.is_set():
                raise TaskStopped()
            current_task = self.tasks[self.current_task_index]
            finished = current_task.check_and_run()
            time.sleep(1)
            if finished:  # 返回 True 表示任务完成
                self.current_task_index += 1

    def click(self, x, y):
        """1280*720 的逻辑坐标，自动缩放到窗口实际分辨率"""
        w, h = get_client_size(self.target_window)
        real_x = int(x * w / self.width)
        real_y = int(y * h / self.height)
        click_window(self.target_window, real_x, real_y)

    def drag(self, x1, y1, x2, y2, duration=0.5):
        drag_window(self.target_window, x1, y1, x2, y2, duration)

    def activate_target_window(self):
        """激活目标窗口"""
        try:
            self.target_window.activate()
        except Exception as e:
            log(f"激活窗口失败: {e}")

    def is_window_active(self):
        return self.target_window.isActive

    def is_area_color(self, p1, p2, expected_color, tolerance=10, threshold_ratio=0.5):
        """检测指定区域颜色是否符合预期"""
        w, h = get_client_size(self.target_window)
        scaled_p1 = (int(p1[0] * w / self.width), int(p1[1] * h / self.height))
        scaled_p2 = (int(p2[0] * w / self.width), int(p2[1] * h / self.height))
        return check_area_color(self.target_window, scaled_p1, scaled_p2, expected_color, tolerance, threshold_ratio)

    def exit_program(self):
        log("检测到 / 键，退出程序")
        # self.stop_all()
        os._exit(0)
