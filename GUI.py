from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QFileDialog, QWidget, QVBoxLayout, QCheckBox, QHBoxLayout
from PyQt5.QtGui import QFont, QImage, QPixmap
import sys
import mss
from PIL import Image
import threading
from threading import RLock
from CaptureScreen import start_listening_for_hotkeys
from filelock import FileLock
import json

DEFAULT_IMAGE_PATH = 'C:/Documents'
TEMP_IMAGE_PATH = './temp_ss.png'
THUMBNAIL_WIDTH = 500
GLOBAL_DICT = {"hello": "World!"}
DICT_LOCK = RLock()

CONFIG_FILE = 'config.json'
CONFIG_LOCK_FILE = 'config.lock'
CONFIG_DICT = {}
FLOCK = FileLock(CONFIG_LOCK_FILE)


def start_gui():
    sys.exit(app.exec_())


def update_config():
    with FLOCK:
        with open(CONFIG_FILE, 'w') as fp:
            json.dump(CONFIG_DICT, fp)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # self.setStyleSheet("padding: 5px 10px 5px 10px")
        self.setFixedWidth(550)
        self.setFixedHeight(600)

        self.monitor_buttons = []

        main_layout = QVBoxLayout()
        self.main_widget = QWidget(self)
        self.main_widget.setFixedWidth(550)
        self.main_widget.setFixedHeight(600)

        self.g_settings = QWidget(self)
        self.g_settings.setFixedWidth(500)
        self.g_settings.setFixedHeight(150)
        # self.g_settings.setStyleSheet('background-color: #f00')

        g_settings_layout = QVBoxLayout()
        g_settings_layout.addStretch()

        self.g_settings_save_file_cb = QCheckBox('Save Screenshot', self)
        self.g_settings_save_file_cb.setFixedHeight(30)
        self.g_settings_save_file_cb.setFont(QFont('Arial', 10))
        self.g_settings_save_file_cb.stateChanged.connect(self.cb_save_file_state_changed)
        # Checked after we create the path widget


        self.g_settings_save_file_path = QLabel("Path: {}".format(CONFIG_DICT['ss_path']), self)
        self.g_settings_save_file_path.setFixedHeight(30)
        self.g_settings_save_file_path.setStyleSheet('padding-left: 5px;'
                                                  'border: 1px solid #bbb; '
                                                  'border-radius: 2px;'
                                                  'cursor: pointer;')
        self.g_settings_save_file_path.mouseReleaseEvent = lambda event: self.get_ss_save_path()

        # now we can check it after the path widget has been made
        self.g_settings_save_file_cb.setChecked(CONFIG_DICT['save_ss'])

        g_settings_layout.addWidget(self.g_settings_save_file_cb)
        g_settings_layout.addWidget(self.g_settings_save_file_path)

        self.g_settings_cpy2_clip = QCheckBox('Copy to Clipboard', self)
        self.g_settings_cpy2_clip.setFixedHeight(40)
        self.g_settings_cpy2_clip.setFont(QFont('Arial', 10))
        self.g_settings_cpy2_clip.setStyleSheet('margin-top: 20px')
        self.g_settings_cpy2_clip.stateChanged.connect(self.cb_cpy2_clip_state_changed)
        self.g_settings_cpy2_clip.setChecked(CONFIG_DICT['copy_2_cb'])
        g_settings_layout.addWidget(self.g_settings_cpy2_clip)

        self.g_settings_show_toast = QCheckBox('Show toast', self)
        self.g_settings_show_toast.setFixedHeight(40)
        self.g_settings_show_toast.setFont(QFont('Arial', 10))
        self.g_settings_show_toast.setStyleSheet('margin-top: 20px')
        self.g_settings_show_toast.stateChanged.connect(self.cb_show_toast_state_changed)
        self.g_settings_show_toast.setChecked(CONFIG_DICT['show_toast'])
        g_settings_layout.addWidget(self.g_settings_show_toast)

        self.g_settings.setLayout(g_settings_layout)

        # 500x281
        preview_layout = QVBoxLayout()
        preview_layout.addStretch(0)
        self.g_preview = QWidget(self)
        self.g_preview.setFixedHeight(400)
        self.g_preview.setFixedWidth(500)
        self.g_preview.setStyleSheet('border-radius: 3px')

        self.preview_label = QLabel("Monitors")
        preview_layout.addWidget(self.preview_label)

        monitor_layout = QHBoxLayout()
        self.g_monitors = QWidget(self)
        self.g_monitors.setMinimumHeight(20)
        self.g_monitors.setMinimumWidth(20)

        self.gen_monitor_list()

        print(self.monitor_buttons)

        for i in range(0, len(self.monitor_buttons)):
            monitor_layout.addWidget(self.monitor_buttons[i])
        monitor_layout.addStretch()

        self.g_monitors.setLayout(monitor_layout)
        preview_layout.addWidget(self.g_monitors)

        self.image_preview = QWidget(self)
        self.image_preview.setFixedWidth(490)
        self.image_preview.setFixedHeight(281)
        self.image_preview.setStyleSheet('background-color:#eee; border: 1px solid #bbb; border-radius: 2px')
        preview_layout.addWidget(self.image_preview)

        self.g_preview.setLayout(preview_layout)

        main_layout.addWidget(self.g_settings)
        main_layout.addWidget(self.g_preview)
        self.main_widget.setLayout(main_layout)

        self.show()

    def get_ss_save_path(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if file == '':
            return
        self.set_ss_save_path(file)

    def set_ss_save_path(self, file):
        self.g_settings_save_file_path.setText('Path: {}'.format(file))
        CONFIG_DICT['ss_path'] = file
        update_config()

    def gen_monitor_list(self):
        with mss.mss() as scr:
            for i in range(0, len(scr.monitors)):
                button = QPushButton(self)
                button.setText(str(i))
                button.setFixedWidth(40)
                button.setFixedHeight(40)
                button.setStyleSheet('QPushButton { background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #fff, stop: 1 #eee); border: 1px solid #bbb; } QPushButton:pressed { background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #eee, stop: 1 #fff); }')
                button.clicked.connect(lambda: self.preview_screen())
                self.monitor_buttons.append(button)

    def preview_screen(self):
        mid = int(self.sender().text())
        with mss.mss() as scr:
            scr_img = scr.grab(scr.monitors[mid])

            img = Image.frombytes("RGB", scr_img.size, scr_img.bgra, "raw", "BGRX")
            img.thumbnail((500, 281))
            img.save('temp_ss.png')

            self.image_preview.setStyleSheet('background-color:#eee; background-image: url({});background-repeat: no-repeat; background-position: center center; border: 1px solid #bbb;'.format(TEMP_IMAGE_PATH))

    def cb_save_file_state_changed(self, int):
        if self.g_settings_save_file_cb.isChecked():
            self.g_settings_save_file_path.setEnabled(True)
            CONFIG_DICT['save_ss'] = True
        else:
            self.g_settings_save_file_path.setEnabled(False)
            CONFIG_DICT['save_ss'] = False

        update_config()

    def cb_cpy2_clip_state_changed(self, int):
        CONFIG_DICT['copy_2_cb'] = self.g_settings_cpy2_clip.isChecked()
        update_config()

    def cb_show_toast_state_changed(self, int):
        CONFIG_DICT['show_toast'] = self.g_settings_show_toast.isChecked()
        update_config()


with open(CONFIG_FILE) as config:
    CONFIG_DICT = json.load(config)
    print(CONFIG_DICT)

app = QApplication([])
window = Window()
start_gui()

listener = threading.Thread(target=start_listening_for_hotkeys)
listener.start()
