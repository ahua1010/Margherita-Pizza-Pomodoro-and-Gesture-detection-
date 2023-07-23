import sys
import cv2
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QInputDialog
from eye_tracking import eye_detect
from UI import Ui_MainWindow

class MainWindow_controller(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__() # in python3, super(Class, self).xxx = super().xxx
        self.ui = uic.loadUi("demo.ui",self)
        #self.ui.setupUi(self)
        self.setup_control()
        self.ui.fuctionlist.itemClicked.connect(self.tab_switch)

        #番茄鐘初始
        self.remaining_time = 25 * 60  # 初始倒數時間為25分鐘
        self.timer_running = False  # 計時器是否正在運行
        self.current_mode = 'Work'  # 目前的模式（工作或休息）
        self.open_flag=True #姿態檢測模式
        #self.video_stream=cv2.VideoCapture('D:/酪梨資料夾/大學作業/專題/pyqt/demo/test.mp4')
        self.painter = QPainter(self)
        self.dt=eye_detect()
    
    #tab切換
    def tab_switch(self,Index):
        if self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "首頁":
            self.ui.stackedWidget.setCurrentIndex(0)
        elif self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "伸展操":
            self.ui.stackedWidget.setCurrentIndex(1)
        # self.stackedWidget.setCurrentIndex(1)
        # self.stackedWidget.setCurrentIndex(2)
        
    #番茄鐘功能
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
                self.ui.tomato_mode.setText("休息時間")
            else:
                self.current_mode = 'Work'
                self.remaining_time = 25 * 60  # 工作25分鐘
                self.ui.tomato_mode.setText("工作時間")

    '''
    def on_video(self):
        if self.open_flag:
            self.pushButton.setText('open')
        else:
            self.pushButton.setText('close')
        self.open_flag = bool(1-self.open_flag)#
    '''
        
    '''def paintEvent(self, a0: QtGui.QPaintEvent):
        if self.open_flag:
            ret, frame = self.video_stream.read()
            if frame is None:
                return
            frame=cv2.resize(frame,(self.ui.frame4.size().width(), frame.shape[0]),interpolation=cv2.INTER_AREA)
            frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            frame=self.dt.run(ret, frame)
            self.Qframe=QImage(frame.data,frame.shape[1],frame.shape[0],frame.shape[1]*3,QImage.Format_RGB888)
            self.ui.face_tracking.setPixmap(QPixmap.fromImage(self.Qframe))
            self.update()'''
        