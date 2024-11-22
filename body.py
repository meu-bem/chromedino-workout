import mediapipe as mp
import cv2

# Paths
video_path = 0

# Mediapipe setup
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Initialize Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def get_body_position(landmarks):
    # Check if landmarks are available
    if not landmarks:
        return "No landmarks detected"

    if len(landmarks) < mp_pose.PoseLandmark.RIGHT_KNEE.value:
        return 'Something weird'

    print(len(landmarks))
    print(mp_pose.PoseLandmark.RIGHT_KNEE.value)

    # Get the positions of important landmarks (hips and knees)
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]

    # Calculate the knee angle (simplified as the vertical distance from hips to knees)
    knee_angle = (left_knee.y - left_hip.y + right_knee.y - right_hip.y) / 2  # Approximation

    # Determine the movement based on the knee and hip positions
    if knee_angle < 0.23:
        return "Squatting"
    return "Standing"

def check_jump(landmarks, previous_position):
    # Check if landmarks are available
    if not landmarks or len(landmarks) < mp_pose.PoseLandmark.LEFT_HIP.value:
        return "No landmarks detected", previous_position

    # Track the change in vertical position (e.g., based on pelvis position)
    pelvis_y = landmarks[mp_pose.PoseLandmark.LEFT_HIP].y  # You can average left and right hip

    if previous_position is None:
        return None, pelvis_y  # On first frame, just return position

    # Check for upward movement indicating a jump
    if pelvis_y - previous_position > 0.016:
        return "Jumping", pelvis_y
    return "Not Jumping", pelvis_y

# Configure Pose Landmarker
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.IMAGE
)

# OpenCV VideoCapture
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

previous_position = None

# Create PoseLandmarker instance
with PoseLandmarker.create_from_options(options) as landmarker:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to RGB (OpenCV loads images in BGR)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create a Mediapipe Image from the frame
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Perform pose detection
        try:
            pose_landmarker_result = landmarker.detect(mp_image)
        except ValueError as e:
            print(f"Error during pose detection: {e}")
            continue

        # Visualize the landmarks on the frame
        if pose_landmarker_result.pose_landmarks:
            for landmark in pose_landmarker_result.pose_landmarks[0]:  # Iterate over landmarks
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), radius=5, color=(0, 255, 0), thickness=-1)

            position = get_body_position(pose_landmarker_result.pose_landmarks[0])
            movement, previous_position = check_jump(pose_landmarker_result.pose_landmarks[0], previous_position)

            print(f"Current position: {position}, Movement: {movement}")

        # Display the processed frame
        cv2.imshow("Pose Landmarks", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
            break

# Release resources
cap.release()
cv2.destroyAllWindows()
