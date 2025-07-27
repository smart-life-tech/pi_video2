# 🎥 Raspberry Pi HDMI Video Switcher (GPIO Controlled)

This project allows you to **toggle between HDMI video playback and a live webcam feed** using a physical button connected to **GPIO 22** on a **Raspberry Pi 5**.

Useful for display kiosks, art installations, or smart video systems where control via physical interface is required.

---

## 🚀 Features

- ✅ Plays 720p video file from SD card on boot
- ✅ Toggles to USB webcam feed when a button is pressed
- ✅ Uses `GPIO 22` for input (active low)
- ✅ Displays video on Pi’s HDMI output
- ✅ Runs fullscreen for clean output
- ✅ Clean toggling with internal debounce logic

---

## 🧰 Requirements

- **Raspberry Pi 5** (or Pi 4)
- **Raspberry Pi OS (Bookworm or later)**
- **USB Webcam**
- **HDMI display**
- **Push button**
- **Jumper wires**

### 📦 Python Dependencies

Install with:

```bash
pip install opencv-python psutil RPi.GPIO
sudo apt install vlc
