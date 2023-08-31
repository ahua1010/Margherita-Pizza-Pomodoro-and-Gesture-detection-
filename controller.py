import sys
import cv2

from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QInputDialog, QHeaderView, QSpinBox, QDialogButtonBox, QDialog

import pandas as pd
import numpy as np
import requests

from eye_tracking import eye_detect
from UI import Ui_MainWindow
#番茄中設定
class WorkTimeDialog(QDialog):
    def __init__(self, parent=None):
        super(WorkTimeDialog, self).__init__(parent)
        self.setWindowTitle("設定工作和休息時間")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 第一個標題及對應的上下按鈕
        work_label = QLabel("請輸入工作時間（分鐘）:")
        self.work_spinbox = QSpinBox()
        self.work_spinbox.setMinimum(1)
        self.work_spinbox.setMaximum(60)
        self.work_spinbox.setValue(25)

        layout.addWidget(work_label)
        layout.addWidget(self.work_spinbox)

        # 第二個標題及對應的上下按鈕
        rest_label = QLabel("請輸入短休息時間（分鐘）:")
        self.short_rest_spinbox = QSpinBox()
        self.short_rest_spinbox.setMinimum(1)
        self.short_rest_spinbox.setMaximum(15)
        self.short_rest_spinbox.setValue(5)

        layout.addWidget(rest_label)
        layout.addWidget(self.short_rest_spinbox)
        
        # 第三個標題及對應的上下按鈕
        rest_label = QLabel("請輸入長休息時間（分鐘）:")
        self.long_rest_spinbox = QSpinBox()
        self.long_rest_spinbox.setMinimum(1)
        self.long_rest_spinbox.setMaximum(40)
        self.long_rest_spinbox.setValue(20)

        layout.addWidget(rest_label)
        layout.addWidget(self.long_rest_spinbox)

        # 按鈕佈局
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        self.setLayout(layout)

class TableModel(QtCore.QAbstractTableModel):
 
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data
 
    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()] #pandas's iloc method
            return str(value)
 
        if role == Qt.ItemDataRole.TextAlignmentRole:          
            return Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignHCenter
            # return Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignLeft
         
        if role == Qt.ItemDataRole.BackgroundRole and (index.row()%2 == 0):
            return QtGui.QColor('#d8ffdb')
 
    def rowCount(self, index):
        return self._data.shape[0]
 
    def columnCount(self, index):
        return self._data.shape[1]
 
    # Add Row and Column header
    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole: # more roles
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
 
            # if orientation == Qt.Orientation.Vertical:
            #     return str(self._data.index[section])

class MainWindow_controller(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__() # in python3, super(Class, self).xxx = super().xxx
        self.ui = uic.loadUi("demo.ui",self)
        #self.ui.setupUi(self)
        self.setup_control()
        self.data = self.getData()
        self.showData()
        self.ui.stackedWidget.setCurrentIndex(0)
         
        # Signals
        self.ui.comboBox_city.currentIndexChanged.connect(self.showData)
        self.ui.fuctionlist.itemClicked.connect(self.tab_switch)

        #番茄鐘初始
        self.remaining_time = 25 * 60  # 初始倒數時間為25分鐘
        self.timer_running = False  # 計時器是否正在運行
        self.current_mode = 'Work'  # 目前的模式（工作或休息）
        self.open_flag=True #姿態檢測模式
        self.work_time = 25 * 60 #預設工作時間
        self.short_rest_time = 5 * 60 #預設休息時間
        self.long_rest_time = 20 * 60 #預設休息時間
        #self.video_stream=cv2.VideoCapture('D:/酪梨資料夾/大學作業/專題/pyqt/demo/test.mp4')
        self.painter = QPainter(self)
        self.dt=eye_detect()
    
    #tab切換
    def tab_switch(self,Index):
        if self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "首頁":
            self.ui.stackedWidget.setCurrentIndex(0)
        elif self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "伸展操":
            self.ui.stackedWidget.setCurrentIndex(1)
        elif self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "天氣":
            self.ui.stackedWidget.setCurrentIndex(2)
        elif self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "設定":
            self.ui.stackedWidget.setCurrentIndex(3)
        else:
            self.ui.stackedWidget.setCurrentIndex(0)
    
    #番茄鐘功能
    def setup_control(self):
        #番茄鐘開始按鈕
        self.ui.tomato_start.clicked.connect(self.start_stop_timer)
        #修改按鈕
        self.ui.tomato_change.clicked.connect(self.change_time)
        #跳過按鈕
        self.ui.tomato_skip.clicked.connect(self.skip_timer)
        #重設按鈕
        self.ui.tomato_reset.clicked.connect(self.reset_timer)
        
    #更新時間
    def update_timer_label(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        time_text = '{:02d}:{:02d}'.format(minutes, seconds)
        self.ui.tomato_time.setText(time_text)
        self.ui.progressBar.setMaximum(self.remaining_time)

    #修改時間
    def change_time(self):
        dialog = WorkTimeDialog()
        dialog.exec_()
        self.work_time = dialog.work_spinbox.value() * 60
        self.short_rest_time = dialog.short_rest_spinbox.value() * 60
        self.long_rest_time = dialog.long_rest_spinbox.value() * 60

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
        if self.current_mode == 'Work':
            self.ui.progressBar.setValue(self.work_time - self.remaining_time)
        else:
            self.ui.progressBar.setValue(self.short_rest_time - self.remaining_time)

        if self.remaining_time <= 0:
            self.timer.stop()
            self.timer_running = False
            self.ui.tomato_start.setStyleSheet("border: none;\n"
            "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/start.png);")

            if self.current_mode == 'Work':
                self.current_mode = 'Rest'
                self.remaining_time = self.short_rest_time  # 休息5分鐘
                self.ui.tomato_mode.setText("休息時間")
            else:
                self.current_mode = 'Work'
                self.remaining_time = self.work_time  # 工作25分鐘
                self.ui.tomato_mode.setText("工作時間")
            
    def reset_timer(self):
        self.timer.stop()
        self.timer_running = False
        self.ui.tomato_start.setStyleSheet("border: none;\n"
        "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/start.png);")

        if self.current_mode == 'Work':
            self.current_mode = 'Work'
            self.remaining_time = self.work_time  # 工作25分鐘
            self.ui.tomato_mode.setText("工作時間")
        else:
            self.current_mode = 'Rest'
            self.remaining_time = self.short_rest_time  # 休息5分鐘
            self.ui.tomato_mode.setText("休息時間")
        self.update_timer_label()

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
            
    #天氣預報功能
    # Slots
    def getData(self):
        api = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/'
        dataCode = 'F-C0032-001' # 臺灣各縣市天氣預報資料及國際都市天氣預報
        url = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001"
        
        Auth = "CWB-90732145-6FD1-4458-8DF5-3EEFA3973447"
        url = api + dataCode + "?Authorization="+ Auth + "&format=JSON"
        res = requests.get(url)
        
        data = res.json()
        # 首先取得縣市名稱並寫入 comboBox
        city = []
        for i in range(len(data['records']['location'])):
            city.append(data['records']['location'][i]['locationName'])
         
        self.ui.comboBox_city.addItems(city)
        return data
    
    def showData(self):
        n, m = 3, 5
        cityName = self.comboBox_city.currentText()
        cityIdx = self.comboBox_city.currentIndex()
        # 先定位資料所在的結構層次，再依次取用
        tmp =self.data['records']['location'][cityIdx]['weatherElement']
        d = []
        for i in range(n):
            d.append(tmp[0]['time'][i]['startTime'])
            for j in range(m):
                d.append(tmp[j]['time'][i]['parameter']['parameterName'])
         
        self.df = pd.DataFrame(np.reshape(d, (n,m+1)))
        self.df.columns = ['時間', '天氣現象','降雨機率(%)','最低溫度','舒適度','最高溫度']
        self.model = TableModel(self.df)
        self.ui.tableView.setModel(self.model)
        # self.tableView.resizeColumnsToContents
        self.ui.tableView.resizeColumnToContents(0)
        self.ui.tableView.resizeColumnToContents(1)
        self.ui.tableView.resizeColumnToContents(2)
        self.ui.tableView.resizeColumnToContents(3)
        self.ui.tableView.resizeColumnToContents(5)
        # 设置列宽自动调整
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        