import cv2
import time, threading
import mediapipe as mp
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates as denormalize_coordinates
import pickle
import numpy as np
import tensorflow as tf
from PyQt5 import QtCore
# from tensorflow import keras

class PoseDetection(QtCore.QThread):
    rawdata = QtCore.pyqtSignal(np.ndarray)  # 建立傳遞信號，需設定傳遞型態為 np.ndarray

    def __init__(self, parent=None, model_file='./pose/model.sav'):
        super().__init__(parent)
        # AI hunchback
        self.model = pickle.load(open(model_file, 'rb'))
        self.mp_pose = mp.solutions.pose
        self.target_lm_idx = [0, 2, 5, 9, 10, 11, 12]
        self.pred = -1

        # AI drowsy
        self.mp_face_mesh = mp.solutions.face_mesh
        # Landmark points corresponding to left eye
        all_left_eye_idxs = list(self.mp_face_mesh.FACEMESH_LEFT_EYE)
        all_left_eye_idxs = set(np.ravel(all_left_eye_idxs)) 
        # Landmark points corresponding to right eye
        all_right_eye_idxs = list(self.mp_face_mesh.FACEMESH_RIGHT_EYE)
        all_right_eye_idxs = set(np.ravel(all_right_eye_idxs))
        # The chosen 12 points:   P1,  P2,  P3,  P4,  P5,  P6
        self.chosen_left_eye_idxs  = [362, 385, 387, 263, 373, 380]
        self.chosen_right_eye_idxs = [33,  160, 158, 133, 153, 144]
        self.drowsy_frames = 0

        # Thread lock
        self.img_lock = threading.Lock()

        # camera
        self.frame_num = 0
        self.cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if self.cam is None or not self.cam.isOpened():
            self.connect = False
            self.running = False
        else:
            self.connect = True
            self.running = False

    def run(self):
        with self.mp_pose.Pose(
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
        ) as self.pose:
         
         with self.mp_face_mesh.FaceMesh(
         max_num_faces=1,
         refine_landmarks=True,
         min_detection_confidence=0.5,
         min_tracking_confidence=0.5
         ) as self.face_mesh:
            
            while self.running and self.connect:
                ret, img = self.cam.read()
                if ret:
                    img = cv2.flip(img, 1)

                    self.thread_hunchbackPredict = threading.Thread(target=self.hunchbackPredict, args=(img,))
                    self.thread_hunchbackPredict.start()
                    
                    self.thread_drawsyPredict = threading.Thread(target=self.drawsyPredict, args=(img,))
                    self.thread_drawsyPredict.start()

                    if   self.pred == 0:
                        img = cv2.putText(img, 'Excellent Posture', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 255, 153), 2, cv2.LINE_AA)
                    elif self.pred == 1:
                        img = cv2.putText(img, 'Okay Posture', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 255, 255), 2, cv2.LINE_AA)
                    elif self.pred == 2:
                        img = cv2.putText(img, 'Bad Posture', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 153, 255), 2, cv2.LINE_AA)
                    elif self.pred == 3:
                        img = cv2.putText(img, 'Terrible Posture', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (51, 51, 255), 2, cv2.LINE_AA)
                    else: 
                        img = cv2.putText(img, 'Start Analyzing', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, ((255, 0, 0)), 2, cv2.LINE_AA)
                    
                    if self.drowsy_frames > 10:
                        img = cv2.putText(img, 'ALERT', fontFace=0, org=(200, 300), fontScale=3, color=(0, 255, 0), thickness = 3)

                    # if self.frame_num == 0:
                    #     self.time_start = time.time()
                    # if self.frame_num >= 0:
                    #     self.frame_num += 1
                    #     self.t_total = time.time() - self.time_start
                    #     if self.frame_num % 100 == 0:
                    #         self.frame_rate = float(self.frame_num) / self.t_total
                    #         print()
                    #         print('FPS: %0.3f frames/sec' % self.frame_rate)
                    #         print()

                    self.thread_drawsyPredict.join()
                    self.thread_hunchbackPredict.join()
                    
                    self.rawdata.emit(img)
                else:
                    print("Warning!!!")
                    self.connect = False

    def hunchbackPredict(self, img):
        self.img_lock.acquire()
        try:
            img.flags.writeable = False
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.pose.process(img)

            if results.pose_landmarks is not None:
                lm_result = []
                for lm_idx in self.target_lm_idx:
                    lm_result.append(results.pose_landmarks.landmark[lm_idx].x)
                    lm_result.append(results.pose_landmarks.landmark[lm_idx].y)
                    lm_result.append(results.pose_landmarks.landmark[lm_idx].z)
                    lm_result.append(results.pose_landmarks.landmark[lm_idx].visibility)
                lm_result = np.array(lm_result)[None, :]
                self.pred = np.argmax(self.model.predict(lm_result, verbose=0)[0])
            else: pass
        finally:
            self.img_lock.release()

    def drawsyPredict(self, img):
        self.img_lock.acquire()
        try:
            img.flags.writeable = False
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_h, img_w = img.shape[:2]
            results = self.face_mesh.process(img)
            if results.multi_face_landmarks:
                for face_id, face_landmarks in enumerate(results.multi_face_landmarks):
                    landmarks = face_landmarks.landmark
                    EAR = self.calculate_avg_ear(landmarks, img_w, img_h)
                    if (EAR <= 0.15):
                        self.drowsy_frames += 1
                    else:
                        self.drowsy_frames = 0
        finally:
            self.img_lock.release()
        
    def calculate_avg_ear(self, landmarks, img_w, img_h):
        # Calculate Eye aspect ratio 
        left_ear,  _ = self.get_ear(landmarks, self.chosen_left_eye_idxs,  img_w, img_h)
        right_ear, _ = self.get_ear(landmarks, self.chosen_right_eye_idxs, img_w, img_h)

        Avg_EAR = (left_ear + right_ear) / 2

        print()
        print("Avg_EAR: ", Avg_EAR)
        print()

        return Avg_EAR
    
    def get_ear(self, landmarks, refer_idxs, frame_width, frame_height):
        """
        Calculate Eye Aspect Ratio for one eye.
    
        Args:
            landmarks: (list) Detected landmarks list
            refer_idxs: (list) Index positions of the chosen landmarks
                                in order P1, P2, P3, P4, P5, P6
            frame_width: (int) Width of captured frame
            frame_height: (int) Height of captured frame
    
        Returns:
            ear: (float) Eye aspect ratio
        """
        try:
            # Compute the euclidean distance between the horizontal
            coords_points = []
            for i in refer_idxs:
                lm = landmarks[i]
                coord = denormalize_coordinates(lm.x, lm.y, frame_width, frame_height)
                coords_points.append(coord)
            # Eye landmark (x, y)-coordinates
            P2_P6 = self.distance(coords_points[1], coords_points[5])
            P3_P5 = self.distance(coords_points[2], coords_points[4])
            P1_P4 = self.distance(coords_points[0], coords_points[3])
            # Compute the eye aspect ratio
            ear = (P2_P6 + P3_P5) / (2.0 * P1_P4)
    
        except:
            ear = 0.0
            coords_points = None

        return ear, coords_points
    
    def distance(self, point_1, point_2):
        """Calculate l2-norm between two points"""
        dist = sum([(i - j) ** 2 for i, j in zip(point_1, point_2)]) ** 0.5
        return dist
    
    def open(self):
        if self.connect:
            self.running = True
    
    def stop(self):
        if self.connect:
            self.running = False

    def close(self):
        if self.connect:
            self.running = False
            time.sleep(1)
            self.cam.release()


if __name__ == "__main__":
    hunchback_detector = PoseDetection()
    hunchback_detector.start()
