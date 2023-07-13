import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QInputDialog

#from eye_tracking import *
#import cv2
#import numpy as np

from UI import Ui_MainWindow

class MainWindow_controller(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__() # in python3, super(Class, self).xxx = super().xxx
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_control()
        #番茄鐘初始
        self.remaining_time = 25 * 60  # 初始倒數時間為25分鐘
        self.timer_running = False  # 計時器是否正在運行
        self.current_mode = 'Work'  # 目前的模式（工作或休息）
        
    def setup_control(self):
        #番茄鐘開始按鈕
        self.ui.tomato_start.clicked.connect(self.start_stop_timer)
        #修改按鈕
        self.ui.tomato_change.clicked.connect(self.change_time)
        #跳過按鈕
        self.ui.tomato_skip.clicked.connect(self.skip_timer)
        
    #更新時間
    def update_timer_label(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        time_text = '{:02d}:{:02d}'.format(minutes, seconds)
        self.ui.tomato_time.setText(time_text)

    #修改時間
    def change_time(self):
        time, ok = QInputDialog.getInt(self, '修改時間', '請輸入計時時間（分鐘）:', self.remaining_time // 60, 0, 60)
        if ok:
            self.remaining_time = time * 60
            self.update_timer_label()

    def start_stop_timer(self):
        if self.timer_running:
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self):
        if self.timer_running:
            return

        self.timer_running = True
        self.ui.tomato_start.setStyleSheet("border: none;\n"
"image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/stop.png);")
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
        
    def stop_timer(self):
        self.timer_running = False
        self.ui.tomato_start.setStyleSheet("border: none;\n"
"image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/start.png);")
        self.timer.stop()
        
    def skip_timer(self):
        self.timer.stop()
        self.remaining_time = 1
        self.ui.tomato_start.setStyleSheet("border: none;\n"
"image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/start.png);")
        self.update_timer()

    def update_timer(self):
        self.remaining_time -= 1
        self.update_timer_label()

        if self.remaining_time <= 0:
            self.timer.stop()
            self.timer_running = False
            self.ui.tomato_start.setStyleSheet("border: none;\n"
    "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/start.png);")

            if self.current_mode == 'Work':
                self.current_mode = 'Rest'
                self.remaining_time = 5 * 60  # 休息5分鐘
                self.ui.tomato_mode.setText("REST")
            else:
                self.current_mode = 'Work'
                self.remaining_time = 25 * 60  # 工作25分鐘
                self.ui.tomato_mode.setText("WORK")
        