import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import numpy as np

model_path = r'pose_landmarker_heavy.task'

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
PoseLandmarkerResult = mp.tasks.vision.PoseLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

# Global variables to share data with main_game.py
latest_result = None
lateral_raise_count = 0
arms_raised = False
incorrect_form_detected = False
one_arm_raised_time = None
FORM_CHECK_DELAY = 0.5

# NEW: Variable to store the visual frame for Pygame to grab
latest_visualized_frame = None


def result_callback(result: PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    latest_result = result


def check_lateral_raise_form(pose_landmarks):
    global arms_raised, lateral_raise_count, incorrect_form_detected, one_arm_raised_time

    if len(pose_landmarks) < 17:
        return

    left_shoulder = pose_landmarks[11]
    right_shoulder = pose_landmarks[12]
    left_wrist = pose_landmarks[15]
    right_wrist = pose_landmarks[16]

    left_raised = left_wrist.y < left_shoulder.y
    right_raised = right_wrist.y < right_shoulder.y
    both_raised = left_raised and right_raised

    # Form logic
    if (left_raised and not right_raised) or (right_raised and not left_raised):
        if one_arm_raised_time is None:
            one_arm_raised_time = time.time()
        elif time.time() - one_arm_raised_time > FORM_CHECK_DELAY:
            incorrect_form_detected = True
    else:
        one_arm_raised_time = None
        if both_raised or (not left_raised and not right_raised):
            incorrect_form_detected = False

    # Rep Counting Logic
    if both_raised and not arms_raised:
        arms_raised = True
        incorrect_form_detected = False
    elif not both_raised and arms_raised:
        if not incorrect_form_detected:
            lateral_raise_count += 1
            print(f"Rep Count: {lateral_raise_count}")
        arms_raised = False


def draw_stickman(frame, pose_landmarks):
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


def main():
    global latest_visualized_frame

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=result_callback)

    cap = cv2.VideoCapture(0)
    # Lower resolution slightly to ensure smooth Pygame rendering
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    with PoseLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            # Process Frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            frame_timestamp_ms = int(time.time() * 1000)
            landmarker.detect_async(mp_image, frame_timestamp_ms)

            # Logic Update
            if latest_result and latest_result.pose_landmarks:
                for pose_landmarks in latest_result.pose_landmarks:
                    check_lateral_raise_form(pose_landmarks)
                    # DRAW STICKMAN on the frame
                    draw_stickman(frame, pose_landmarks)

            # Flip frame horizontally for mirror effect (easier for user)
            frame = cv2.flip(frame, 1)

            # Store this frame so Main Game can access it
            latest_visualized_frame = frame

            # Small sleep to save CPU
            time.sleep(0.01)

    cap.release()


if __name__ == "__main__":
    main()