import cv2
import numpy as np
import time
import concurrent.futures
import PoseModule as pm
import pygame

pygame.mixer.init()
#偵測給定的圖片和目標圖片的角度是否達標 並且畫出來
class Stretch():
    def __init__(self, target_img):
        self.comparison = pm.poseDetector()
        self.detector = pm.poseDetector()
        self.target_img = self.comparison.findPose(target_img, False)
        self.comparison.findPosition(self.target_img, False)

        self.ptime = 0
        self.total_time = 0
        self.drawList = []

    def stretchDetect(self, object_img, offset, allow_angle, length, x1, x2, x3, np):
        object_img = self.detector.findPose(object_img, False)
        lmList = self.detector.findPosition(object_img, False)

        per = False
        if len(lmList) != 0:
            object_angle = self.detector.findAngle(x1, x2, x3)
            target_angle = self.comparison.findAngle(x1, x2, x3) - offset

            gap = abs(object_angle - target_angle)
            gap = 360 - gap if gap > 180 else gap

            per = gap <= allow_angle
            color = (0, 255, 0) if per else (13, 23, 227)
            object_img = self.detector.drawAngle(object_img, x1, x2, x3, np, target_angle, length, color)
        
        return per, object_img

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

# 放影片的
def playMp4(name, filePath, skip):
    cap = cv2.VideoCapture(filePath)
    fps = cap.get(cv2.CAP_PROP_FPS)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.resize(frame,(1280,720))

        key = cv2.waitKeyEx(int(1000 / fps)) & 0xff
        if key == ord(" "):
            x, y = 580, 340
            width, height = 25, 80
            left_rectangle_x = x + width
            cv2.rectangle(frame, (left_rectangle_x, y), (left_rectangle_x + width, y + height), (211, 211, 211), -1)
            right_rectangle_x = left_rectangle_x +  2*width
            cv2.rectangle(frame, (right_rectangle_x, y), (right_rectangle_x + width, y + height), (211, 211, 211), -1)
            cv2.imshow(name, frame)
            pause_music()
            cv2.waitKey(0)
            unpause_music()
        
        #如果按下方向鍵左
        if key == ord(','):
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) - 100)
        if key == ord('.'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) + 100)
        if skip and (key == ord('Q') or key == ord("q") or key == 27):
            break
        # if cv2.getWindowProperty('Stretching!',cv2.WND_PROP_VISIBLE) < 1:
        #     stop_music()
        #     cv2.destroyWindow('Stretching!')

        cv2.imshow(name, frame)

        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            break
    return cap

# 播放音樂
def music_play(file, n):
    pygame.mixer.music.load(file)
    pygame.mixer.music.play(n)
 
def pause_music():
    pygame.mixer.music.pause()
 
def unpause_music():
    pygame.mixer.music.unpause()
 
def stop_music():
    pygame.mixer.music.stop()
 
def skip_music(seconds):
    #pos = pygame.mixer.music.get_pos()
    pygame.mixer.music.set_pos(seconds)

# 速度太慢 獨立出去一個線程
def open_camera():
    global cap1
    cap1 = cv2.VideoCapture(0)
    if not cap1.isOpened():
        print("無法開啟你的鏡頭")
        exit()

def main():
    cv2.namedWindow('Stretching!', cv2.WINDOW_KEEPRATIO)
    
    actions = [
        ("img/mp4_1.png", "title/mp4_1.mp4", "example_video/mp4_1.mp4", [
            (-10, 35,   1, 11, 13, 15, True),
            ( 10, 35,   1, 12, 14, 16, True),
            ( 20, 25, 0.3, 23, 11, 13, False),
            (-20, 25, 0.3, 24, 12, 14, False)
        ]),
        ("img/mp4_2.png", "title/mp4_2.mp4", "example_video/mp4_2.mp4", [
            (0, 40, 1, 14, 16, 13, True),
            (30, 20, 1, 11, 13, 15, True)
        ]),
        ("img/mp4_3.png", "title/mp4_4.mp4", "example_video/mp4_3.mp4", [
            (-10, 20, 1, 12, 14, 16, True),
            (0, 20, 0.3, 24, 12, 14, False)
        ]),
        ("img/mp4_4.png", "title/mp4_3.mp4", "example_video/mp4_4.mp4", [
            (0, 20, 1, 11, 13, 15, True),
            (0, 20, 0.3, 23, 11, 13, False)
        ]),
        ("img/mp4_5.png", "title/mp4_6.mp4", "example_video/mp4_5.mp4", [
            (0, 35, 1, 13, 15, 12, True)
        ]),
        ("img/mp4_6.png", "title/mp4_5.mp4", "example_video/mp4_6.mp4", [
            (20, 35, 1, 14, 16, 11, True)
        ])
    ]

    open_camera_future = concurrent.futures.ThreadPoolExecutor().submit(open_camera)
    music_play("sound/bgm.wav", -1)

    title = playMp4('Stretching!', "title/mp4_0.mp4", False)
    title.release()
    
    for action in actions:
        stretcher =  Stretch(cv2.imread(action[0]))
        title = playMp4('Stretching!',action[1], False)
        cap2 = playMp4('Stretching!', action[2], True)
        open_camera_future.result()

        if not title.isOpened():
            print("標題影片", action[1], "無法開啟")
            exit()
        if not cap2.isOpened():
            print("範例影片", action[2], "無法開啟")
            exit()
        title.release()

        while True:
            ret1, img = cap1.read()
            ret2, v_img = cap2.read()
            img = cv2.flip(img, 1)

            origin_width = img.shape[1]
            new_width = int(origin_width / img.shape[0] * 720)
            img = cv2.resize(img, (new_width, 720), interpolation=cv2.INTER_CUBIC)  # 等比例放大尺寸
            gap = int((1280 - new_width) * 0.5)
            img = cv2.copyMakeBorder(img, 0, 0, gap, gap,cv2.BORDER_CONSTANT, value=(255,255,255))

            v_img = cv2.resize(v_img, (427, 240))  # 縮小尺寸
            if cap2.get(cv2.CAP_PROP_POS_FRAMES) == cap2.get(cv2.CAP_PROP_FRAME_COUNT):
                cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            success = []
            for params in action[3]:
                per, img = stretcher.stretchDetect(img, *params)
                success.append(per) # 將布林值放入列表中

            img = stretcher.drawTime(img, *success)
            img[0:240, 853:1280] = v_img
            cv2.rectangle(img, (853, 0), (1280, 240), (255, 255, 255), 5)
            cv2.imshow('Stretching!', img)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('Q') or key == ord('q') or stretcher.total_time >= 1:  # 按下 'q' 鍵退出迴圈
                break
            if cv2.getWindowProperty('Stretching!', cv2.WND_PROP_VISIBLE) < 10:
                cv2.destroyWindow('Stretching!')
                break
        hint = pygame.mixer.Sound("sound/hint.wav")
        hint.play()
        cap2.release()
    cap1.release()
    stop_music()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()