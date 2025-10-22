import ctypes
import sys
from utils import *

ctypes.windll.shcore.SetProcessDpiAwareness(2)
sys.stdout.reconfigure(encoding='utf-8')

target_window = find_target_window()
target_window.activate()
time.sleep(0.1)
save_failed_screenshot(screenshot_window(target_window))