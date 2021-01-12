import mss
from PIL import Image
import keyboard
import win32clipboard as cb
from io import BytesIO

NUM_MONITORS = 3
active_monitor = 1


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
    with mss.mss() as scr:
        scr_img = scr.grab(scr.monitors[active_monitor])

        img = Image.frombytes("RGB", scr_img.size, scr_img.bgra, "raw", "BGRX")
        img.save('screenshot.png')

        output = BytesIO()
        img.save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        send_to_clipboard(cb.CF_DIB, data)


switch_screen_shortcuts = ['ctrl+alt+' + str(i) for i in range(0, NUM_MONITORS)]
for sc in switch_screen_shortcuts:
    keyboard.add_hotkey(sc, lambda sc=sc: set_active_monitor(sc[-1]))


print(switch_screen_shortcuts)

shortcut = "ctrl+alt+s"
keyboard.add_hotkey(shortcut, on_trigger)

print("Ready to capture...")
keyboard.wait()

