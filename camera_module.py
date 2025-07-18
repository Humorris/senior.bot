import cv2
import mediapipe as mp
import time
import math
from gpiozero import Servo
from threading import Thread, Event
import pyttsx3

# Initialize mediapipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

# Parameter settings
ANGLE_TOLERANCE = 15  # ±15 degrees
INIT_TIME = 10        # Stabilization time in seconds
DISTRACTION_LIMIT = 60  # Auto stop after 60 seconds of distraction

# Eye X-axis offset limits
EYE_X_LEFT_LIMIT = 0.40  # Left eye limit
EYE_X_RIGHT_LIMIT = 0.60  # Right eye limit

# Variable initialization
phase = "init"
init_angles = []
init_start = None
goal_angle = None

focus_time = 0.0
distraction_time = 0.0
off_count = 0
prev_in_range = True

# Servo control setup
servo = Servo(18)
servo_stop_event = Event()

tts_engine = pyttsx3.init()
tts_played = False

def servo_move():
    """Move the servo up and down until a stop event is received."""
    while not servo_stop_event.is_set():
        servo.value = 1
        for _ in range(10):  # Check for stop event every 0.1 seconds
            if servo_stop_event.is_set():
                break
            time.sleep(0.1)
        servo.value = -1
        for _ in range(10):
            if servo_stop_event.is_set():
                break
            time.sleep(0.1)
    servo.value = 0  # Stop the motor to avoid jitter

def get_face_angle(landmarks):
    left_eye = landmarks[33]
    right_eye = landmarks[263]
    dx = right_eye.x - left_eye.x
    dy = right_eye.y - left_eye.y
    angle = math.degrees(math.atan2(dy, dx))
    return angle

def is_eye_looking_outside(landmarks):
    left_eye_center_x = (landmarks[133].x + landmarks[33].x) / 2
    right_eye_center_x = (landmarks[362].x + landmarks[263].x) / 2

    if left_eye_center_x < EYE_X_LEFT_LIMIT or right_eye_center_x > EYE_X_RIGHT_LIMIT:
        return True
    return False

def write_status(focus, distraction, offcnt, status_msg):
    if "Focusing" in status_msg:
        stat = "OK"
    elif "Distracted" in status_msg:
        stat = "Distrct"
    elif "No face" in status_msg:
        stat = "NoFace"
    else:
        stat = "Unknown"
    with open("focus_status.txt", "w", encoding="utf-8") as f:
        f.write(f"Fcs:{int(focus)}s Dst:{int(distraction)}s\n")
        f.write(f"Off:{offcnt} Stat:{stat}\n")

servo_thread = None

def initialize_camera():
    print("Please face forward and hold steady for 10 seconds to set focus direction.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to grab frame")
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        status_text = ""
        now = time.time()

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            angle = get_face_angle(landmarks)

            eye_outside = is_eye_looking_outside(landmarks)

            if phase == "init":
                if init_start is None:
                    init_start = now
                    init_angles = []

                init_angles.append(angle)
                elapsed = now - init_start
                status_text = f"Setting focus... {int(elapsed)}s"

                if elapsed >= INIT_TIME:
                    goal_angle = sum(init_angles) / len(init_angles)
                    print(f"\n✅ Focus direction set at angle: {goal_angle:.2f}°\n")
                    phase = "focus"
                    focus_time = 0.0
                    distraction_time = 0.0
                    off_count = 0
                    prev_in_range = True

            elif phase == "focus":
                angle_diff = angle - goal_angle

                in_facial_range = abs(angle_diff) <= ANGLE_TOLERANCE
                in_eye_range = not eye_outside

                if in_facial_range and in_eye_range:
                    focus_time += 1/30
                    status_text = f"Focusing! Face diff: {angle_diff:.1f}, Eyes OK"

                    if servo_thread is not None and servo_thread.is_alive():
                        servo_stop_event.set()
                        servo_thread.join()
                        servo_thread = None

                    tts_played = False

                    prev_in_range = True

                else:
                    distraction_time += 1/30
                    status_text = f"Distracted! Face diff: {angle_diff:.1f}, Eye out: {eye_outside}"

                    if prev_in_range:
                        off_count += 1
                        prev_in_range = False

                    if servo_thread is None or not servo_thread.is_alive():
                        servo_stop_event.clear()
                        servo_thread = Thread(target=servo_move)
                        servo_thread.start()

                    if distraction_time >= 30 and not tts_played:
                        tts_engine.say("專心點")
                        tts_engine.runAndWait()
                        tts_played = True

                if distraction_time >= DISTRACTION_LIMIT:
                    print("\n⚠️ Distracted over 60 seconds. Auto stopping.\n")
                    break

        else:
            status_text = "No face detected"

        write_status(focus_time, distraction_time, off_count, status_text)

        if results.multi_face_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                frame, results.multi_face_landmarks[0], mp_face_mesh.FACEMESH_TESSELATION)

        cv2.putText(frame, status_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Focus time: {int(focus_time)}s", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, f"Distraction time: {int(distraction_time)}s", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(frame, f"Off count: {off_count}", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("Focus Tracker with Servo and Eye Check", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("\n❌ Manual stop\n")
            break

    if servo_thread is not None and servo_thread.is_alive():
        servo_stop_event.set()
        servo_thread.join()

def release_resources():
    cap.release()
    cv2.destroyAllWindows()

initialize_camera()
release_resources()