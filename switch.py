from gpiozero import Button
import cv2
import subprocess
import time
import psutil

# === CONFIG ===
VIDEO_FILE = "BigBuckBunny_320x180.mp4"  
GPIO_BUTTON = 27
STATE_VIDEO = 0
STATE_CAMERA = 1

# === GLOBAL STATE ===
current_state = STATE_VIDEO
vlc_process = None

# === SETUP BUTTON ===
button = Button(GPIO_BUTTON, pull_up=True)

# === UTILS ===
def kill_vlc():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and "vlc" in proc.info['name'].lower():
            try:
                proc.terminate()
            except Exception:
                pass

def play_video():
    print("[INFO] Playing video...")
    kill_vlc()
    return subprocess.Popen(["cvlc", "--fullscreen", "--play-and-exit", VIDEO_FILE])

def show_webcam():
    print("[INFO] Showing webcam...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    while current_state == STATE_CAMERA:
        ret, frame = cap.read()
        if not ret:
            break
        frame_resized = cv2.resize(frame, (1280, 720))
        cv2.imshow('Webcam Feed', frame_resized)

        if cv2.waitKey(1) == 27:  # Esc to quit
            break

    cap.release()
    cv2.destroyAllWindows()

# === BUTTON HANDLER ===
def button_pressed():
    global current_state, vlc_process

    print("[GPIOZERO] Button pressed")

    if current_state == STATE_VIDEO:
        print("[STATE] Switching to camera")
        kill_vlc()
        current_state = STATE_CAMERA
    else:
        print("[STATE] Switching to video")
        current_state = STATE_VIDEO

button.when_pressed = button_pressed

# === MAIN LOOP ===
try:
    while True:
        if current_state == STATE_VIDEO:
            vlc_process = play_video()
            vlc_process.wait()  # Wait for video to finish or be killed
        elif current_state == STATE_CAMERA:
            show_webcam()
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")
    kill_vlc()
    cv2.destroyAllWindows()
