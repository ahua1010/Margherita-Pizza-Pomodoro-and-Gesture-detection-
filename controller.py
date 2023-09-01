import sys
import cv2
import pandas as pd
import numpy as np
import requests

from PyQt5.QtGui import *
from PyQt5.QtCore import QDateTime
from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtCore import QTimer, Qt, QDate, QTime, QDateTime
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QInputDialog, QHeaderView, QSpinBox, QDialogButtonBox, QDialog

from eye_tracking import eye_detect
from UI import Ui_MainWindow


#番茄鐘長短時設定
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

class MainWindow_controller(QtWidgets.QMainWindow):    
    def __init__(self):
        super().__init__() # in python3, super(Class, self).xxx = super().xxx
        self.ui = uic.loadUi("demo.ui",self)
        #self.ui.setupUi(self)
        self.setup_control()
        self.ui.fuctionlist.itemClicked.connect(self.tab_switch)
        self.renewData()
        self.ui.stackedWidget.setCurrentIndex(0)

        #番茄鐘初始
        self.tomato = 0
        self.bigrest = 4
        self.remaining_time = 25 * 60  # 初始倒數時間為25分鐘
        self.ui.progressBar.setMaximum(self.remaining_time)
        self.ui.progressBar.setValue(self.remaining_time)
        self.timer_running = False  # 計時器是否正在運行
        self.current_mode = 'Work'  # 目前的模式（工作或休息）
        self.open_flag=True #姿態檢測模式
        #self.video_stream=cv2.VideoCapture('D:/酪梨資料夾/大學作業/專題/pyqt/demo/test.mp4')
        self.painter = QPainter(self)
        self.dt=eye_detect()
        
        #todolist初始
        self.add = 0
        self.edit = 0
        self.ui.todo_date.setDateTime(QDateTime.currentDateTime())
        self.ui.todo_line.setVisible(False)
        self.ui.todo_date.setVisible(False)
    
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
        
    #連接按鈕
    def setup_control(self):
        #番茄鐘開始按鈕
        self.ui.tomato_start.clicked.connect(self.start_stop_timer)
        #修改按鈕
        self.ui.tomato_change.clicked.connect(self.change_time)
        #跳過按鈕
        self.ui.tomato_skip.clicked.connect(self.skip_timer)
        #重置按鈕
        self.ui.tomato_reset.clicked.connect(self.reset_timer)
        #todolist添加按鈕
        self.ui.todo_add.clicked.connect(self.add_check_task)
        #todolist編輯按鈕
        self.ui.todo_edit.clicked.connect(self.edit_check_task)
        #todolist刪除按鈕
        self.ui.todo_delete.clicked.connect(self.delete_task)
        #todolist清單物件
        self.todo_list.itemClicked.connect(self.load_task)
        self.ui.comboBox_city.currentIndexChanged.connect(self.showData)
        
    ##番茄鐘
    #更新時間
    def update_timer_label(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        time_text = '{:02d}:{:02d}'.format(minutes, seconds)
        self.ui.tomato_time.setText(time_text)

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
        self.timer.timeout.connect(self.decrease_remaining_time)
        self.timer.start(1000)
        
    def stop_timer(self):
        self.timer_running = False
        self.ui.tomato_start.setStyleSheet("border: none;\n"
        "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/start.png);")
        self.timer.stop()
        
    def skip_timer(self):
        self.remaining_time = 1
        self.ui.tomato_start.setStyleSheet("border: none;\n"
        "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/start.png);")
        self.handle_timer_completion(True)
        self.timer.stop()
        
    def reset_timer(self):
        self.stop_timer()
        if self.current_mode == 'Work':
            self.remaining_time = 25 * 60
        else:
            if self.bigrest == 4:
                self.remaining_time = 30 * 60  # 休息30分鐘
            else:
                self.remaining_time = 5 * 60  # 休息5分鐘
        self.start_timer()

    #時鐘秒數遞減
    def decrease_remaining_time(self):
        self.remaining_time -= 1
        self.ui.progressBar.setValue(self.remaining_time) 
        self.update_timer_label()

        if self.remaining_time > 0:
            return

        self.handle_timer_completion(False)
    
    #時鐘結束處理
    def handle_timer_completion(self,skip):
        self.timer.stop()
        self.timer_running = False
        self.ui.tomato_start.setStyleSheet("border: none;\n"
                                        "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/start.png);")

        if self.current_mode == 'Work':
            self.handle_work_completion(skip)
        else:
            self.handle_rest_completion()

        self.ui.progressBar.setMaximum(self.remaining_time)
        self.ui.progressBar.setValue(self.remaining_time)
        self.update_timer_label()
      
    #時鐘工作時段結束處理          
    def handle_work_completion(self, skip):
        #skip的話番茄數不會增加
        if not skip:
            self.tomato += 1
        if self.bigrest > 0:
            self.bigrest -= 1
        self.current_mode = 'Rest'
        if self.bigrest == 0:
            self.remaining_time = 30 * 60  # 休息30分鐘
            self.bigrest = 4
        else:
            self.remaining_time = 5 * 60  # 休息5分鐘
        self.ui.tomato_mode.setText("休息時間")
        self.ui.tomato_count.setText("總番茄數 x {}".format(self.tomato))
        self.ui.tomato_bigrest.setText("{} 節工作後長休息".format(self.bigrest))

    #時鐘工作時段結束處理 
    def handle_rest_completion(self):
        self.current_mode = 'Work'
        self.remaining_time = 25 * 60  # 工作25分鐘
        self.ui.tomato_mode.setText("工作時間")
    
    #todolist
    def add_check_task(self):
        if self.add == 0:
            self.add_task()
        else:
            self.check_task()
    
    def add_task(self):
        self.ui.todo_line.setVisible(True)
        self.ui.todo_date.setVisible(True)
        self.todo_add.setStyleSheet("border: none;\n"
"image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/check.png);")
        self.add = 1
    
    def check_task(self):
        task_text = self.ui.todo_line.text()
        date_time = self.ui.todo_date.dateTime()
        task_datetime_str = date_time.toString('yyyy-MM-dd hh:mm:ss')
        task_text_with_datetime = f'{task_text} (Due: {task_datetime_str})'
        self.ui.todo_line.setVisible(False)
        self.ui.todo_date.setVisible(False)
        self.todo_add.setStyleSheet("border: none;\n"
"image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/add.png);")
        self.add = 0

        if task_text:
            self.todo_list.addItem(task_text_with_datetime)
            self.ui.todo_line.clear()
    
    def edit_check_task(self):
        if self.edit == 0:
            self.edit_task()
        else:
            self.check_edit_task()
            
    def edit_task(self):
        selected_item = self.todo_list.currentItem()
        if selected_item:
            self.ui.todo_line.setVisible(True)
            self.ui.todo_date.setVisible(True)
            self.todo_edit.setStyleSheet("border: none;\n"
"image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/check.png);")
            self.edit = 1
   
    def check_edit_task(self):
        selected_item = self.todo_list.currentItem()
        if selected_item:
            new_task_text = self.ui.todo_line.text()
            date_time = self.ui.todo_date.dateTime()
            task_datetime_str = date_time.toString('yyyy-MM-dd hh:mm:ss')
            new_task_text_with_datetime = f'{new_task_text} (Due: {task_datetime_str})'
            if new_task_text:
                selected_item.setText(new_task_text_with_datetime)
                self.ui.todo_line.clear()
            self.ui.todo_line.setVisible(False)
            self.ui.todo_date.setVisible(False)
            self.todo_edit.setStyleSheet("border: none;\n"
    "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/edit.png);")
            self.edit = 0
        
    def delete_task(self):
        selected_item = self.todo_list.currentItem()
        if selected_item:
            confirm_delete = QMessageBox.question(self, '刪除任務', '確定刪除該項任務嗎?',
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm_delete == QMessageBox.Yes:
                self.todo_list.takeItem(self.todo_list.row(selected_item))
                
    def load_task(self, item):
        task_text = item.text().split(' (Due: ')[0]
        self.ui.todo_line.setText(task_text)
        date_time_str = item.text().split(' (Due: ')[1][:-1]
        date_time = QDateTime.fromString(date_time_str, 'yyyy-MM-dd hh:mm:ss')
        self.ui.todo_date.setDateTime(date_time)
        
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
    def renewData(self):
        self.getData()
        self.showData()
        
    def getData(self):
        api = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/'
        dataCode = 'F-C0032-001' # 臺灣各縣市天氣預報資料及國際都市天氣預報
        url = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001"
        
        Auth = "CWB-90732145-6FD1-4458-8DF5-3EEFA3973447"
        url = api + dataCode + "?Authorization="+ Auth + "&format=JSON"
        res = requests.get(url)
        
        self.data = res.json()
        # 首先取得縣市名稱並寫入 comboBox
        city = []
        for i in range(len(self.data['records']['location'])):
            city.append(self.data['records']['location'][i]['locationName'])
         
        self.ui.comboBox_city.addItems(city)
        self.ui.comboBox_city.setCurrentText("彰化縣")
    
    def showData(self):
        n, m = 3, 5
        cityName = self.comboBox_city.currentText()
        cityIdx = self.comboBox_city.currentIndex()
        # 先定位資料所在的結構層次，再依次取用
        tmp =self.data['records']['location'][cityIdx]['weatherElement']
        
        avg_temp = (int(tmp[2]['time'][0]['parameter']['parameterName']) + int(tmp[4]['time'][0]['parameter']['parameterName']))/2
        weather  = tmp[0]['time'][0]['parameter']['parameterName']
        self.ui.temperature.setText('{:.1f} °C'.format(avg_temp))
        self.ui.weather.setText('{}'.format(weather))
        
        #['時間', '天氣現象','降雨機率(%)','最低溫度','舒適度','最高溫度']
        #判斷天氣來放圖片
        if   "雷" in weather:
            self.ui.weather_icon.setStyleSheet("image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/多雲陣雨或雷雨.png);")
        elif "雨" in weather:
            self.ui.weather_icon.setStyleSheet("image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/多雲陣雨.png);")
        elif "多雲" in weather and "時晴" in weather:
            self.ui.weather_icon.setStyleSheet("image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/陰時多雲.png);")
        elif "雲" in weather:
            self.ui.weather_icon.setStyleSheet("image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/晴時多雲.png);")
        elif "晴天" in weather:
            self.ui.weather_icon.setStyleSheet("image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/晴天.png);")
        else:
            self.ui.weather_icon.setStyleSheet("image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/未知天氣.png);")
        
        chart = QChart()
        chart.setTitle("近二日天氣預測")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        #折線數據
        datetime_series = QLineSeries()
        x_values = []  # 用於存儲 QDateTime 對象

        for i in range(5):
            # 將日期時間字串轉換為 QDateTime 對象
            datetime = QDateTime.fromString(tmp[0]['time'][int(i/2)]['startTime'], "yyyy-MM-dd hh:mm:ss")
            # 添加到 x 軸值清單中
            x_values.append(datetime)
        
        min_temp = QLineSeries()
        y_values = []
        for i in range(5):
            if i%2 == 0:
                y_values.append(int(tmp[2]['time'][int(i/2)]['parameter']['parameterName']))
            else:
                y_values.append((int(tmp[2]['time'][int(i/2)]['parameter']['parameterName']) + int(tmp[2]['time'][int(i/2)+1]['parameter']['parameterName']))/2)
        for value in range(0, len(x_values)):
            min_temp.append(x_values[value].toMSecsSinceEpoch(), y_values[value])# 將 QDateTime 對象轉換為毫秒數
        min_temp.setName('最低溫度')
        chart.addSeries(min_temp)  # 加入最低溫折線
        min_ = min(y_values)
        max_ = max(y_values)
        
        max_temp = QLineSeries()
        y_values = []
        for i in range(5):
            if i%2 == 0:
                y_values.append(int(tmp[4]['time'][int(i/2)]['parameter']['parameterName']))
            else:
                y_values.append((int(tmp[4]['time'][int(i/2)]['parameter']['parameterName']) + int(tmp[4]['time'][int(i/2)+1]['parameter']['parameterName']))/2)
        for value in range(0, len(x_values)):
            max_temp.append(x_values[value].toMSecsSinceEpoch(), y_values[value])
        max_temp.setName('最高溫度')
        chart.addSeries(max_temp)  # 加入最高溫折線
        min_ = min(min_, min(y_values))
        max_ = max(max_, max(y_values))
        
        #折線圖顯示調整
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MM-dd hh:mm")  # 設定日期時間的顯示格式
        axis_x.setTickCount(5)  # 設定顯示的刻度數量
        axis_x.setTitleText("日期時間")  # 設定 x 軸標題
        axis_x.setMin(x_values[0])  # 設定 x 軸最小值
        axis_x.setMax(x_values[4])  # 設定 x 軸最大值

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setRange(min_ - 1, max_ + 1) 
        axis_y.setTitleText("溫度")
        
        chart.setAxisX(axis_x)
        chart.setAxisY(axis_y)
        for series in chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
        
        #加入layout
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        v_box = QVBoxLayout()
        v_box.addWidget(chart_view)
        self.ui.chart.setLayout(v_box)
