import threading
import time
from utils import log, click_window, screenshot_window, get_rgb_image
import cv2
import numpy as np


class Image:
    def __init__(self, path):
        self.path = path
        self.image = get_rgb_image(self.path)
class Task:
    def __init__(self, name, controller):
        self.name = name
        self.controller = controller
        self.enabled = True   # 任务是否启用
    
    def check_and_run(self):
        """每个任务实现：判断是否该执行 + 执行操作"""
        raise NotImplementedError
    
    def match_template_but_not_click(self, image:Image, times = 5, delay = 1, threshold=0.5):
        count = 0
        image_path, image = image.path, image.image
        while count<times:
            self.controller.activate_target_window()
            screenshot = screenshot_window(self.controller.target_window)
            screenshot = cv2.resize(screenshot, self.controller.get_default_size())
            res = cv2.matchTemplate(screenshot, image, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            x, y = max_loc
            h, w = image.shape[:2]
            recogonize_flag = max_val > threshold
            log(f"[{self.name} {image_path}] {recogonize_flag and '识别成功' or '识别失败'} {count}. 匹配度: {max_val:.2f}, 位置: {max_loc}，匹配位置: ({x}, {y}), 尺寸: ({w}, {h})")
            if recogonize_flag:  # 匹配度阈值
                # 画出匹配到的矩形框，便于调试
                if self.controller.is_testing:
                    cv2.rectangle(screenshot, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.imwrite("debug_match.png", cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR))  # 或保存到文件
                return True
            else:
                if self.controller.is_testing:
                    cv2.rectangle(screenshot, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.imwrite("debug_match_failed.png", cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR))  # 或保存到文件
            count+=1
            time.sleep(delay)
        return False
    
    def match_template(self, image, times = 5, delay = 1, threshold=0.5):
        count = 0
        while count<times:
            self.controller.activate_target_window()
            screenshot = screenshot_window(self.controller.target_window)
            screenshot = cv2.resize(screenshot, self.controller.get_default_size())
            res = cv2.matchTemplate(screenshot, image, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            x, y = max_loc
            h, w = image.shape[:2]
            log(f"[{self.name}] {count}. 匹配度: {max_val:.2f}, 位置: {max_loc}，匹配位置: ({x}, {y}), 尺寸: ({w}, {h})")
            if max_val > threshold:  # 匹配度阈值
                # 画出匹配到的矩形框，便于调试
                cv2.rectangle(screenshot, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.imwrite("debug_match.png", cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR))  # 或保存到文件
                log(f"[{self.name}] 识别成功")
                self.controller.click(x+int(w/2), y+int(h/2))
                return True
            else:
                cv2.rectangle(screenshot, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.imwrite("debug_match_failed.png", cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR))  # 或保存到文件
                log(f"[{self.name}] 识别失败")
            count+=1
            time.sleep(delay)
        return False

class EnterGameTask(Task):
    def __init__(self, name, controller):
        super().__init__(name, controller)
        # 提前加载按钮模板（比如 start_button.png）
            # 提前加载按钮模板并转换成 RGB
        self.start_btn = Image("assets/start_button.png")
        self.hai_btn = Image("assets/hai_button.png")
    
    def check_and_run(self):
        if not self.enabled:
            return
        self.match_template(self.start_btn)
        time.sleep(1)
        self.match_template(self.hai_btn)
        return True


class SkipTask(Task):
    def __init__(self, name, controller):
        super().__init__(name, controller)
        # 提前加载按钮模板（比如 start_button.png）
        self.skip_btn = Image("assets/skip_button.png")

    def check_and_run(self):
        if not self.enabled:
            return
        for i in range(10):  # 循环 10 次
            self.match_template(self.skip_btn, threshold=0.5)
            time.sleep(1)  # 每次间隔 1 秒
        return True

class CloseTask(Task):
    def __init__(self, name, controller):
        super().__init__(name, controller)
        # 提前加载按钮模板（比如 start_button.png）
        self.btn = Image("assets/close_btn.png")

    def check_and_run(self):
        if not self.enabled:
            return
        for i in range(5):  # 循环 10 次
            self.match_template(self.btn, threshold=0.5)
            time.sleep(1)  # 每次间隔 1 秒
        return True

class RewardTask(Task):
    def __init__(self, name, controller):
        super().__init__(name, controller)
        self.btn = Image("assets/reward_btn.png")
        self.close_btn = Image("assets/close_btn.png")

    def check_and_run(self):
        if not self.enabled:
            return
        self.match_template(self.btn, threshold=0.5)
        time.sleep(5)  # 等待 1 秒，确保界面稳定
        self.match_template(self.close_btn, threshold=0.5)
        return True

class DailyTask(Task):
    def __init__(self, name, controller):
        super().__init__(name, controller)
        self.quest_btn = Image("assets/quest_btn.png")
        self.daily_1_btn = Image("assets/daily_1.png")
        self.skip_daily_1 = Image("assets/skip_daily_1.png")
        self.ok = Image("assets/ok.png")
        self.hai = Image("assets/hai.png")
        self.return_btn = Image("assets/return.png")
        self.daily_2_btn = Image("assets/daily_2.png")
        self.skip_daily_2 = Image("assets/skip_daily_2.png")
        self.home = Image("assets/home.png")

    def check_and_run(self):
        if not self.enabled:
            return
        self.match_template(self.quest_btn, threshold=0.5)
        self.match_template(self.daily_1_btn, threshold=0.5)
        self.match_template(self.skip_daily_1, threshold=0.5)
        self.match_template(self.ok, threshold=0.5)
        time.sleep(1)  # 等待 1 秒，确保界面稳定
        self.match_template(self.hai, threshold=0.5)
        for _ in range(7):
            time.sleep(1)
            self.controller.click(640, 620)
        self.match_template(self.return_btn, threshold=0.5)
        self.match_template(self.daily_2_btn, threshold=0.5)
        self.match_template(self.skip_daily_2, threshold=0.5)
        time.sleep(1)
        self.controller.click(700, 420)
        time.sleep(1)
        self.match_template(self.ok, threshold=0.5)
        time.sleep(1)  # 等待 1 秒，确保界面稳定
        self.match_template(self.hai, threshold=0.5)
        for _ in range(7):
            time.sleep(1)
            self.controller.click(640, 620)
        time.sleep(1)
        self.match_template(self.home, threshold=0.5)
        return True

class TowerTask(Task):
    def __init__(self, name, controller):
        super().__init__(name, controller)
        self.quest_btn = Image("assets/quest_btn.png")
        self.tower = Image("assets/tower.png")
        self.tower_word = Image("assets/tower_word.png")
        self.return_btn = Image("assets/return.png")
        self.chuji = Image("assets/chuji.png")
        self.winner = Image("assets/winner.png")
        self.home = Image("assets/home.png")
        self.tower_btn_pos = [(259,280),(479,280),(699,280),(919,280),(1139,280)]

    def check_and_run(self):
        if not self.enabled:
            return
        self.match_template(self.quest_btn, threshold=0.5)
        time.sleep(1)
        if self.match_template(self.tower, threshold=0.5):
            time.sleep(1)
            for pos in self.tower_btn_pos:
                self.controller.click(*pos)
                time.sleep(1)
                for _ in range(5):
                    if self.match_template_but_not_click(self.tower_word, threshold=0.5):
                        break
                    if self.match_template(self.chuji, threshold=0.5):
                        time.sleep(1)
                        if self.match_template(self.chuji, threshold=0.5):
                            time.sleep(20)  # 等待，确保战斗开始
                            self.match_template(self.winner, times = 5, delay = 20, threshold=0.5)
                            time.sleep(1)  # 等待 1 秒，确保界面稳定
                            for _ in range(4):
                                time.sleep(1)
                                self.controller.click(*self.controller.get_point(0.9, 0.9))
                            time.sleep(5)  # 等待 1 秒，确保界面稳定
                        else:
                            continue
                    # self.match_template(self.return_btn, threshold=0.5)
        time.sleep(1)
        self.match_template(self.home, threshold=0.5)
        return True

class DailyRewardTask(Task):
    def __init__(self, name, controller):
        super().__init__(name, controller)
        self.mission = Image("assets/mission.png")
        self.receive = Image("assets/receive.png")

    def check_and_run(self):
        if not self.enabled:
            return
        self.match_template(self.mission, threshold=0.5)
        time.sleep(1)  # 等待 1 秒，确保界面稳定
        self.match_template(self.receive, threshold=0.5)
        return True

class ReceivePresentTask(Task):
    def __init__(self, name, controller):
        super().__init__(name, controller)
        self.present = Image("assets/present.png")
        self.receive = Image("assets/present_receive.png")
        self.close = Image("assets/close_btn.png")

    def check_and_run(self):
        self.match_template(self.present, threshold=0.5)
        time.sleep(1)
        self.match_template(self.receive, threshold=0.5)
        time.sleep(2)
        self.match_template(self.close, threshold=0.5)
        time.sleep(1)
        self.match_template(self.close, threshold=0.5)
        return True

class AutoBattleTask(Task):
    def __init__(self, name, controller):
        super().__init__(name, controller)
        self.battle = Image("assets/chuji.png")
        self.winner = Image("assets/winner.png")
        self.skip = Image("assets/skip_button.png")

    def check_and_run(self):
        if not self.enabled:
            return
        x1,y1 = self.controller.get_point(0.7, 0.38)
        x2,y2 = self.controller.get_point(0.7, 0.8)
        while True:
            self.controller.drag(x1, y1, x2, y2, duration=0.2)
            time.sleep(0.2)
            self.controller.click(x1,y1)
            time.sleep(3)
            if self.match_template(self.skip, times = 5, delay = 1, threshold=0.5):
                break
            self.match_template(self.battle, threshold=0.5)
            time.sleep(20)  # 等待 10 秒，确保战斗开始
            self.match_template(self.winner, times = 5, delay = 20, threshold=0.5)
            time.sleep(1)  # 等待 1 秒，确保界面稳定
            for _ in range(4):
                time.sleep(1)
                self.controller.click(*self.controller.get_point(0.9, 0.9))
            time.sleep(5)  # 等待 1 秒，确保界面稳定
        return True
    
class BackToHomeTask:
    def __init__(self, name, controller):
        super().__init__(name, controller)
        self.home = Image("assets/home.png")

    def check_and_run(self):
        self.match_template(self.home, threshold=0.5)
        return True

class DelayTask(Task):
    def __init__(self, name, controller, delay_seconds=5):
        super().__init__(name, controller)
        self.delay_seconds = delay_seconds
        self.start_time = None

    def check_and_run(self):
        if self.start_time is None:
            self.start_time = time.time()
            log(f"[{self.name}] 开始等待 {self.delay_seconds} 秒")
        time.sleep(self.delay_seconds)
        log(f"[{self.name}] 等待完成")
        return True  # 任务完成