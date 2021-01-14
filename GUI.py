from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QFileDialog, QWidget, QVBoxLayout, QCheckBox, QHBoxLayout
from PyQt5.QtGui import QFont, QCursor, QIcon
from PyQt5 import QtCore, QtWinExtras
import sys
import mss
from PIL import Image
import threading
from threading import RLock
from CaptureScreen import start_listening_for_hotkeys
from filelock import FileLock
import json
import ctypes
import os

# https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
# for setting the taskbar icon in windows
myappid = 'devin.projects.powerss.1'  # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

DEFAULT_IMAGE_PATH = 'C:/Documents'
TEMP_IMAGE_PATH = './temp_ss.png'
ICON_IMAGE_PATH = './assets/icon.png'
DEFAULT_PREVIEW_PATH = './assets/default_preview.png'
THUMBNAIL_WIDTH = 490
THUMBNAIL_HEIGHT = 281
GLOBAL_DICT = {"hello": "World!"}
DICT_LOCK = RLock()

WINDOW_TITLE = 'PowerSS'
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
        self.setFixedWidth(525)
        self.setFixedHeight(800)
        self.setWindowTitle(WINDOW_TITLE)

        # self.setWindowIcon(app_icon)

        self.monitor_buttons = []

        main_layout = QVBoxLayout()
        self.main_widget = QWidget(self)
        self.main_widget.setFixedWidth(525)
        self.main_widget.setFixedHeight(800)

        self.g_instructions = QWidget(self)
        self.g_instructions.setFixedWidth(500)
        self.g_instructions.setFixedHeight(100)
        self.g_instructions.setStyleSheet('border: 1px solid #000;'
                                          'border-radius: 2px')

        g_instructions_layout = QVBoxLayout()

        self.g_instructions_title = QLabel('How to use PowerSS:')
        instructions_title_fontt = QFont('Arial', 10)
        instructions_title_fontt.setBold(True)
        self.g_instructions_title.setFont(instructions_title_fontt)
        self.g_instructions_title.setStyleSheet('border: none;')
        g_instructions_layout.addWidget(self.g_instructions_title)

        # To see which monitor is which, test the preview below
        self.g_instructions_hotkeys = QLabel('ctrl+alt+[monitor number] - Set active monitor\nctrl+alt+s - Take screenshot')
        self.g_instructions_hotkeys.setFont(QFont('Arial', 10))
        self.g_instructions_hotkeys.setStyleSheet('border: none;')
        g_instructions_layout.addWidget(self.g_instructions_hotkeys)

        self.g_instructions_preview = QLabel('To see which monitor is which, test the preview below')
        self.g_instructions_preview.setFont(QFont('Arial', 10))
        self.g_instructions_preview.setStyleSheet('border: none;')
        g_instructions_layout.addWidget(self.g_instructions_preview)

        g_instructions_layout.addStretch()
        self.g_instructions.setLayout(g_instructions_layout)

        self.g_settings = QWidget(self)
        self.g_settings.setFixedWidth(500)
        self.g_settings.setFixedHeight(250)

        g_settings_layout = QVBoxLayout()

        self.g_settings_save_file_cb = QCheckBox('Save Screenshot', self)
        self.g_settings_save_file_cb.setFixedHeight(30)
        self.g_settings_save_file_cb.setFont(QFont('Arial', 10))
        self.g_settings_save_file_cb.setStyleSheet("border: none;")
        self.g_settings_save_file_cb.stateChanged.connect(self.cb_save_file_state_changed)
        # Checked after we create the path widget

        if CONFIG_DICT['ss_path'] == '':
            self.init_save_path()

        self.g_settings_save_file_path = QLabel("Path: {}".format(CONFIG_DICT['ss_path']), self)
        self.g_settings_save_file_path.setFixedHeight(30)
        self.g_settings_save_file_path.setStyleSheet('QLabel{ padding-left: 5px;'
                                                     'border: 1px solid #bbb; '
                                                     'border-radius: 2px;'
                                                     'cursor: pointer;} '
                                                     'QLabel:hover{ border: 1px solid #666; }')
        self.g_settings_save_file_path.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_settings_save_file_path.mouseReleaseEvent = lambda event: self.get_ss_save_path()

        # now we can check it after the path widget has been made
        self.g_settings_save_file_cb.setChecked(CONFIG_DICT['save_ss'])

        g_settings_layout.addWidget(self.g_settings_save_file_cb)
        g_settings_layout.addWidget(self.g_settings_save_file_path)

        self.g_settings_cpy2_clip = QCheckBox('Copy to Clipboard', self)
        self.g_settings_cpy2_clip.setFixedHeight(40)
        self.g_settings_cpy2_clip.setFont(QFont('Arial', 10))
        self.g_settings_cpy2_clip.setStyleSheet('border: none;')
        self.g_settings_cpy2_clip.stateChanged.connect(self.cb_cpy2_clip_state_changed)
        self.g_settings_cpy2_clip.setChecked(CONFIG_DICT['copy_2_cb'])
        g_settings_layout.addWidget(self.g_settings_cpy2_clip)

        self.g_settings_show_toast_on_monitor_change = QCheckBox('Toast on Monitor Change', self)
        self.g_settings_show_toast_on_monitor_change.setFixedHeight(40)
        self.g_settings_show_toast_on_monitor_change.setFont(QFont('Arial', 10))
        self.g_settings_show_toast_on_monitor_change.setStyleSheet('border: none;')
        self.g_settings_show_toast_on_monitor_change.stateChanged.connect(self.cb_show_toast_on_monitor_state_changed)
        self.g_settings_show_toast_on_monitor_change.setChecked(CONFIG_DICT['show_toast_on_monitor_change'])
        g_settings_layout.addWidget(self.g_settings_show_toast_on_monitor_change)

        self.g_settings_show_toast_on_capture = QCheckBox('Toast on Capture', self)
        self.g_settings_show_toast_on_capture.setFixedHeight(40)
        self.g_settings_show_toast_on_capture.setFont(QFont('Arial', 10))
        self.g_settings_show_toast_on_capture.setStyleSheet('border: none;')
        self.g_settings_show_toast_on_capture.stateChanged.connect(self.cb_show_toast_on_capture_state_changed)
        self.g_settings_show_toast_on_capture.setChecked(CONFIG_DICT['show_toast_on_capture'])
        g_settings_layout.addWidget(self.g_settings_show_toast_on_capture)

        # g_settings_layout.addStretch()
        self.g_settings.setLayout(g_settings_layout)

        # 500x281
        preview_layout = QVBoxLayout()
        # preview_layout.addStretch(0)
        self.g_preview = QWidget(self)
        self.g_preview.setFixedHeight(400)
        self.g_preview.setFixedWidth(500)
        self.g_preview.setStyleSheet('border-radius: 3px')

        self.preview_label = QLabel("Preview Monitors")
        self.preview_label.setFont(instructions_title_fontt)
        preview_layout.addWidget(self.preview_label)

        monitor_layout = QHBoxLayout()
        self.g_monitors = QWidget(self)
        self.g_monitors.setMinimumHeight(20)
        self.g_monitors.setMinimumWidth(20)

        self.gen_monitor_list()

        for i in range(0, len(self.monitor_buttons)):
            monitor_layout.addWidget(self.monitor_buttons[i])
        monitor_layout.addStretch()

        self.g_monitors.setLayout(monitor_layout)
        preview_layout.addWidget(self.g_monitors)

        self.image_preview = QWidget(self)
        self.image_preview.setFixedWidth(490)
        self.image_preview.setFixedHeight(281)
        self.image_preview.setStyleSheet('background-color:#eee; '
                                         'border: 1px solid #bbb; '
                                         'border-radius: 2px;'
                                         'background-color:#eee; '
                                         'background-image: url({}); '
                                         'background-repeat: no-repeat; '
                                         'background-position: center center; '
                                         'border: 1px solid #bbb;'.format(DEFAULT_PREVIEW_PATH))
        preview_layout.addWidget(self.image_preview)

        self.g_preview.setLayout(preview_layout)

        main_layout.addWidget(self.g_instructions)
        main_layout.addWidget(self.g_settings)
        main_layout.addWidget(self.g_preview)
        main_layout.addStretch()
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
                button.setStyleSheet('QPushButton { '
                                     'background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #fff, stop: 1 #eee); border: 1px solid #bbb;'
                                     '} '
                                     'QPushButton:pressed { '
                                     'background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #eee, stop: 1 #fff); '
                                     '} '
                                     'QPushButton:hover {'
                                     'border: 1px solid #666;'
                                     '}')
                button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
                button.clicked.connect(lambda: self.preview_screen())
                self.monitor_buttons.append(button)

    def preview_screen(self):
        mid = int(self.sender().text())
        with mss.mss() as scr:
            scr_img = scr.grab(scr.monitors[mid])

            img = Image.frombytes("RGB", scr_img.size, scr_img.bgra, "raw", "BGRX")
            img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
            img.save(TEMP_IMAGE_PATH)

            self.image_preview.setStyleSheet('background-color:#eee; background-image: url({});background-repeat: no-repeat; background-position: center center; border: 1px solid #bbb;'.format(TEMP_IMAGE_PATH))

    def cb_save_file_state_changed(self, int):
        self.g_settings_save_file_path.setEnabled(self.g_settings_save_file_cb.isChecked())
        CONFIG_DICT['save_ss'] = self.g_settings_save_file_cb.isChecked()

        if CONFIG_DICT['ss_path'] == '':
            self.init_save_path()

        update_config()

    def cb_cpy2_clip_state_changed(self, int):
        CONFIG_DICT['copy_2_cb'] = self.g_settings_cpy2_clip.isChecked()
        update_config()

    def cb_show_toast_on_monitor_state_changed(self, int):
        CONFIG_DICT['show_toast_on_monitor_change'] = self.g_settings_show_toast_on_monitor_change.isChecked()
        update_config()

    def cb_show_toast_on_capture_state_changed(self, int):
        CONFIG_DICT['show_toast_on_capture'] = self.g_settings_show_toast_on_monitor_change.isChecked()
        update_config()

    def closeEvent(self, event):
        if os.path.exists(TEMP_IMAGE_PATH):
            os.remove(TEMP_IMAGE_PATH)

    def init_save_path(self):
        cwd = os.getcwd()
        CONFIG_DICT['ss_path'] = cwd
        update_config()


with open(CONFIG_FILE) as config:
    CONFIG_DICT = json.load(config)

app = QApplication([])

app_icon = QIcon()
app_icon.addFile('./assets/icon-16x16.png', QtCore.QSize(16, 16))
app_icon.addFile('./assets/icon-24x24.png', QtCore.QSize(24, 24))
app_icon.addFile('./assets/icon-32x32.png', QtCore.QSize(32, 32))
app_icon.addFile('./assets/icon-48x48.png', QtCore.QSize(48, 48))
app_icon.addFile('./assets/icon-256x256.png', QtCore.QSize(256, 256))

app.setWindowIcon(app_icon)

window = Window()
start_gui()

listener = threading.Thread(target=start_listening_for_hotkeys)
listener.start()
