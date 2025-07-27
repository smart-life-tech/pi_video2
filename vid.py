import subprocess
import time
import os
import signal

# === CONFIG ===
VIDEO_FILE = "/home/pi/test.mp4"
CAM_IMAGE = "/dev/shm/cam.jpg"
SWITCH_INTERVAL = 10  # Seconds
CAMERA_CMD = ["fswebcam", "-q", "--no-banner", "-r", "1280x720", CAM_IMAGE]
VIEWER_CMD = ["feh", "-F", "-Z", "--hide-pointer", "--reload", "1", CAM_IMAGE]

video_proc = None
viewer_proc = None

def start_video():
    global video_proc
    print("[INFO] Starting video playback")
    video_proc = subprocess.Popen([
        "cvlc", "--no-osd", "--play-and-exit", "--no-video-title-show", "--quiet", VIDEO_FILE
    ])
    
def stop_video():
    global video_proc
    if video_proc and video_proc.poll() is None:
        print("[INFO] Stopping video playback")
        video_proc.terminate()
        video_proc.wait()
    video_proc = None

def start_camera():
    global viewer_proc
    print("[INFO] Starting camera preview")
    viewer_proc = subprocess.Popen(VIEWER_CMD)
    # Start a loop to update the image every second in background
    try:
        for _ in range(SWITCH_INTERVAL * 10):  # Roughly 10 FPS
            subprocess.run(CAMERA_CMD)
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    stop_camera()

def stop_camera():
    global viewer_proc
    if viewer_proc and viewer_proc.poll() is None:
        print("[INFO] Stopping camera preview")
        viewer_proc.terminate()
        viewer_proc.wait()
    viewer_proc = None

# === MAIN LOOP ===
try:
    while True:
        start_video()
        time.sleep(SWITCH_INTERVAL)
        stop_video()
        
        start_camera()
        # image capture loop happens inside start_camera
        # no need to sleep here
except KeyboardInterrupt:
    print("Exiting...")
    stop_video()
    stop_camera()
