import pygame
import sys
import time
import os
import subprocess
import psutil
import cv2
from gpiozero import DigitalInputDevice

# === CONFIG ===
VIDEO_FILE = "/home/deg/pi_video2/test.mp4"        # Path to MP4
IMAGE_PATH = "/home/deg/pi_video2/black.png"        # Black background image
GPIO_INPUT = 22                                      # GPIO pin (connected to GND for video)
STATE_VIDEO = 0
STATE_CAMERA = 1

# === GLOBAL STATE ===
current_state = None
mpv_process = None

# === GPIO SETUP ===
input_pin = DigitalInputDevice(GPIO_INPUT, pull_up=True)

# === PYGAME BLACK SCREEN SETUP ===
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
image = pygame.image.load(IMAGE_PATH)
image = pygame.transform.scale(image, (screen_width, screen_height))
pygame.mouse.set_visible(False)

def draw_black_screen():
    screen.fill((0, 0, 0))
    screen.blit(image, (0, 0))
    pygame.display.flip()

def kill_mpv():
    global mpv_process
    if mpv_process:
        mpv_process.terminate()
        mpv_process = None
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and "mpv" in proc.info['name'].lower():
            try:
                proc.kill()
            except Exception:
                pass

def play_video():
    global mpv_process
    print("[INFO] Playing video...")
    #kill_mpv()
    draw_black_screen()
    #time.sleep(0.3)  # Small delay to ensure screen is cleared
    mpv_process = subprocess.Popen([
        "mpv",
        "--fs",
        "--loop",
        "--ontop",
        "--no-border",
        "--geometry=0:0",
        VIDEO_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def show_webcam():
    print("[INFO] Showing webcam...")
    kill_mpv()
    #draw_black_screen()
    time.sleep(0.3)  # Prevent flicker from leftover mpv window

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open webcam")
        return

    cv2.namedWindow("Webcam Feed", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Webcam Feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    subprocess.call(["wmctrl", "-r", "Webcam Feed", "-b", "add,above"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    while input_pin.value == 1:  # Webcam only active while ungrounded
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read from webcam")
            break

        frame_resized = cv2.resize(frame, (screen_width, screen_height))
        cv2.imshow("Webcam Feed", frame_resized)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# === MAIN LOOP ===
try:
    print("[BOOT] System starting...")
    while True:
        draw_black_screen()

        if input_pin.value == 0:  # GROUNDED = play video
            if current_state != STATE_VIDEO:
                current_state = STATE_VIDEO
                play_video()
        else:  # UNGROUNDED = show webcam
            if current_state != STATE_CAMERA:
                current_state = STATE_CAMERA
                show_webcam()

        pygame.event.pump()
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Shutting down...")
    kill_mpv()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()
