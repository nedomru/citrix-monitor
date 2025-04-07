import time
import threading
import queue
import psutil
import winsound
import os
from pystray import Icon, MenuItem, Menu
from PIL import Image

PROCESS_NAMES = ["Citrix.DesktopViewer.App.exe", "CDViewer.exe"]
MISSING_THRESHOLD = 10
ALERT_INTERVAL = 5  # секунд
CUSTOM_SOUND = "sounds/alert.wav"
ICON_OK = "icons/ok.png"
ICON_FIRE = "icons/fire.png"

stop_event = threading.Event()
alerting = threading.Event()
missing_seconds = 0
icon_queue = queue.Queue()  # Queue for icon updates


def load_icon(path):
    try:
        full_path = os.path.join(os.path.dirname(__file__), path)
        print(f"Loading icon from: {full_path}")
        if os.path.exists(full_path):
            return Image.open(full_path)
        else:
            print(f"Icon file not found: {full_path}")
            return None
    except Exception as e:
        print(f"Error loading icon {path}: {e}")
        return None


def process_running(process_names):
    # Check if any of the specified processes are running
    running_processes = [proc.info['name'] for proc in psutil.process_iter(['name'])]
    return any(name in running_processes for name in process_names)


def alert_loop():
    while not stop_event.is_set():
        if alerting.is_set():
            sound_path = os.path.join(os.path.dirname(__file__), CUSTOM_SOUND)
            if os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME)
            else:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
            time.sleep(ALERT_INTERVAL)
        else:
            time.sleep(1)


def monitor_process():
    global missing_seconds
    while not stop_event.is_set():
        is_running = process_running(PROCESS_NAMES)
        print(f"Processes {PROCESS_NAMES} running: {is_running}")

        if is_running:
            missing_seconds = 0
            alerting.clear()
            icon_queue.put(ICON_OK)  # Queue icon update
        else:
            missing_seconds += 1
            print(f"Missing for {missing_seconds} seconds")
            if missing_seconds >= MISSING_THRESHOLD:
                alerting.set()
                icon_queue.put(ICON_FIRE)  # Queue icon update
        time.sleep(1)


def setup(icon):
    icon.visible = True
    threading.Thread(target=alert_loop, daemon=True).start()
    threading.Thread(target=monitor_process, daemon=True).start()

    # Icon update loop in main thread
    while not stop_event.is_set():
        try:
            # Non-blocking queue check
            icon_path = icon_queue.get(block=False)
            new_icon = load_icon(icon_path)
            if new_icon:
                icon.icon = new_icon
                print(f"Icon updated to: {icon_path}")
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error updating icon: {e}")

        time.sleep(0.5)


def on_exit(icon):
    stop_event.set()
    icon.stop()


def main():
    menu = Menu(MenuItem("Выход", lambda: on_exit(icon)))
    default_icon = load_icon(ICON_FIRE)

    icon = Icon("Мониторинг Цитрикса", default_icon, menu=menu)
    icon.run(setup=setup)


if __name__ == "__main__":
    main()