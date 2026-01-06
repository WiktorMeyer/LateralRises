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

# Define pose connections manually (standard pose skeleton)
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)
]

# Global variables
latest_result = None
lateral_raise_count = 0
arms_raised = False
incorrect_form_detected = False
one_arm_raised_time = None  # Track when one arm goes up
FORM_CHECK_DELAY = 0.5  # Wait 0.5 seconds before flagging incorrect form


def result_callback(result: PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    """Callback function to store the latest pose detection result."""
    global latest_result
    latest_result = result


def check_lateral_raise_form(pose_landmarks):
    """
    Check if the user is performing lateral raises correctly.
    Returns: (both_raised, left_raised, right_raised, form_correct)
    """
    global arms_raised, lateral_raise_count, incorrect_form_detected, one_arm_raised_time

    if len(pose_landmarks) < 17:
        return False, False, False, True

    left_shoulder = pose_landmarks[11]
    right_shoulder = pose_landmarks[12]
    left_wrist = pose_landmarks[15]
    right_wrist = pose_landmarks[16]

    # Check if wrists are above shoulders
    left_raised = left_wrist.y < left_shoulder.y
    right_raised = right_wrist.y < right_shoulder.y
    both_raised = left_raised and right_raised

    # Form checking logic
    form_correct = True
    current_time = time.time()

    # If only one arm is raised
    if (left_raised and not right_raised) or (right_raised and not left_raised):
        if one_arm_raised_time is None:
            # Start the timer
            one_arm_raised_time = current_time
        elif current_time - one_arm_raised_time > FORM_CHECK_DELAY:
            # Timer expired, flag incorrect form
            incorrect_form_detected = True
            form_correct = False
    else:
        # Both arms in same state (both up or both down), reset timer
        one_arm_raised_time = None
        if both_raised or (not left_raised and not right_raised):
            incorrect_form_detected = False

    # State machine for counting reps
    if both_raised and not arms_raised:
        # Arms just went up - transition to raised state
        arms_raised = True
        incorrect_form_detected = False  # Reset form flag on new rep
    elif not both_raised and arms_raised:
        # Arms just went down - count the rep only if form was correct
        if not incorrect_form_detected:
            lateral_raise_count += 1
            print(f"Lateral Raise Count: {lateral_raise_count}")
        else:
            print("Rep not counted due to incorrect form")
        arms_raised = False

    return both_raised, left_raised, right_raised, form_correct


def draw_landmarks(frame, pose_landmarks):
    """Draw relevant pose landmarks on the frame."""
    h, w, c = frame.shape
    landmarks_to_draw = [11, 12, 13, 14, 15, 16]

    for idx in landmarks_to_draw:
        if idx < len(pose_landmarks):
            landmark = pose_landmarks[idx]
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            visibility = landmark.visibility if hasattr(landmark, 'visibility') else 1.0

            if visibility > 0.5:
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
            else:
                cv2.circle(frame, (cx, cy), 3, (0, 150, 0), -1)


def draw_connections(frame, pose_landmarks):
    """Draw connections between relevant landmarks."""
    h, w, c = frame.shape
    relevant_connections = [(11, 13), (13, 15), (12, 14), (14, 16), (11, 12)]

    for connection in relevant_connections:
        start_idx, end_idx = connection

        if start_idx < len(pose_landmarks) and end_idx < len(pose_landmarks):
            start_landmark = pose_landmarks[start_idx]
            end_landmark = pose_landmarks[end_idx]

            start_vis = start_landmark.visibility if hasattr(start_landmark, 'visibility') else 1.0
            end_vis = end_landmark.visibility if hasattr(end_landmark, 'visibility') else 1.0

            if start_vis > 0.5 and end_vis > 0.5:
                start_point = (int(start_landmark.x * w), int(start_landmark.y * h))
                end_point = (int(end_landmark.x * w), int(end_landmark.y * h))
                cv2.line(frame, start_point, end_point, (255, 0, 0), 2)


def draw_ui_elements(frame):
    """Draw all UI elements (counter, status, feedback) on the frame."""
    # Display lateral raise counter
    counter_text = f'Lateral Raises: {lateral_raise_count}'
    cv2.putText(frame, counter_text, (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    # Display arms status
    status_text = "Arms: RAISED" if arms_raised else "Arms: LOWERED"
    status_color = (0, 255, 255) if arms_raised else (255, 255, 255)
    cv2.putText(frame, status_text, (10, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

    # Display form feedback if incorrect
    if incorrect_form_detected:
        feedback_text = "INCORRECT FORM: Keep both arms at the same level!"
        cv2.putText(frame, feedback_text, (10, 170),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)


def process_frame(frame):
    """Process a single frame: detect pose, check form, and draw visualizations."""
    if latest_result and latest_result.pose_landmarks:
        for pose_landmarks in latest_result.pose_landmarks:
            # Check form and count reps
            check_lateral_raise_form(pose_landmarks)

            # Draw landmarks and connections
            draw_landmarks(frame, pose_landmarks)
            draw_connections(frame, pose_landmarks)

    # Draw UI elements
    draw_ui_elements(frame)


def initialize_camera():
    """Initialize and return the camera capture object."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        exit()
    return cap


def main():
    """Main function to run the pose tracking application."""
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=result_callback)

    cap = initialize_camera()
    print("Starting pose detection. Press 'q' to quit.")

    with PoseLandmarker.create_from_options(options) as landmarker:
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                print("Error: Failed to capture frame")
                break

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Calculate timestamp
            frame_timestamp_ms = int(time.time() * 1000)

            # Send frame for pose detection
            landmarker.detect_async(mp_image, frame_timestamp_ms)

            # Process and visualize
            process_frame(frame)

            # Display the frame
            cv2.imshow('MediaPipe Pose Tracking', frame)

            # Break on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_count += 1
            time.sleep(0.01)

        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("Pose detection stopped.")


if __name__ == "__main__":
    main()