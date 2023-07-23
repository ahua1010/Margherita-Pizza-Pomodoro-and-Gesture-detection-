import cv2
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates as denormalize_coordinates

class eye_detect():
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh 
        # 並標記左眼對應的點
        self.all_left_eye_idxs = list(self.mp_face_mesh.FACEMESH_LEFT_EYE)
        # 壓平並刪除重複項
        self.all_left_eye_idxs = set(np.ravel(self.all_left_eye_idxs)) 

        # 右眼對應的標誌點
        self.all_right_eye_idxs = list(self.mp_face_mesh.FACEMESH_RIGHT_EYE)
        self.all_right_eye_idxs = set(np.ravel(self.all_right_eye_idxs))

        # 組合繪圖 - 雙眼的標誌點
        self.all_idxs = self.all_left_eye_idxs.union(self.all_right_eye_idxs)

        # 所選12個點：P1、P2、P3、P4、P5、P6
        self.chosen_left_eye_idxs  = [362, 385, 387, 263, 373, 380]
        self.chosen_right_eye_idxs = [33,  160, 158, 133, 153, 144]
        self.all_chosen_idxs = self.chosen_left_eye_idxs + self.chosen_right_eye_idxs

        # B: 計算用戶似乎要瞌睡的幀數（半閉眼睛）
        self.drowsy_frames = 0
        
    def run(self, ret, frame):
        if not ret and frame:
            return frame

        # 獲取當前幀並收集圖像信息
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_h, img_w = frame.shape[:2]

        with self.mp_face_mesh.FaceMesh(
            max_num_faces=1,       # 一次偵測最多幾個人臉
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as face_mesh:
            # D: 收集mediapipe結果
            results = face_mesh.process(rgb_frame)

            # 如果檢測可用
            if results.multi_face_landmarks:

                all_landmarks = np.array([np.multiply([p.x, p.y], [img_w, img_h]).astype(int) for p in results.multi_face_landmarks[0].landmark])
                
                # G: 右眼和左眼標誌
                right_eye = all_landmarks[self.chosen_right_eye_idxs]
                left_eye = all_landmarks[self.chosen_left_eye_idxs]
                
                # H: 僅在圖像上繪製眼睛的標誌
                cv2.polylines(frame, [left_eye], True, (0,255,0), 1, cv2.LINE_AA)
                cv2.polylines(frame, [right_eye], True, (0,255,0), 1, cv2.LINE_AA) 

                # 迭代每張臉的檢測。 這裡，我們有 max_num_faces=1，所以只執行一次迭代
                for face_id, face_landmarks in enumerate(results.multi_face_landmarks):

                    landmarks = face_landmarks.landmark
                    EAR = self.calculate_avg_ear(landmarks, self.chosen_left_eye_idxs, self.chosen_right_eye_idxs, img_w, img_h)
                    if (EAR <= 0.15):
                        self.drowsy_frames += 1
                    else:
                        self.drowsy_frames = 0

                # L: 如果 count 大於 k，則表示該人昏昏欲睡的時間超過 k 幀
                if (self.drowsy_frames > 100):
                    cv2.putText(img=frame, text='ALERT', fontFace=0, org=(200, 300), fontScale=3, color=(0, 255, 0), thickness = 3)
                    
        return frame
    
    def distance(self, point_1, point_2):
        """計算兩點之間的 l2-範數"""
        dist = sum([(i - j) ** 2 for i, j in zip(point_1, point_2)]) ** 0.5
        return dist

    def get_ear(self, landmarks, refer_idxs, frame_width, frame_height):
        """
        計算一隻眼睛的眼睛縱橫比
        
        """
        try:
            # 計算水平線之間的歐氏距離
            coords_points = []
            for i in refer_idxs:
                lm = landmarks[i]
                coord = denormalize_coordinates(lm.x, lm.y, frame_width, frame_height)
                coords_points.append(coord)
    
            # 眼睛地標 (x, y) 坐標
            P2_P6 = self.distance(coords_points[1], coords_points[5])
            P3_P5 = self.distance(coords_points[2], coords_points[4])
            P1_P4 = self.distance(coords_points[0], coords_points[3])
    
            # 計算眼睛長寬比
            ear = (P2_P6 + P3_P5) / (2.0 * P1_P4)
    
        except:
            ear = 0.0
            coords_points = None
    
        return ear, coords_points

    def calculate_avg_ear(self, landmarks, left_eye_idxs, right_eye_idxs, img_w, img_h):
        # Calculate Eye aspect ratio 
        left_ear,  _ = self.get_ear(landmarks, left_eye_idxs,  img_w, img_h)
        right_ear, _ = self.get_ear(landmarks, right_eye_idxs, img_w, img_h)

        Avg_EAR = (left_ear + right_ear) / 2
        return Avg_EAR

    def open_len(self, arr):
        y_arr = []

        for _,y in arr:
            y_arr.append(y)

        min_y = min(y_arr)
        max_y = max(y_arr)

        return max_y - min_y 
