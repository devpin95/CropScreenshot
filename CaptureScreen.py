import mss
from PIL import Image
import keyboard
import win32clipboard as cb
from io import BytesIO
from filelock import FileLock
import json
from datetime import datetime

NUM_MONITORS = 3
active_monitor = 1
CONFIG_LOCK_FILE = 'config.lock'
CONFIG_FILE = 'config.json'
CONFIG_DICT = {}
FLOCK = FileLock(CONFIG_LOCK_FILE)


def get_config():
    global CONFIG_DICT
    with FLOCK:
        with open(CONFIG_FILE, 'r') as fp:
            CONFIG_DICT = json.load(fp)


def send_to_clipboard(clip_type, data):
    cb.OpenClipboard()
    cb.EmptyClipboard()
    cb.SetClipboardData(clip_type, data)
    cb.CloseClipboard()


def set_active_monitor(mid):
    global active_monitor
    active_monitor = int(mid)
    print('monitor {} is now active'.format(active_monitor))


def on_trigger():

    get_config()

    print(CONFIG_DICT)

    with mss.mss() as scr:
        print("Taking sss")
        scr_img = scr.grab(scr.monitors[active_monitor])

        img = Image.frombytes("RGB", scr_img.size, scr_img.bgra, "raw", "BGRX")

        if CONFIG_DICT['save_ss']:
            path = '{}/{}-screenshot.png'.format(CONFIG_DICT['ss_path'], datetime.now().strftime("%m%d%Y-%H%M%S"))
            print("PATH", path)
            img.save(path)

        output = BytesIO()
        img.save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        if CONFIG_DICT['copy_2_cb']:
            send_to_clipboard(cb.CF_DIB, data)

switch_screen_shortcuts = ['ctrl+alt+' + str(i) for i in range(0, NUM_MONITORS)]
for sc in switch_screen_shortcuts:
    keyboard.add_hotkey(sc, lambda sc=sc: set_active_monitor(sc[-1]))

shortcut = "ctrl+alt+s"
keyboard.add_hotkey(shortcut, on_trigger)

def start_listening_for_hotkeys():
    keyboard.wait()

