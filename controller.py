import numpy as np
import requests
import PyQt5.sip as sip
from PyQt5.QtGui import *
from PyQt5.QtCore import QDateTime, QUrl, QThread
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox, QDialog, QMessageBox, QStyle
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from win10toast import ToastNotifier  # 导入系统通知对象
import time  # 系统时间模块
import datetime
from threading import Timer  # 定时器

from stretch import stretchdectector as sd
from hunchback_detection import HunchbackDetection

from UI import Ui_MainWindow

class MainWindow_controller(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__() # in python3, super(Class, self).xxx = super().xxx
        self.ui = uic.loadUi("demo.ui",self)
        #self.ui.setupUi(self)
        self.renewWeatherData()
        self.setup_control()
        self.ui.fuctionlist.itemClicked.connect(self.tab_switch)
        self.ui.stackedWidget.setCurrentIndex(0)

        #番茄鐘初始
        self.tomato = 0
        self.bigrest = 4
        self.work_time = 25
        self.short_rest_time = 5
        self.long_rest_time = 20
        self.remaining_time = self.work_time * 60  # 初始倒數時間為25分鐘
        self.timer = QTimer()
        self.ui.progressBar.setMaximum(self.remaining_time)
        self.ui.progressBar.setValue(self.remaining_time)
        self.timer_running = False  # 計時器是否正在運行
        self.timer_connected = False  # 用於跟蹤 timeout 信號的連接狀態
        self.current_mode = 'Work'  # 目前的模式（工作或休息）
        
        #todo list初始
        self.add = 0
        self.edit = 0
        self.ui.todo_date.setDateTime(QDateTime.currentDateTime())
        self.ui.todo_line.setVisible(False)
        self.ui.todo_date.setVisible(False)

        # 首頁辨識初始
        # 設定相機功能
        self.ProcessCam = HunchbackDetection()  # 建立相機物件
        self.openCam()
        if self.ProcessCam.connect:
            # 連接影像訊號 (rawdata) 至 getRaw()
            self.ProcessCam.rawdata.connect(self.getRawImg)  # 槽功能：取得並顯示影像

        self.create_player()

    def closeEvent(self, event):
        print()
        print("close")
        print()
        self.ProcessCam.close()
    
    #tab切換
    def tab_switch(self,Index):
        if self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "首頁":
            self.openCam()
            self.ui.stackedWidget.setCurrentIndex(0)
        elif self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "伸展操":
            self.ProcessCam.stop()
            self.ui.stackedWidget.setCurrentIndex(1)
        elif self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "天氣":
            self.ProcessCam.stop()
            self.ui.stackedWidget.setCurrentIndex(2)
        elif self.ui.fuctionlist.item(self.ui.fuctionlist.row(Index)).text() == "設定":
            self.ProcessCam.stop()
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
        self.ui.comboBox_city.currentIndexChanged.connect(self.showWeatherData)
        
    ##番茄鐘
    #更新時間
    def update_timer_label(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        time_text = '{:02d}:{:02d}'.format(minutes, seconds)
        self.ui.progressBar.setValue(self.remaining_time)
        self.ui.tomato_time.setText(time_text)

    #修改時間
    def change_time(self):
        dialog = WorkTimeDialog((self.work_time, self.short_rest_time, self.long_rest_time))
        dialog.exec_()
        self.work_time = dialog.work_spinbox.value()
        self.short_rest_time = dialog.short_rest_spinbox.value()
        self.long_rest_time = dialog.long_rest_spinbox.value()

    def start_stop_timer(self):
        if self.timer_running:
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self):
        if self.timer_running:
            return  # 如果計時器已經在運行，則不執行任何操作
        self.timer_running = True
        self.ui.tomato_start.setStyleSheet("border: none;\n"
        "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/stop.png);")

        if not self.timer_connected:
            # 連接 timeout 信號，但僅在第一次開始計時器時執行
            self.timer.timeout.connect(self.decrease_remaining_time)
            self.timer_connected = True
        
        self.timer.start(1000)
        
    def stop_timer(self):
        self.timer_running = False
        self.ui.tomato_start.setStyleSheet("border: none;\n"
        "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/play.png);")
        self.timer.stop()
        
    def skip_timer(self):
        self.remaining_time = 1
        self.ui.tomato_start.setStyleSheet("border: none;\n"
        "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/play.png);")
        self.handle_timer_completion(True)
        self.timer.stop()
        
    def reset_timer(self):
        self.stop_timer()
        if self.current_mode == 'Work':
            self.remaining_time = self.work_time * 60
        else:
            if self.bigrest == 4:
                self.remaining_time = self.long_rest_time * 60
            else:
                self.remaining_time = self.short_rest_time * 60
        self.update_timer_label()  # 手動更新計時器顯示
        self.start_timer()  # 重新啟動計時器

    #時鐘秒數遞減
    def decrease_remaining_time(self):
        self.remaining_time -= 1
        self.ui.progressBar.setValue(self.remaining_time) 
        self.update_timer_label()

        if self.remaining_time > 0:
            return

        self.handle_timer_completion(False)
    
    #時鐘結束處理
    def handle_timer_completion(self, skip):
        self.timer.stop()
        self.timer_running = False

        if self.current_mode == 'Work':
            self.handle_work_completion(skip)
            self.ui.tomato_start.setStyleSheet("border: none;\n"
                                            "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/play.png);")
        else:
            self.handle_rest_completion()
            self.ui.tomato_start.setStyleSheet("border: none;\n"
                                            "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/play.png);")
        self.ui.progressBar.setMaximum(self.remaining_time)
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
            self.remaining_time = self.long_rest_time * 60  # 休息30分鐘
            self.bigrest = 4
        else:
            self.remaining_time = self.short_rest_time * 60  # 休息5分鐘
        self.ui.tomato_mode.setText("休息時間")
        self.ui.tomato_count.setText("總番茄數 x {}".format(self.tomato))
        self.ui.tomato_bigrest.setText("{} 節工作後長休息".format(self.bigrest))

    #時鐘工作時段結束處理 
    def handle_rest_completion(self):
        self.current_mode = 'Work'
        self.remaining_time = self.work_time * 60  # 工作25分鐘
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
        self.todo_add.setStyleSheet("border: none;\n" "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/check.png);")
        self.add = 1
    
    def check_task(self):
        task_text = self.ui.todo_line.text()
        date_time = self.ui.todo_date.dateTime()
        task_datetime_str = date_time.toString('yyyy-MM-dd hh:mm:ss')
        task_text_with_datetime = f'{task_text} (Due: {task_datetime_str})'
        self.ui.todo_line.setVisible(False)
        self.ui.todo_date.setVisible(False)
        self.todo_add.setStyleSheet("border: none;\n" "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/add.png);")
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
            self.todo_edit.setStyleSheet("border: none;\n" "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/check.png);")
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
            self.todo_edit.setStyleSheet("border: none;\n" "image:url(D:/酪梨資料夾/大學作業/專題/pyqt/demo/img/edit.png);")
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

    # 首頁影像辨識
    def openCam(self):
        if self.ProcessCam.connect:
            self.ProcessCam.open()
            self.ProcessCam.start()

    def getRawImg(self, data):
        self.showDataImg(data)

    def showDataImg(self, img):
        self.Ny, self.Nx, _ = img.shape  # 取得影像尺寸

        # 反轉顏色
        img_new = np.zeros_like(img)
        img_new[...,0] = img[...,2]
        img_new[...,1] = img[...,1]
        img_new[...,2] = img[...,0]
        img = img_new

        # 建立 Qimage 物件 (RGB格式)
        qimg = QtGui.QImage(img.data, self.Nx, self.Ny, QtGui.QImage.Format_RGB888)
        labelSize = self.ui.face_tracking.size()
        pixmap = QPixmap(qimg).scaled(labelSize.width(), labelSize.height())
        self.ui.face_tracking.setPixmap(pixmap)

    #天氣預報功能
    # Slots
    def renewWeatherData(self):
        self.getWeatherData()
        self.showWeatherData()
        
    def getWeatherData(self):
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
    
    def showWeatherData(self):
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
             
        # 获取QWidget的引用（例如，您的QWidget对象是widget）
        widget = self.ui.chart  # 用您的QWidget对象替换这里的self.ui.chart

        # 清除布局
        old_layout = widget.layout()  # 获取QWidget的布局
        if old_layout is not None:
            if old_layout is not None:
                for i in reversed(range(old_layout.count())):
                    old_layout.itemAt(i).widget().setParent(None)
                sip.delete(old_layout)
           
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
            if value % 2 == 0:
                min_temp.append(x_values[value].toMSecsSinceEpoch(), y_values[value])# 將 QDateTime 對象轉換為毫秒數
            else:
                min_temp.append((x_values[value-1].toMSecsSinceEpoch()+x_values[value+1].toMSecsSinceEpoch())/2, y_values[value])# 將 QDateTime 對象轉換為毫秒數
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
            if value % 2 == 0:
                max_temp.append(x_values[value].toMSecsSinceEpoch(), y_values[value])
            else:
                max_temp.append((x_values[value-1].toMSecsSinceEpoch()+x_values[value+1].toMSecsSinceEpoch())/2, y_values[value])# 將 QDateTime 對象轉換為毫秒數
            print(max_temp)
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

    # 伸展操介面
    # 影片播放
    def create_player(self):
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        videowidget = self.ui.widgetVideo

        # 影片播放按鈕變數類別屬性
        self.ui.btnPause.setEnabled(False)  # 禁用暫停按鈕，使其無法點擊
        self.ui.btnPause.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))  # 設置播放按鈕的圖示為播放圖示
        self.ui.btnPause.clicked.connect(self.play_video)  # 連接暫停按鈕的點擊事件到 play_video 方法，點擊時執行播放功能

        self.ui.slideVideo.sliderMoved.connect(self.set_position)  # 當影片進度條滑動時，連接到 set_position 方法，用於設定播放位置
        self.mediaPlayer.setVideoOutput(videowidget)  # 設定媒體播放器的視頻輸出為 videowidget，以顯示影片畫面
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)  # 監聽媒體播放器的狀態變化，連接到 mediastate_changed 方法
        self.mediaPlayer.positionChanged.connect(self.position_changed)  # 監聽播放位置的變化，連接到 position_changed 方法
        self.mediaPlayer.durationChanged.connect(self.duration_changed)  # 監聽媒體的總播放時間變化，連接到 duration_changed 方法
        self.mediaPlayer.mediaStatusChanged.connect(self.handle_media_status)

        # buttton to play video
        self.ui.btnVideo1.clicked.connect(self.video_select)
        self.ui.btnVideo2.clicked.connect(self.video_select)
        self.ui.btnVideo3.clicked.connect(self.video_select)
        self.ui.btnVideo4.clicked.connect(self.video_select)
        self.ui.btnVideo5.clicked.connect(self.video_select)
        self.ui.btnVideo6.clicked.connect(self.video_select)

    # 影片按鈕選擇
    def video_select(self):
        self.ui.stackedWidget.setCurrentIndex(4)
        btn_name = self.sender().objectName()

        video_mapping = {
            'btnVideo1': ('Resource/title_video/title1.mp4', 1),
            'btnVideo2': ('Resource/title_video/title2.mp4', 2),
            'btnVideo3': ('Resource/title_video/title3.mp4', 3),
            'btnVideo4': ('Resource/title_video/title4.mp4', 4),
            'btnVideo5': ('Resource/title_video/title5.mp4', 5),
            'btnVideo6': ('Resource/title_video/title6.mp4', 6)
        }

        global videoId
        filename, videoId = video_mapping.get(btn_name, ('', 0))
        self.open_and_play_video(filename)

    # 開啟並播放影片
    def open_and_play_video(self, filename):
        if filename != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.ui.btnPause.setEnabled(True)

            if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
                self.mediaPlayer.pause()
            else:
                self.mediaPlayer.play()

    # 變更播放暫停按鍵的 icon
    def mediastate_changed(self, state):
        icon = self.style().standardIcon(QStyle.SP_MediaPause) if state == QMediaPlayer.PlayingState else self.style().standardIcon(QStyle.SP_MediaPlay)
        self.ui.btnPause.setIcon(icon)

    # 進度條
    def position_changed(self, position):
        self.slideVideo.setValue(position)

    # 進度條移動範圍
    def duration_changed(self, duration):
        self.slideVideo.setRange(0, duration)

    # 連接影片與伸展操視窗
    def handle_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            sd.choose(videoId-1)

    # 播放鍵按下去後的影片處理
    def play_video(self):
        if (self.mediaPlayer.state() == QMediaPlayer.PlayingState):
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    # 進度條與影片進度的關聯
    def set_position(self, position):
        self.mediaPlayer.setPosition(position)

#番茄鐘長短時設定
class WorkTimeDialog(QDialog):
    def __init__(self, time_setting, parent=None):
        super(WorkTimeDialog, self).__init__(parent)
        self.setWindowTitle("設定工作和休息時間")
        self.work_time, self.short_rest_time, self.long_rest_time = time_setting
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 第一個標題及對應的上下按鈕
        work_label = QLabel("請輸入工作時間（分鐘）:")
        self.work_spinbox = QSpinBox()
        self.work_spinbox.setMinimum(1)
        self.work_spinbox.setMaximum(60)
        self.work_spinbox.setValue(self.work_time)

        layout.addWidget(work_label)
        layout.addWidget(self.work_spinbox)

        # 第二個標題及對應的上下按鈕
        rest_label = QLabel("請輸入短休息時間（分鐘）:")
        self.short_rest_spinbox = QSpinBox()
        self.short_rest_spinbox.setMinimum(1)
        self.short_rest_spinbox.setMaximum(15)
        self.short_rest_spinbox.setValue(self.short_rest_time)

        layout.addWidget(rest_label)
        layout.addWidget(self.short_rest_spinbox)
        
        # 第三個標題及對應的上下按鈕
        rest_label = QLabel("請輸入長休息時間（分鐘）:")
        self.long_rest_spinbox = QSpinBox()
        self.long_rest_spinbox.setMinimum(1)
        self.long_rest_spinbox.setMaximum(40)
        self.long_rest_spinbox.setValue(self.long_rest_time)

        layout.addWidget(rest_label)
        layout.addWidget(self.long_rest_spinbox)

        # 按鈕佈局
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        self.setLayout(layout)

# Windows 通知欄提醒
class WinNotify(QThread):
    def __init__(self, parent = None):
        super(WinNotify, self).__init__(parent)
        self.parent = parent
        self.notify = ToastNotifier()
        self.working = True
 
    def __del__(self):
        self.working = False
        self.wait()

    def run(self):
        self.show_toast()
    
    def show_toast(self):
        # TODO 該如何傳遞要顯示的訊息
        notifyHead = "番茄鐘-該休息了"
        notifyText = "您已工作了300分鐘,該休息了"
        notifyIcon = "img/tomato.png"
        self.notify.show_toast(f"{notifyHead}", f"{notifyText}", duration=5, threaded=True, icon_path=notifyIcon)
