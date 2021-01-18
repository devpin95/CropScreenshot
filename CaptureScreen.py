import mss
from PIL import Image
import keyboard
import win32clipboard as cb
from io import BytesIO
from filelock import FileLock
import json
from datetime import datetime
from win10toast import ToastNotifier
import os
from multiprocessing import current_process

NUM_MONITORS = 3
active_monitor = 1
CONFIG_LOCK_FILE = 'config.lock'
CONFIG_FILE = 'config.json'
CONFIG_DICT = {}
FLOCK = FileLock(CONFIG_LOCK_FILE)


def start_listening_for_hotkeys():
    get_config()
    keyboard.add_hotkey(CONFIG_DICT['ss_hotkey'], on_trigger)

    switch_screen_shortcuts = ['ctrl+alt+' + str(i) for i in range(0, NUM_MONITORS)]
    for sc in switch_screen_shortcuts:
        keyboard.add_hotkey(sc, lambda sc=sc: set_active_monitor(sc[-1]))

    print("Listening from", current_process().name)
    keyboard.wait()


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
    global CONFIG_DICT

    get_config()

    active_monitor = int(mid)
    print(os.getpid(), 'monitor {} is now active'.format(active_monitor))
    if CONFIG_DICT['show_toast_on_monitor_change']:
        toaster = ToastNotifier()
        toaster.show_toast("PowerSS", 'monitor {} is now active'.format(active_monitor), duration=2, threaded=True,
                           icon_path='assets\\icon-pink-256x256.ico')


def on_trigger():

    get_config()

    with mss.mss() as scr:
        toast_str = ''
        scr_img = scr.grab(scr.monitors[active_monitor])

        img = Image.frombytes("RGB", scr_img.size, scr_img.bgra, "raw", "BGRX")

        # now = datetime.now().strftime("%m%d%Y%H%M%S")
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        if CONFIG_DICT['save_ss']:
            path = '{}/{}-ss.png'.format(CONFIG_DICT['ss_path'], now)
            print("PATH", path)
            img.save(path)
            toast_str += '{}-screenshot.png saved!'.format(now)

        output = BytesIO()
        img.save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        if CONFIG_DICT['copy_2_cb']:
            send_to_clipboard(cb.CF_DIB, data)
            toast_str = 'Copied to Clipboard\n' + toast_str

        if CONFIG_DICT['show_toast_on_capture']:
            toaster = ToastNotifier()
            toaster.show_toast("PowerSS", toast_str, duration=5, threaded=True,
                               icon_path='assets\\icon-pink-256x256.ico')

