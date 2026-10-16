import os

import cv2
import numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError:  # pragma: no cover - optional dependency in headless environments
    mp = None
    python = None
    vision = None


class GestureController:
    def __init__(self, width=480, height=360):
        self.width = width
        self.height = height
        self.detector = None
        self._smoothed_points = None

        self.HAND_CONNECTIONS = [
            (0,1), (1,2), (2,3), (3,4),
            (0,5), (5,6), (6,7), (7,8),
            (5,9), (9,10), (10,11), (11,12),
            (9,13), (13,14), (14,15), (15,16),
            (13,17), (0,17), (17,18), (18,19), (19,20)
        ]

        if python is not None and vision is not None:
            model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
            if os.path.exists(model_path):
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.HandLandmarkerOptions(
                    base_options=base_options,
                    num_hands=1,
                    min_hand_detection_confidence=0.4,
                    min_hand_presence_confidence=0.4
                )
                self.detector = vision.HandLandmarker.create_from_options(options)

    def _is_finger_extended(self, pts, tip_idx, mcp_idx):
        pip_idx = tip_idx - 2
        if len(pts) <= max(tip_idx, mcp_idx) or pip_idx <= mcp_idx:
            return False
        mcp = np.asarray(pts[mcp_idx], dtype=np.float32)
        pip = np.asarray(pts[pip_idx], dtype=np.float32)
        tip = np.asarray(pts[tip_idx], dtype=np.float32)
        first_segment = np.linalg.norm(pip - mcp)
        second_segment = np.linalg.norm(tip - pip)
        total_length = first_segment + second_segment
        if total_length == 0:
            return False
        return np.linalg.norm(tip - mcp) >= 0.78 * total_length

    def get_direction_and_action(self, frame, current_direction):
        new_direction = current_direction
        action = None

        frame = cv2.resize(frame, (self.width, self.height))
        h, w, _ = frame.shape

        if self.detector is None or mp is None:
            cv2.putText(frame, f"DIR: {new_direction}", (10, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            return new_direction, action, frame

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        detection_result = self.detector.detect(mp_image)

        if detection_result.hand_landmarks:
            landmarks = detection_result.hand_landmarks[0]
            raw_pts = np.array(
                [(lm.x * w, lm.y * h) for lm in landmarks], dtype=np.float32
            )
            if self._smoothed_points is None:
                self._smoothed_points = raw_pts
            else:
                self._smoothed_points = (
                    0.8 * raw_pts + 0.2 * self._smoothed_points
                )
            pts = [tuple(point.astype(int)) for point in self._smoothed_points]

            if len(pts) >= 21:
                for start_idx, end_idx in self.HAND_CONNECTIONS:
                    cv2.line(frame, pts[start_idx], pts[end_idx], (0, 255, 150), 2)

                for idx, pt in enumerate(pts):
                    color = (255, 255, 0) if idx in [4, 8, 12, 16, 20] else (0, 100, 255)
                    cv2.circle(frame, pt, 4, color, -1)

                index_open = self._is_finger_extended(pts, 8, 5)
                middle_open = self._is_finger_extended(pts, 12, 9)
                ring_open = self._is_finger_extended(pts, 16, 13)
                pinky_open = self._is_finger_extended(pts, 20, 17)

                if index_open and middle_open and not ring_open and not pinky_open:
                    action = "RESTART"
                    cv2.putText(frame, "ACTION: RESTART (PEACE ✌️)", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                elif index_open and not middle_open:
                    pip = pts[6]
                    tip = pts[8]

                    dx = tip[0] - pip[0]
                    dy = tip[1] - pip[1]
                    threshold = max(8, np.hypot(dx, dy) * 0.2)

                    candidate_direction = None
                    if abs(dx) > abs(dy):
                        if dx > threshold:
                            candidate_direction = "RIGHT"
                        elif dx < -threshold:
                            candidate_direction = "LEFT"
                    else:
                        # Image y increases downward: a fingertip above the knuckle has negative dy.
                        if dy < -threshold:
                            candidate_direction = "UP"
                        elif dy > threshold:
                            candidate_direction = "DOWN"

                    if candidate_direction is not None:
                        opposites = {
                            "UP": "DOWN",
                            "DOWN": "UP",
                            "LEFT": "RIGHT",
                            "RIGHT": "LEFT",
                        }
                        if candidate_direction != opposites.get(current_direction):
                            new_direction = candidate_direction

                    cv2.arrowedLine(frame, pip, tip, (0, 255, 255), 3, tipLength=0.3)
                else:
                    self._smoothed_points = None
        else:
            self._smoothed_points = None

        cv2.putText(frame, f"AIM: {new_direction}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"STEER: {new_direction}", (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        return new_direction, action, frame

    def close(self):
        if self.detector is not None:
            self.detector.close()
            self.detector = None
    