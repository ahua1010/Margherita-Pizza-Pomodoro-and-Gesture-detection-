import cv2
import numpy as np
import time
import concurrent.futures
from . import PoseModule as pm
import pygame

pygame.mixer.init()  # 初始化音效模組

# 建立 Stretch 類別，用於偵測特定動作的程式邏輯
class Stretch():
    def __init__(self, target_img):
        self.comparison = pm.poseDetector()  # 姿勢偵測器，用於比較參考圖片的姿勢
        self.detector = pm.poseDetector()     # 姿勢偵測器，用於偵測物件的姿勢
        self.target_img = self.comparison.findPose(target_img, False)  # 找出參考圖片中的人體姿勢
        self.comparison.findPosition(self.target_img, False)  # 找出參考圖片中各關節的位置

        self.ptime = 0  # 上次計時的時間
        self.total_time = 0  # 總共持續的時間
        self.drawList = []  # 儲存繪製的資訊

    # 偵測特定動作是否達到標準
    def stretchDetect(self, object_img, offset, allow_angle, length, x1, x2, x3, np):
        object_img = self.detector.findPose(object_img, False)  # 偵測物件的姿勢
        lmList = self.detector.findPosition(object_img, False)  # 找出物件中各關節的位置

        per = False  # 預設判斷為未達標
        if len(lmList) != 0:  # 若物件中有偵測到關節
            object_angle = self.detector.findAngle(x1, x2, x3)  # 計算物件角度
            target_angle = self.comparison.findAngle(x1, x2, x3) - offset  # 計算參考角度（可調整偏移）

            gap = abs(object_angle - target_angle)  # 計算兩角度的差距
            gap = 360 - gap if gap > 180 else gap  # 處理差距超過180度的情況

            per = gap <= allow_angle  # 判斷差距是否在允許範圍內
            color = (0, 255, 0) if per else (13, 23, 227)  # 設定顏色（達標為綠色，未達標為藍色）
            object_img = self.detector.drawAngle(object_img, x1, x2, x3, np, target_angle, length, color)  # 繪製角度資訊
        
        return per, object_img  # 回傳是否達標以及繪製的影像

    # 繪製持續時間
    def drawTime(self, img, *args):
        for i in args:
            if not i:
                cv2.rectangle(img, (0, 650), (200, 715), (28, 28, 28), cv2.FILLED)
                cv2.putText(img, str(round(self.total_time, 1))+" s", (7, 703), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                self.ptime = time.time()
                return img

        if self.ptime:
            self.total_time += time.time() - self.ptime
        self.ptime = time.time()

        cv2.rectangle(img, (0, 650), (200, 715), (28, 28, 28), cv2.FILLED)
        cv2.putText(img, str(round(self.total_time, 1))+" s", (7, 703), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
        
        return img

# 播放影片的函式
def playMp4(name, filePath, skip):
    cap = cv2.VideoCapture(filePath)  # 開啟影片檔案
    fps = cap.get(cv2.CAP_PROP_FPS)  # 取得影片的幀率

    while cap.isOpened():
        ret, frame = cap.read()  # 讀取一幀影像
        if not ret:
            break
        
        frame = cv2.resize(frame,(1280,720))  # 調整影像大小為 1280x720

        key = cv2.waitKeyEx(int(1000 / fps)) & 0xff  # 計算按鍵等待時間
        # 若按下空白鍵，執行特定動作
        if key == ord(" "):
            x, y = 580, 340
            width, height = 25, 80
            left_rectangle_x = x + width
            cv2.rectangle(frame, (left_rectangle_x, y), (left_rectangle_x + width, y + height), (211, 211, 211), -1)
            right_rectangle_x = left_rectangle_x +  2*width
            cv2.rectangle(frame, (right_rectangle_x, y), (right_rectangle_x + width, y + height), (211, 211, 211), -1)
            cv2.imshow(name, frame)
            pause_music()  # 暫停音樂
            cv2.waitKey(0)
            unpause_music()  # 恢復音樂播放
        
        # 若按下左方向鍵，倒退影片幾幀
        if key == ord(','):
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) - 100)
        # 若按下右方向鍵，前進影片幾幀
        if key == ord('.'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) + 100)
        # 若按下 'Q' 鍵或 'q' 鍵，中斷影片播放
        if skip and (key == ord('Q') or key == ord("q") or key == 27):
            break
        # 若影片視窗不可見，停止音樂並關閉視窗
        if cv2.getWindowProperty('Stretching!',cv2.WND_PROP_VISIBLE) < 1:
            stop_music()
            cv2.destroyWindow('Stretching!')

        cv2.imshow(name, frame)

        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 影片播放完畢後回到開始位置
            break
    return cap  # 回傳影片物件


# 播放音樂的函式
def music_play(file, n):
    pygame.mixer.music.load(file)  # 載入音樂檔案
    pygame.mixer.music.play(n)  # 播放音樂
 
def pause_music():
    pygame.mixer.music.pause()  # 暫停音樂
 
def unpause_music():
    pygame.mixer.music.unpause()  # 恢復音樂播放
 
def stop_music():
    pygame.mixer.music.stop()  # 停止音樂播放
 
def skip_music(seconds):
    pygame.mixer.music.set_pos(seconds)  # 跳轉音樂播放位置


# 開啟攝像頭的函式，放在獨立的執行緒中執行
def open_camera():
    global cap1
    cap1 = cv2.VideoCapture(0)  # 開啟攝像頭
    if not cap1.isOpened():
        print("無法開啟你的鏡頭")
        exit()

def choose(video_id):
    cv2.namedWindow('Stretching!', cv2.WINDOW_KEEPRATIO)  # 建立視窗

    # 定義多組動作
    actions = [
        ("./stretch/img/mp4_1.png", "./stretch/title/mp4_1.mp4", "./stretch/example_video/mp4_1.mp4", [
            (-10, 35,   1, 11, 13, 15, True),
            ( 10, 35,   1, 12, 14, 16, True),
            ( 20, 25, 0.3, 23, 11, 13, False),
            (-20, 25, 0.3, 24, 12, 14, False)
        ]),
        ("./stretch/img/mp4_2.png", "./stretch/title/mp4_2.mp4", "./stretch/example_video/mp4_2.mp4", [
            (0, 40, 1, 14, 16, 13, True),
            (30, 20, 1, 11, 13, 15, True)
        ]),
        ("./stretch/img/mp4_3.png", "./stretch/title/mp4_4.mp4", "./stretch/example_video/mp4_3.mp4", [
            (-10, 20, 1, 12, 14, 16, True),
            (0, 20, 0.3, 24, 12, 14, False)
        ]),
        ("./stretch/img/mp4_4.png", "./stretch/title/mp4_3.mp4", "./stretch/example_video/mp4_4.mp4", [
            (0, 20, 1, 11, 13, 15, True),
            (0, 20, 0.3, 23, 11, 13, False)
        ]),
        ("./stretch/img/mp4_5.png", "./stretch/title/mp4_6.mp4", "./stretch/example_video/mp4_5.mp4", [
            (0, 35, 1, 13, 15, 12, True)
        ]),
        ("./stretch/img/mp4_6.png", "./stretch/title/mp4_5.mp4", "./stretch/example_video/mp4_6.mp4", [
            (20, 35, 1, 14, 16, 11, True)
        ])
    ]
    open_camera()  # 開啟攝像頭
    music_play("./stretch/sound/bgm.wav", -1)  # 播放背景音樂

    # title = playMp4('Stretching!', "title/mp4_0.mp4", False)  # 播放標題影片
    # title.release()  # 釋放影片物件
    
    action = actions[video_id]
    #for action in actions:
    stretcher =  Stretch(cv2.imread(action[0]))  # 創建 Stretch 物件並載入參考圖片
    #title = playMp4('Stretching!',action[1], False)  # 播放動作標題影片
    #cap2 = playMp4('Stretching!', action[2], True)  # 播放範例影片
    cap2 = cv2.VideoCapture(action[2])
    #open_camera_future.result()  # 等待攝像頭開啟完成

    # 檢查影片是否成功開啟
    # if not title.isOpened():
    #     print("標題影片", action[1], "無法開啟")
    #     exit()
    if not cap2.isOpened():
        print("範例影片", action[2], "無法開啟")
        exit()
    # title.release()  # 釋放影片物件
    
    done = False
    while True:
        ret1, img = cap1.read()  # 讀取攝像頭影像
        ret2, v_img = cap2.read()  # 讀取範例影片影像
        img = cv2.flip(img, 1)  # 鏡像翻轉影像

        # 調整攝像頭影像大小
        origin_width = img.shape[1]
        new_width = int(origin_width / img.shape[0] * 720)
        img = cv2.resize(img, (new_width, 720), interpolation=cv2.INTER_CUBIC)
        gap = int((1280 - new_width) * 0.5)
        img = cv2.copyMakeBorder(img, 0, 0, gap, gap,cv2.BORDER_CONSTANT, value=(255,255,255))

        v_img = cv2.resize(v_img, (427, 240))  # 調整範例影片大小
        if cap2.get(cv2.CAP_PROP_POS_FRAMES) == cap2.get(cv2.CAP_PROP_FRAME_COUNT):
            cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 影片播放完畢後回到開始位置
        
        success = []
        for params in action[3]:
            per, img = stretcher.stretchDetect(img, *params)  # 偵測特定動作
            success.append(per)  # 將是否達標的結果加入列表

        img = stretcher.drawTime(img, *success)  # 繪製持續時間和結果
        img[0:240, 853:1280] = v_img  # 將範例影片加入到主畫面中
        cv2.rectangle(img, (853, 0), (1280, 240), (255, 255, 255), 5)  # 繪製邊框
        cv2.imshow('Stretching!', img)  # 顯示畫面

        key = cv2.waitKey(1) & 0xFF
        if key == ord('Q') or key == ord('q') or stretcher.total_time >= 5:  # 按下 'q' 鍵或達到一定時間後結束
            if stretcher.total_time >= 5:
                done = True
            break
        # if cv2.getWindowProperty('Stretching!', cv2.WND_PROP_VISIBLE) < 10:
        #     cv2.destroyWindow('Stretching!')  # 若視窗不可見，關閉視窗
        #     break
    hint = pygame.mixer.Sound("./stretch/sound/hint.wav")
    hint.play()  # 播放提示音效
    cap2.release()  # 釋放範例影片物件


    cap1.release()  # 釋放攝像頭物件
    stop_music()  # 停止音樂播放
    
    cv2.destroyAllWindows()  # 關閉視窗
    return done
# if __name__ == "__main__":
#     concurrent.futures.ThreadPoolExecutor().submit(choose(1))  # 執行主程式
