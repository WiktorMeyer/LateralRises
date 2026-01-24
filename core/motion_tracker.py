import threading

import cv2
import mediapipe as mp
import time

class MotionTracker:
    def __init__(self):
        self.latest_result = None
        self.lateral_raise_count = 0
        self.arms_raised = False
        self.incorrect_form_detected = False
        self.one_arm_raised_time = None
        self.FORM_CHECK_DELAY = 0.5
        self.left_wrist_height = 0.5
        self.right_wrist_height = 0.5
        self.latest_visualized_frame = None
        self.left_arm_up = False
        self.right_arm_up = False
        self.BaseOptions = mp.tasks.BaseOptions
        self.PoseLandmarker = mp.tasks.vision.PoseLandmarker
        self.PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
        self.PoseLandmarkerResult = mp.tasks.vision.PoseLandmarkerResult
        self.VisionRunningMode = mp.tasks.vision.RunningMode
        self.model_path = r'assets/pose_landmarker_heavy.task'

    def result_callback(self, result: mp.tasks.vision.PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        self.latest_result = result

    def check_lateral_raise_form(self, pose_landmarks):

        if len(pose_landmarks) < 17:
            return

        left_shoulder = pose_landmarks[11]
        right_shoulder = pose_landmarks[12]
        left_wrist = pose_landmarks[15]
        right_wrist = pose_landmarks[16]

        DISCOUNT_FACTOR = 1.25

        left_threshold_y = left_shoulder.y * DISCOUNT_FACTOR
        right_threshold_y = right_shoulder.y * DISCOUNT_FACTOR

        # Check if wrists are above shoulders (Y coordinate is smaller when higher)
        left_raised = left_wrist.y < left_threshold_y
        right_raised = right_wrist.y < right_threshold_y

        # Export these for the UI to use (ADD self.!)
        self.left_arm_up = left_raised
        self.right_arm_up = right_raised
        self.left_wrist_height = left_wrist.y
        self.right_wrist_height = right_wrist.y

        both_raised = left_raised and right_raised

        # Form logic (Asymmetry check)
        if (left_raised and not right_raised) or (right_raised and not left_raised):
            if self.one_arm_raised_time is None:
                self.one_arm_raised_time = time.time()
            elif time.time() - self.one_arm_raised_time > self.FORM_CHECK_DELAY:
                self.incorrect_form_detected = True
        else:
            self.one_arm_raised_time = None
            # Only clear incorrect form if we fix it (both up or both down)
            if both_raised or (not left_raised and not right_raised):
                self.incorrect_form_detected = False

        # Rep Counting Logic
        if both_raised and not self.arms_raised:
            self.arms_raised = True
            self.incorrect_form_detected = False
        elif not both_raised and self.arms_raised:
            if not self.incorrect_form_detected:
                self.lateral_raise_count += 1
                print(f"Rep Count: {self.lateral_raise_count}")
            self.arms_raised = False

    def draw_stickman(self, frame, pose_landmarks):
        """Draws the stickman overlay on the OpenCV frame."""
        h, w, c = frame.shape

        # 1. Draw Connections (Lines)
        # Define connections (Shoulders, Arms, Torso)
        connections = [
            (11, 12),  # Shoulders
            (11, 13), (13, 15),  # Left Arm
            (12, 14), (14, 16),  # Right Arm
            (11, 23), (12, 24),  # Torso
            (23, 24)  # Hips
        ]

        for start_idx, end_idx in connections:
            if start_idx < len(pose_landmarks) and end_idx < len(pose_landmarks):
                lm1 = pose_landmarks[start_idx]
                lm2 = pose_landmarks[end_idx]

                # Check visibility
                if hasattr(lm1, 'visibility') and lm1.visibility < 0.5: continue
                if hasattr(lm2, 'visibility') and lm2.visibility < 0.5: continue

                p1 = (int(lm1.x * w), int(lm1.y * h))
                p2 = (int(lm2.x * w), int(lm2.y * h))

                # Draw Thick Blue Line
                cv2.line(frame, p1, p2, (255, 255, 0), 4)

        # 2. Draw Landmarks (Joints)
        relevant_indices = [11, 12, 13, 14, 15, 16]  # Shoulders, Elbows, Wrists
        for idx in relevant_indices:
            if idx < len(pose_landmarks):
                lm = pose_landmarks[idx]
                if hasattr(lm, 'visibility') and lm.visibility < 0.5: continue

                cx, cy = int(lm.x * w), int(lm.y * h)
                # Draw Red Circles for Joints
                cv2.circle(frame, (cx, cy), 8, (0, 0, 255), -1)


    def run(self):
        # Setup MediaPipe
        options = self.PoseLandmarkerOptions(
            base_options=self.BaseOptions(model_asset_path=self.model_path),
            running_mode=self.VisionRunningMode.LIVE_STREAM,
            result_callback=self.result_callback)

        cap = cv2.VideoCapture(0)
        # Set low resolution for speed (analysis doesn't need 4k)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        print("Tracking started in background...")

        with self.PoseLandmarker.create_from_options(options) as landmarker:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break

                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                frame_timestamp_ms = int(time.time() * 1000)
                landmarker.detect_async(mp_image, frame_timestamp_ms)

                # Process logic
                if self.latest_result and self.latest_result.pose_landmarks:
                    for pose_landmarks in self.latest_result.pose_landmarks:
                        self.check_lateral_raise_form(pose_landmarks)
                        # DRAW STICKMAN on the frame
                        self.draw_stickman(frame, pose_landmarks)

                # NOTE: No cv2.imshow here! This keeps it hidden.
                frame = cv2.flip(frame, 1)  # MOVE THIS BEFORE STORING

                # Store this frame so Main Game can access it
                self.latest_visualized_frame = frame

                # Small sleep to prevent CPU hogging
                time.sleep(0.01)

        cap.release()

    def start(self):
        t = threading.Thread(target=self.run, daemon=True)
        t.start()