import cv2
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates as denormalize_coordinates

def distance(point_1, point_2):
    """Calculate l2-norm between two points"""
    dist = sum([(i - j) ** 2 for i, j in zip(point_1, point_2)]) ** 0.5
    return dist

def get_ear(landmarks, refer_idxs, frame_width, frame_height):
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
        P2_P6 = distance(coords_points[1], coords_points[5])
        P3_P5 = distance(coords_points[2], coords_points[4])
        P1_P4 = distance(coords_points[0], coords_points[3])
 
        # Compute the eye aspect ratio
        ear = (P2_P6 + P3_P5) / (2.0 * P1_P4)
 
    except:
        ear = 0.0
        coords_points = None
 
    return ear, coords_points

def calculate_avg_ear(landmarks, left_eye_idxs, right_eye_idxs, image_w, image_h):
    # Calculate Eye aspect ratio 
    left_ear,  _ = get_ear(landmarks, left_eye_idxs,  img_w, img_h)
    right_ear, _ = get_ear(landmarks, right_eye_idxs, img_w, img_h)

    Avg_EAR = (left_ear + right_ear) / 2
    return Avg_EAR

def open_len(arr):
    y_arr = []

    for _,y in arr:
        y_arr.append(y)

    min_y = min(y_arr)
    max_y = max(y_arr)

    return max_y - min_y


# MAIN
mp_face_mesh = mp.solutions.face_mesh

# Landmark points corresponding to left eye
all_left_eye_idxs = list(mp_face_mesh.FACEMESH_LEFT_EYE)
# flatten and remove duplicates
all_left_eye_idxs = set(np.ravel(all_left_eye_idxs)) 

# Landmark points corresponding to right eye
all_right_eye_idxs = list(mp_face_mesh.FACEMESH_RIGHT_EYE)
all_right_eye_idxs = set(np.ravel(all_right_eye_idxs))

# Combined for plotting - Landmark points for both eye
all_idxs = all_left_eye_idxs.union(all_right_eye_idxs)

# The chosen 12 points:   P1,  P2,  P3,  P4,  P5,  P6
chosen_left_eye_idxs  = [362, 385, 387, 263, 373, 380]
chosen_right_eye_idxs = [33,  160, 158, 133, 153, 144]
all_chosen_idxs = chosen_left_eye_idxs + chosen_right_eye_idxs

# handle of the webcam
cap = cv2.VideoCapture(0)

# Mediapipe parametes
with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as face_mesh:

    # B: count how many frames the user seems to be going to nap (half closed eyes)
    drowsy_frames = 0

    while True:

        # get every frame from the web-cam
        ret, frame = cap.read()
        if not ret:
            break

        # Get the current frame and collect the image information
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_h, img_w = frame.shape[:2]

        # D: collect the mediapipe results
        results = face_mesh.process(rgb_frame)

        # If detections are available.
        if results.multi_face_landmarks:

            all_landmarks = np.array([np.multiply([p.x, p.y], [img_w, img_h]).astype(int) for p in results.multi_face_landmarks[0].landmark])
            
            # G: right and left eye landmarks
            right_eye = all_landmarks[chosen_right_eye_idxs]
            left_eye = all_landmarks[chosen_left_eye_idxs]
            
            # H: draw only landmarks of the eyes over the image
            cv2.polylines(frame, [left_eye], True, (0,255,0), 1, cv2.LINE_AA)
            cv2.polylines(frame, [right_eye], True, (0,255,0), 1, cv2.LINE_AA) 

            # Iterate over detections of each face. Here, we have max_num_faces=1, so only one iteration is performed.
            for face_id, face_landmarks in enumerate(results.multi_face_landmarks):

                landmarks = face_landmarks.landmark
                EAR = calculate_avg_ear(landmarks, chosen_left_eye_idxs, chosen_right_eye_idxs, img_w, img_h)
                if (EAR <= 0.15):
                    drowsy_frames += 1
                else:
                    drowsy_frames = 0

            # L: if count is above k, that means the person has drowsy eyes for more than k frames.
            if (drowsy_frames > 100):
                cv2.putText(img=frame, text='ALERT', fontFace=0, org=(200, 300), fontScale=3, color=(0, 255, 0), thickness = 3)
                

        cv2.imshow('img', frame)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()





