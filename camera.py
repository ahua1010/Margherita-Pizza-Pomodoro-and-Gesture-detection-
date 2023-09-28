import cv2            # 引入 OpenCV 的模組，製作擷取攝影機影像之功能
import sys, time      # 引入 sys 跟 time 模組
import numpy as np    # 引入 numpy 來處理讀取到得影像矩陣

# 引入 PyQt5 模組
# UI 為自行設計的介面程式
from PyQt5 import QtCore, QtGui, QtWidgets
from UI import Ui_MainWindow

class Camera(QtCore.QThread) :
    rawdata = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent = None) :
        """ 初始化
            - 執行 QtCore.QThread 的初始化
            - 建立 cv2 的 VideoCapture 物件
            - 設定屬性來確認狀態
              - self.connect : 連接狀態
              - self.running : 讀取狀態
        """
        # 將父類初始化
        super().__init__(parent)
        # 建 cv2 物件
        self.cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        # 判斷鏡頭正常連接
        if self.cam is None or not self.cam.isOpened() :
            self.connect = False
            self.running = False
        else :
            self.connect = True
            self.running = False

    def run(self) :
        """執行多執行續
            -讀影像
            -傳影像
            -例外處理
        """
        while self.running and self.connect :
            ret, img = self.cam.read()      # 讀影像
            if ret :                        
                self.rawdata.emit(img)      # 傳影像
            else :                          # 例外處理
                print("Warning!!!")
                self.connect = False

    def open(self) :
        """開鏡頭"""
        if self.connect :
            self.running = True

    def stop(self) :
        """暫停鏡頭"""
        if self.connect :
            self.running = True

    def close(self) :
        """關閉鏡頭"""
        if self.connect :
            self.running = False
            time.sleep(1)
            self.cam.release()
