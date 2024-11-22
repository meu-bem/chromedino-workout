import mediapipe as mp
import cv2
import asyncio
import websockets
import json

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
    if not landmarks:
        return "No landmarks detected"

    if len(landmarks) < mp_pose.PoseLandmark.RIGHT_KNEE.value:
        return 'Something weird'

    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]

    knee_angle = (left_knee.y - left_hip.y + right_knee.y - right_hip.y) / 2

    print(knee_angle)
    if knee_angle < 0.13:
        return "Squatting"
    return "Standing"

def check_jump(landmarks, previous_position):
    if not landmarks or len(landmarks) < mp_pose.PoseLandmark.LEFT_HIP.value:
        return "No landmarks detected", previous_position

    pelvis_y = landmarks[mp_pose.PoseLandmark.LEFT_HIP].y

    if previous_position is None:
        return None, pelvis_y

    if pelvis_y - previous_position > 0.017:
        return "Jumping", pelvis_y
    return "Not Jumping", pelvis_y

async def pose_websocket(websocket, path):
    # OpenCV VideoCapture
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    previous_position = None

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.IMAGE
    )

    # Create PoseLandmarker instance
    with PoseLandmarker.create_from_options(options) as landmarker:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

            try:
                pose_landmarker_result = landmarker.detect(mp_image)
            except ValueError as e:
                print(f"Error during pose detection: {e}")
                continue

            if pose_landmarker_result.pose_landmarks:
                position = get_body_position(pose_landmarker_result.pose_landmarks[0])
                movement, previous_position = check_jump(pose_landmarker_result.pose_landmarks[0], previous_position)

                data = {
                    'current_position': position,
                    'movement': movement
                }

                # Send data as JSON through WebSocket
                await websocket.send(json.dumps(data))

            # Display the processed frame (optional for debugging)
            cv2.imshow("Pose Landmarks", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

# Start WebSocket server
start_server = websockets.serve(pose_websocket, "localhost", 8765)

print("WebSocket server started at ws://localhost:8765")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()