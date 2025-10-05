from utils import *
class TaskController:
    def __init__(self, target_window):
        self.target_window = target_window
        self.tasks = []
        self.current_task_index = 0
        self.width, self.height = self.get_default_size()
    
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
        """每帧只运行当前任务"""
        while True:
            if self.current_task_index >= len(self.tasks):
                return  # 全部任务完成

            current_task = self.tasks[self.current_task_index]
            finished = current_task.check_and_run()

            if finished:  # 返回 True 表示任务完成
                self.current_task_index += 1

    def click(self, x, y):
        """1080*720 的逻辑坐标，自动缩放到窗口实际分辨率""" 
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

    def exit_program(self):
        log("检测到 / 键，退出程序")
        self.stop_all()
        os._exit(0)