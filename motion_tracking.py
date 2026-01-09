import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time

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
left_wrist_height = 0.5
right_wrist_height = 0.5

# Variables to share specific limb states for the Bird
left_arm_up = False
right_arm_up = False


def result_callback(result: PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    latest_result = result


def check_lateral_raise_form(pose_landmarks):
    global arms_raised, lateral_raise_count, incorrect_form_detected, one_arm_raised_time
    global left_arm_up, right_arm_up, left_wrist_height, right_wrist_height

    if len(pose_landmarks) < 17:
        return

    left_shoulder = pose_landmarks[11]
    right_shoulder = pose_landmarks[12]
    left_wrist = pose_landmarks[15]
    right_wrist = pose_landmarks[16]

    # Check if wrists are above shoulders (Y coordinate is smaller when higher)
    left_raised = left_wrist.y < left_shoulder.y
    right_raised = right_wrist.y < right_shoulder.y

    # Export these for the UI to use
    left_arm_up = left_raised
    right_arm_up = right_raised
    left_wrist_height = left_wrist.y
    right_wrist_height = right_wrist.y

    both_raised = left_raised and right_raised

    # Form logic (Asymmetry check)
    if (left_raised and not right_raised) or (right_raised and not left_raised):
        if one_arm_raised_time is None:
            one_arm_raised_time = time.time()
        elif time.time() - one_arm_raised_time > FORM_CHECK_DELAY:
            incorrect_form_detected = True
    else:
        one_arm_raised_time = None
        # Only clear incorrect form if we fix it (both up or both down)
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


def main():
    # Setup MediaPipe
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=result_callback)

    cap = cv2.VideoCapture(0)
    # Set low resolution for speed (analysis doesn't need 4k)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Tracking started in background...")

    with PoseLandmarker.create_from_options(options) as landmarker:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            frame_timestamp_ms = int(time.time() * 1000)
            landmarker.detect_async(mp_image, frame_timestamp_ms)

            # Process logic
            if latest_result and latest_result.pose_landmarks:
                for pose_landmarks in latest_result.pose_landmarks:
                    check_lateral_raise_form(pose_landmarks)

            # NOTE: No cv2.imshow here! This keeps it hidden.

            # Small sleep to prevent CPU hogging
            time.sleep(0.01)

    cap.release()


if __name__ == "__main__":
    main()