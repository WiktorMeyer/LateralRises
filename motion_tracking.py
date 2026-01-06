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

# Global variable to store the latest result
latest_result = None

# Lateral raise counter variables
lateral_raise_count = 0
arms_raised = False  # Track if arms are currently raised


# Create a pose landmarker instance with the live stream mode:
def print_result(result: PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    latest_result = result


options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result)

# Use OpenCV's VideoCapture to start capturing from the webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

print("Starting pose detection. Press 'q' to quit.")

with PoseLandmarker.create_from_options(options) as landmarker:
    frame_count = 0

    while cap.isOpened():
        # Read the latest frame from the camera
        ret, frame = cap.read()

        if not ret:
            print("Error: Failed to capture frame")
            break

        # Convert BGR to RGB (OpenCV uses BGR, MediaPipe uses RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert the frame to a MediaPipe Image object
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Calculate timestamp in milliseconds
        frame_timestamp_ms = int(time.time() * 1000)

        # Send live image data to perform pose landmarking
        landmarker.detect_async(mp_image, frame_timestamp_ms)

        # Check for lateral raises and draw landmarks
        if latest_result and latest_result.pose_landmarks:
            for pose_landmarks in latest_result.pose_landmarks:
                h, w, c = frame.shape

                # Get relevant landmark positions for lateral raise detection
                # 11 = left shoulder, 12 = right shoulder
                # 15 = left wrist, 16 = right wrist
                if len(pose_landmarks) >= 17:
                    left_shoulder = pose_landmarks[11]
                    right_shoulder = pose_landmarks[12]
                    left_wrist = pose_landmarks[15]
                    right_wrist = pose_landmarks[16]

                    # Check if both wrists are above their respective shoulders
                    left_raised = left_wrist.y < left_shoulder.y
                    right_raised = right_wrist.y < right_shoulder.y
                    both_raised = left_raised and right_raised

                    # State machine for counting reps
                    if both_raised and not arms_raised:
                        # Arms just went up - transition to raised state
                        arms_raised = True
                    elif not both_raised and arms_raised:
                        # Arms just went down - count the rep and transition to lowered state
                        lateral_raise_count += 1
                        arms_raised = False
                        print(f"Lateral Raise Count: {lateral_raise_count}")

                # Draw only specific landmarks (11, 12, 13, 14, 15, 16)
                landmarks_to_draw = [11, 12, 13, 14, 15, 16]
                for idx in landmarks_to_draw:
                    if idx < len(pose_landmarks):
                        landmark = pose_landmarks[idx]
                        cx, cy = int(landmark.x * w), int(landmark.y * h)
                        # Color based on visibility
                        visibility = landmark.visibility if hasattr(landmark, 'visibility') else 1.0
                        if visibility > 0.5:
                            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
                        else:
                            cv2.circle(frame, (cx, cy), 3, (0, 150, 0), -1)

                # Draw only connections between relevant landmarks
                # 11-13 (left shoulder to left elbow)
                # 13-15 (left elbow to left wrist)
                # 12-14 (right shoulder to right elbow)
                # 14-16 (right elbow to right wrist)
                # 11-12 (shoulder to shoulder)
                relevant_connections = [(11, 13), (13, 15), (12, 14), (14, 16), (11, 12)]

                for connection in relevant_connections:
                    start_idx = connection[0]
                    end_idx = connection[1]

                    if start_idx < len(pose_landmarks) and end_idx < len(pose_landmarks):
                        start_landmark = pose_landmarks[start_idx]
                        end_landmark = pose_landmarks[end_idx]

                        # Only draw if both landmarks are visible enough
                        start_vis = start_landmark.visibility if hasattr(start_landmark, 'visibility') else 1.0
                        end_vis = end_landmark.visibility if hasattr(end_landmark, 'visibility') else 1.0

                        if start_vis > 0.5 and end_vis > 0.5:
                            start_point = (int(start_landmark.x * w), int(start_landmark.y * h))
                            end_point = (int(end_landmark.x * w), int(end_landmark.y * h))

                            cv2.line(frame, start_point, end_point, (255, 0, 0), 2)

        # Display lateral raise counter (large and prominent)
        counter_text = f'Lateral Raises: {lateral_raise_count}'
        cv2.putText(frame, counter_text, (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        # Display arms status
        status_text = "Arms: RAISED" if arms_raised else "Arms: LOWERED"
        status_color = (0, 255, 255) if arms_raised else (255, 255, 255)
        cv2.putText(frame, status_text, (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

        # Display the frame
        cv2.imshow('MediaPipe Pose Tracking', frame)

        # Break loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_count += 1

        # Small delay to prevent overwhelming the system
        time.sleep(0.01)

    # Release resources (moved inside with block)
    cap.release()
    cv2.destroyAllWindows()
    print("Pose detection stopped.")