# pyinstaller -F -i C:\Users\devpi\Documents\projects\CropScreenshot\assets\icon-pink-256x256.ico -n PowerSS --debug GUI.py

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QFileDialog, QWidget, QVBoxLayout, QCheckBox, QHBoxLayout, QSpinBox, QErrorMessage, QTabWidget
from PyQt5.QtGui import QFont, QCursor, QIcon, QKeyEvent
from PyQt5 import QtCore
import sys
import mss
from PIL import Image
from multiprocessing import Process, current_process, freeze_support
from threading import RLock
from CaptureScreen import start_listening_for_hotkeys
from filelock import FileLock
import json
import ctypes
import os
from QtKeyValueToKeyboardValue import qt_to_keyboard

# https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
# for setting the taskbar icon in windows
myappid = 'devin.projects.powerss.1'  # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

DEFAULT_IMAGE_PATH = 'C:/Documents'
TEMP_IMAGE_PATH = './temp_ss.png'
ICON_IMAGE_PATH = './assets/icon.png'
DEFAULT_PREVIEW_PATH = './assets/default_preview.png'
THUMBNAIL_WIDTH = 500
THUMBNAIL_HEIGHT = 281
GLOBAL_DICT = {"hello": "World!"}
DICT_LOCK = RLock()

APP_WIDTH = 525
APP_HEIGHT = 850
WIDGET_WIDTH = 485
FIELD_HEIGHT = 30

ESCAPE_KEY_CODE = 16777216

WINDOW_TITLE = 'PowerSS'
CONFIG_FILE = 'config.json'
CONFIG_LOCK_FILE = 'config.lock'
CONFIG_DICT = {}
FLOCK = FileLock(CONFIG_LOCK_FILE)
HOTKEY_LISTENER = None

FLAG_CAPTURING_INPUT = False

key_list = []


def start_gui():
    sys.exit(app.exec_())


def update_config():
    with FLOCK:
        with open(CONFIG_FILE, 'w') as fp:
            json.dump(CONFIG_DICT, fp)


class HotkeyListener:
    process = None
    started = False

    def __init__(self):
        self.process = Process(target=start_listening_for_hotkeys, name="peepeepoopoo123")
        self.process.daemon = True

    def start(self):
        if not self.started:
            print("starting process 1")
            self.process.start()
            self.started = True
        else:
            print("starting process 2")
            self.process = Process(target=start_listening_for_hotkeys)
            self.process.daemon = True
            self.process.start()

    def kill(self):
        self.process.kill()

    def terminate(self):
        self.process.terminate()


class Window(QMainWindow):
    # set this as a member variable so that we can access elements while we listen for hotkeys
    screen_cap_tab = None
    image_resize_tab = None

    def __init__(self):
        super().__init__()

        # self.setStyleSheet("padding: 5px 10px 5px 10px")
        self.setFixedWidth(APP_WIDTH)
        self.setFixedHeight(APP_HEIGHT + 50)
        self.setWindowTitle(WINDOW_TITLE)

        # self.setWindowIcon(app_icon)

        self.tabs = QTabWidget()

        self.tabs.setStyleSheet("QTabWidget::pane {"
                                "background-color: #f00}")

        self.tabs.currentChanged.connect(self.tab_change_event)
        self.tabs.tabBarClicked.connect(lambda: self.capture_hotkey(ESCAPE_KEY_CODE))

        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(APP_WIDTH, APP_HEIGHT)

        self.tab1_ui()
        self.tab2_ui()

        self.setCentralWidget(self.tabs)

        self.show()

    def tab1_ui(self):
        # Screen Capture tab
        self.tab1.layout = QVBoxLayout(self)

        self.tabs.setStyleSheet("QTabWidget::tab-bar {"
                                "background-color: #f00}")

        self.screen_cap_tab = ScreenCaptureTab(self)
        self.tab1.layout.addWidget(self.screen_cap_tab.main_widget)
        self.tab1.setLayout(self.tab1.layout)

        self.tabs.addTab(self.tab1, "Screen Capture")

    def tab2_ui(self):
        self.tabs.addTab(self.tab2, "Resize Image")

        self.tab2.layout = QVBoxLayout(self)

        self.image_resize_tab = ImageResizeTab(self)
        self.tab2.layout.addWidget(self.image_resize_tab.main_widget)
        self.tab2.setLayout(self.tab2.layout)

    def tab_change_event(self, index):
        global FLAG_CAPTURING_INPUT

        if index is 0:
            self.setFixedWidth(APP_WIDTH)
            self.setFixedHeight(APP_HEIGHT)
        elif index is 1:
            if FLAG_CAPTURING_INPUT:
                self.capture_hotkey('esc')
            self.setFixedWidth(APP_WIDTH)
            self.setFixedHeight(300 + 50)

    def eventFilter(self, obj, event):
        # eventFilter for the main window
        global FLAG_CAPTURING_INPUT
        if event.type() == QtCore.QEvent.KeyPress and FLAG_CAPTURING_INPUT:
            self.capture_hotkey(event.key())

        return super(Window, self).eventFilter(obj, event)

    def capture_hotkey(self, key):
        global FLAG_CAPTURING_INPUT, key_list, HOTKEY_LISTENER

        input_flags = ['esc', 'enter']

        print(key)

        try:
            name = chr(key)
        except:
            name = qt_to_keyboard(key)

        if name not in key_list and name not in input_flags:
            key_list.append(name)
            self.screen_cap_tab.g_settings_hotkey_val.setText('+'.join(key_list))

        resetting = False
        if name == 'esc':
            key_list = []
            resetting = True
        elif name == 'enter':
            if len(key_list) == 0:
                error_dialog = QErrorMessage()
                error_dialog.showMessage('Must enter a sequence of keys...')
                error_dialog.exec_()
            else:
                CONFIG_DICT['ss_hotkey'] = '+'.join(key_list)
                update_config()
                resetting = True

        if resetting:
            key_list = []
            FLAG_CAPTURING_INPUT = False
            self.screen_cap_tab.g_settings_hotkey_val.setText(CONFIG_DICT['ss_hotkey'])
            self.screen_cap_tab.g_setting_hotkey_change_button.setStyleSheet('QPushButton {'
                                                              'border-radius: 2px;'
                                                              'background-color: qlineargradient('
                                                              'x1: 0, y1: 0, x2: 0, y2: 1,'
                                                              'stop: 0 #fff, stop: 1 #eee); '
                                                              'border: 1px solid #bbb;'
                                                              '} '
                                                              'QPushButton:pressed { '
                                                              'background-color: qlineargradient('
                                                              'x1: 0, y1: 0, x2: 0, y2: 1,'
                                                              'stop: 0 #eee, stop: 1 #fff); '
                                                              '} '
                                                              'QPushButton:hover {'
                                                              'border: 1px solid #666;'
                                                              '}')
            self.screen_cap_tab.g_setting_hotkey_change_button.setText('Set')
            self.screen_cap_tab.g_instructions_hotkeys.setText('ctrl+alt+[monitor number] - Set active monitor\n{} - Take screenshot'.format(CONFIG_DICT['ss_hotkey']))

            print("trying to start process")
            try:
                HOTKEY_LISTENER.start()
            except Exception as e:
                print(e)


class ScreenCaptureTab(QWidget):
    main_layout = None
    main_widget = None

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.monitor_buttons = []

        self.main_layout = QVBoxLayout()
        self.main_widget = QWidget(self)
        # self.main_widget.setFixedWidth(APP_WIDTH)
        # self.main_widget.setFixedHeight(APP_HEIGHT)

        # Instruction --------------------------------------------------------------------------------------------------
        self.g_instructions = QWidget(self)
        self.g_instructions.setFixedWidth(WIDGET_WIDTH)
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

        self.g_instructions_hotkeys = QLabel(
            'ctrl+alt+[monitor number] - Set active monitor\n{} - Take screenshot'.format(CONFIG_DICT['ss_hotkey']))
        self.g_instructions_hotkeys.setFont(QFont('Arial', 10))
        self.g_instructions_hotkeys.setStyleSheet('border: none;')
        g_instructions_layout.addWidget(self.g_instructions_hotkeys)

        self.g_instructions_preview = QLabel('To see which monitor is which, test the preview below')
        self.g_instructions_preview.setFont(QFont('Arial', 10))
        self.g_instructions_preview.setStyleSheet('border: none;')
        g_instructions_layout.addWidget(self.g_instructions_preview)

        g_instructions_layout.addStretch()
        self.g_instructions.setLayout(g_instructions_layout)

        # Settings -----------------------------------------------------------------------------------------------------
        self.g_settings = QWidget(self)
        self.g_settings.setFixedWidth(WIDGET_WIDTH)
        self.g_settings.setFixedHeight(325)
        self.g_settings.setStyleSheet('padding: 0; margin: 0;')
        # self.g_settings.setStyleSheet('QWidget{background-color:#f00;} QWidget QCheckBox {padding: 0; margin: 0; background-color: #0f0;}')

        g_settings_layout = QVBoxLayout()
        g_settings_layout.setContentsMargins(0, 0, 0, 0)

        # Hotkey -------------------------------------------------------------------------------------------------------
        self.g_settings_set_hotkey_label = QLabel('Capture Hotkey', self)
        self.g_settings_set_hotkey_label.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_set_hotkey_label.setFont(QFont('Arial', 10))
        self.g_settings_set_hotkey_label.setStyleSheet("border: none;")
        g_settings_layout.addWidget(self.g_settings_set_hotkey_label)

        self.g_settings_set_hotkey = QWidget(self)
        self.g_settings_set_hotkey.setFixedHeight(30)
        self.g_settings_set_hotkey.setFixedWidth(WIDGET_WIDTH)
        self.g_settings_set_hotkey.setStyleSheet('QLabel{'
                                                 'padding-left: 5px;'
                                                 'border: 1px solid #bbb;'
                                                 'border-radius: 2px;}')

        hotkey_layout = QHBoxLayout()
        hotkey_layout.setContentsMargins(0, 0, 0, 0)

        self.g_settings_hotkey_val = QLabel(CONFIG_DICT['ss_hotkey'], self)
        self.g_settings_hotkey_val.setFixedHeight(FIELD_HEIGHT)

        hotkey_layout.addWidget(self.g_settings_hotkey_val)

        self.g_setting_hotkey_change_button = QPushButton("Set")
        self.g_setting_hotkey_change_button.setFixedHeight(FIELD_HEIGHT)
        self.g_setting_hotkey_change_button.setFocusPolicy(QtCore.Qt.NoFocus)
        # self.g_setting_hotkey_change_button.setFixedWidth(100)
        self.g_setting_hotkey_change_button.setStyleSheet('QPushButton {'
                                                          'border-radius: 2px;'
                                                          'background-color: qlineargradient('
                                                          'x1: 0, y1: 0, x2: 0, y2: 1,'
                                                          'stop: 0 #fff, stop: 1 #eee); '
                                                          'border: 1px solid #bbb;'
                                                          '} '
                                                          'QPushButton:pressed { '
                                                          'background-color: qlineargradient('
                                                          'x1: 0, y1: 0, x2: 0, y2: 1,'
                                                          'stop: 0 #eee, stop: 1 #fff); '
                                                          '} '
                                                          'QPushButton:hover {'
                                                          'border: 1px solid #666;'
                                                          '}')
        self.g_setting_hotkey_change_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_setting_hotkey_change_button.clicked.connect(self.get_custom_hotkey)
        hotkey_layout.addWidget(self.g_setting_hotkey_change_button)

        self.g_settings_set_hotkey.setLayout(hotkey_layout)
        g_settings_layout.addWidget(self.g_settings_set_hotkey)

        # Save SS Checkbox ---------------------------------------------------------------------------------------------
        self.g_settings_save_file_cb = QCheckBox('Save Screenshot', self)
        self.g_settings_save_file_cb.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_save_file_cb.setFont(QFont('Arial', 10))
        self.g_settings_save_file_cb.setStyleSheet("border: none;")
        self.g_settings_save_file_cb.stateChanged.connect(self.cb_save_file_state_changed)
        self.g_settings_save_file_cb.setFocusPolicy(QtCore.Qt.NoFocus)
        # Checked after we create the path widget

        if CONFIG_DICT['ss_path'] == '':
            self.init_save_path()

        # SS Path ------------------------------------------------------------------------------------------------------
        # self.g_settings_save_file_path = QLabel("Path: {}".format(CONFIG_DICT['ss_path']), self)
        # self.g_settings_save_file_path.setFixedHeight(FIELD_HEIGHT)
        # # self.g_settings_save_file_path.setFixedWidth(WIDGET_WIDTH)
        # self.g_settings_save_file_path.setStyleSheet('QLabel{ padding-left: 5px;'
        #                                              'border: 1px solid #bbb; '
        #                                              'border-radius: 2px;'
        #                                              'cursor: pointer;} '
        #                                              'QLabel:hover{ border: 1px solid #666; }')
        # self.g_settings_save_file_path.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        # self.g_settings_save_file_path.mouseReleaseEvent = lambda event: self.get_ss_save_path()
        # self.g_settings_save_file_path.setFocusPolicy(QtCore.Qt.NoFocus)

        self.g_settings_set_path = QWidget(self)
        self.g_settings_set_path.setFixedHeight(30)
        self.g_settings_set_path.setFixedWidth(WIDGET_WIDTH)
        self.g_settings_set_path.setStyleSheet('QLabel{'
                                               'padding-left: 5px;'
                                               'border: 1px solid #bbb;'
                                               'border-radius: 2px;}'
                                               'QLabel:hover{border:1px solid #000;}')
        self.g_settings_set_path.setEnabled(CONFIG_DICT['save_ss'])

        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)

        self.g_settings_path_val = QLabel("Path: {}".format(CONFIG_DICT['ss_path']), self)
        self.g_settings_path_val.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_path_val.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_settings_path_val.mouseReleaseEvent = lambda event: os.startfile(CONFIG_DICT['ss_path'])

        path_layout.addWidget(self.g_settings_path_val)

        self.g_setting_path_change_button = QPushButton("")
        self.g_setting_path_change_button.setFixedHeight(FIELD_HEIGHT)
        self.g_setting_path_change_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.g_setting_path_change_button.setFixedWidth(FIELD_HEIGHT)
        self.g_setting_path_change_button.setStyleSheet('QPushButton {'
                                                        'border-radius: 2px;'
                                                        'background-image: url(assets/folder.png);'
                                                        'background-repeat: no-repeat; '
                                                        'background-position: center center;'
                                                        'background-color: qlineargradient('
                                                        'x1: 0, y1: 0, x2: 0, y2: 1,'
                                                        'stop: 0 #fff, stop: 1 #eee); '
                                                        'border: 1px solid #bbb;'
                                                        '} '
                                                        'QPushButton:pressed { '
                                                        'background-color: qlineargradient('
                                                        'x1: 0, y1: 0, x2: 0, y2: 1,'
                                                        'stop: 0 #eee, stop: 1 #fff); '
                                                        '} '
                                                        'QPushButton:hover {'
                                                        'border: 1px solid #666;'
                                                        '}')
        self.g_setting_path_change_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_setting_path_change_button.mouseReleaseEvent = lambda event: self.get_ss_save_path()
        self.g_setting_path_change_button.setFocusPolicy(QtCore.Qt.NoFocus)
        path_layout.addWidget(self.g_setting_path_change_button)

        self.g_settings_set_path.setLayout(path_layout)

        g_settings_layout.addWidget(self.g_settings_save_file_cb)
        g_settings_layout.addWidget(self.g_settings_set_path)

        # Optimize Screenshot ------------------------------------------------------------------------------------------
        self.g_settings_optimize_ss = QCheckBox('Optimize Saved Image', self)
        self.g_settings_optimize_ss.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_optimize_ss.setFont(QFont('Arial', 10))
        self.g_settings_optimize_ss.setStyleSheet('border: none;')
        self.g_settings_optimize_ss.setToolTip('Extra pass to lower file size. Increases time to save file.')
        self.g_settings_optimize_ss.stateChanged.connect(self.cb_optimize_screenshot)
        self.g_settings_optimize_ss.setChecked(CONFIG_DICT['ss_optimize'])
        self.g_settings_optimize_ss.setFocusPolicy(QtCore.Qt.NoFocus)
        g_settings_layout.addWidget(self.g_settings_optimize_ss)

        # now we can check it after the path widget has been made
        self.g_settings_save_file_cb.setChecked(CONFIG_DICT['save_ss'])

        # Copy to clipboard cb -----------------------------------------------------------------------------------------
        self.g_settings_cpy2_clip = QCheckBox('Copy to Clipboard', self)
        self.g_settings_cpy2_clip.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_cpy2_clip.setFont(QFont('Arial', 10))
        self.g_settings_cpy2_clip.setStyleSheet('border: none;')
        self.g_settings_cpy2_clip.stateChanged.connect(self.cb_cpy2_clip_state_changed)
        # We need to set checked after we make the size limit elements
        # self.g_settings_cpy2_clip.setChecked(CONFIG_DICT['copy_2_cb'])
        self.g_settings_cpy2_clip.setFocusPolicy(QtCore.Qt.NoFocus)
        g_settings_layout.addWidget(self.g_settings_cpy2_clip)

        # Clipboard Size Limit------------------------------------------------------------------------------------------
        self.g_settings_limit_clipboard_size = QCheckBox('Limit Clipboard Size', self)
        self.g_settings_limit_clipboard_size.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_limit_clipboard_size.setFont(QFont('Arial', 10))
        self.g_settings_limit_clipboard_size.setStyleSheet('border: none;')
        self.g_settings_limit_clipboard_size.setToolTip(
            'Set the size limit of clipboard')
        self.g_settings_limit_clipboard_size.stateChanged.connect(self.cb_limit_clipboard_size_state_changed)
        self.g_settings_limit_clipboard_size.setFocusPolicy(QtCore.Qt.NoFocus)
        g_settings_layout.addWidget(self.g_settings_limit_clipboard_size)

        self.g_settings_set_size_limit = QWidget(self)
        self.g_settings_set_size_limit.setFixedHeight(30)
        self.g_settings_set_size_limit.setFixedWidth(WIDGET_WIDTH)
        self.g_settings_set_size_limit.setEnabled(CONFIG_DICT['copy_2_cb'])

        size_layout = QHBoxLayout()
        size_layout.setContentsMargins(0, 0, 0, 0)

        self.g_settings_size_val = QSpinBox()
        self.g_settings_size_val.setRange(8, 200)
        self.g_settings_size_val.setFixedWidth(75)
        self.g_settings_size_val.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_size_val.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_settings_size_val.setSuffix(" MB")
        self.g_settings_size_val.setFocusPolicy(QtCore.Qt.NoFocus)
        self.g_settings_size_val.valueChanged.connect(self.set_file_size)
        self.g_settings_size_val.setValue(CONFIG_DICT['ss_mb_size_limit'])
        self.g_settings_size_val.setEnabled(CONFIG_DICT['ss_limit_size'])

        self.g_settings_limit_clipboard_size.setChecked(CONFIG_DICT['ss_limit_size'])

        size_layout.addWidget(self.g_settings_size_val)
        size_layout.addStretch()
        self.g_settings_set_size_limit.setLayout(size_layout)

        g_settings_layout.addWidget(self.g_settings_set_size_limit)

        # Check the copy_2_cb checkbox now
        self.g_settings_cpy2_clip.setChecked(CONFIG_DICT['copy_2_cb'])

        # Show toast on monitor change ---------------------------------------------------------------------------------
        self.g_settings_show_toast_on_monitor_change = QCheckBox('Toast on Monitor Change', self)
        self.g_settings_show_toast_on_monitor_change.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_show_toast_on_monitor_change.setFont(QFont('Arial', 10))
        self.g_settings_show_toast_on_monitor_change.setStyleSheet('border: none;')
        self.g_settings_show_toast_on_monitor_change.setToolTip(
            'Show notification when the active monitor has been changed')
        self.g_settings_show_toast_on_monitor_change.stateChanged.connect(self.cb_show_toast_on_monitor_state_changed)
        self.g_settings_show_toast_on_monitor_change.setChecked(CONFIG_DICT['show_toast_on_monitor_change'])
        self.g_settings_show_toast_on_monitor_change.setFocusPolicy(QtCore.Qt.NoFocus)
        g_settings_layout.addWidget(self.g_settings_show_toast_on_monitor_change)

        # Show toast on capture ----------------------------------------------------------------------------------------
        self.g_settings_show_toast_on_capture = QCheckBox('Toast on Capture', self)
        self.g_settings_show_toast_on_capture.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_show_toast_on_capture.setFont(QFont('Arial', 10))
        self.g_settings_show_toast_on_capture.setStyleSheet('border: none;')
        self.g_settings_show_toast_on_capture.setToolTip('Show notification when screenshot has been captured')
        self.g_settings_show_toast_on_capture.stateChanged.connect(self.cb_show_toast_on_capture_state_changed)
        self.g_settings_show_toast_on_capture.setChecked(CONFIG_DICT['show_toast_on_capture'])
        self.g_settings_show_toast_on_capture.setFocusPolicy(QtCore.Qt.NoFocus)
        g_settings_layout.addWidget(self.g_settings_show_toast_on_capture)

        g_settings_layout.addStretch()
        self.g_settings.setLayout(g_settings_layout)

        # Preview ------------------------------------------------------------------------------------------------------
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.g_preview = QWidget(self)
        self.g_preview.setFixedHeight(350)
        self.g_preview.setFixedWidth(500)
        self.g_preview.setStyleSheet('border-radius: 3px')

        self.preview_label = QLabel("Preview Monitors")
        self.preview_label.setFont(instructions_title_fontt)
        preview_layout.addWidget(self.preview_label)

        monitor_layout = QHBoxLayout()
        monitor_layout.setContentsMargins(0, 0, 0, 0)
        self.g_monitors = QWidget(self)
        self.g_monitors.setMinimumHeight(20)
        self.g_monitors.setMinimumWidth(20)

        self.gen_monitor_list()

        # Add monitor buttons ------------------------------------------------------------------------------------------
        for i in range(0, len(self.monitor_buttons)):
            monitor_layout.addWidget(self.monitor_buttons[i])
        monitor_layout.addStretch()

        self.g_monitors.setLayout(monitor_layout)
        preview_layout.addWidget(self.g_monitors)

        # image --------------------------------------------------------------------------------------------------------
        self.image_preview = QWidget(self)
        self.image_preview.setFixedWidth(WIDGET_WIDTH)
        self.image_preview.setFixedHeight((1080 * WIDGET_WIDTH) / 1920)
        self.image_preview.setStyleSheet('background-color:#eee; '
                                         'border: 1px solid #bbb; '
                                         'border-radius: 2px;'
                                         'background-color:#eee; '
                                         'background-image: url({}); '
                                         'background-repeat: no-repeat; '
                                         'background-position: center center; '
                                         'border: 1px solid #bbb;'.format(DEFAULT_PREVIEW_PATH))
        self.image_preview.setFocusPolicy(QtCore.Qt.NoFocus)
        preview_layout.addWidget(self.image_preview)

        self.g_preview.setLayout(preview_layout)

        # Add Widgets to main widget -----------------------------------------------------------------------------------
        self.main_layout.addWidget(self.g_instructions)
        self.main_layout.addWidget(self.g_settings)
        self.main_layout.addWidget(self.g_preview)
        self.main_layout.addStretch()
        self.main_widget.setLayout(self.main_layout)

    def get_ss_save_path(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if file == '':
            return
        self.set_ss_save_path(file)

    def set_ss_save_path(self, file):
        self.g_settings_path_val.setText('Path: {}'.format(file))
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
                button.setFocusPolicy(QtCore.Qt.NoFocus)
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
        self.g_settings_set_path.setEnabled(self.g_settings_save_file_cb.isChecked())
        self.g_settings_optimize_ss.setEnabled(self.g_settings_save_file_cb.isChecked())
        CONFIG_DICT['save_ss'] = self.g_settings_save_file_cb.isChecked()

        if CONFIG_DICT['ss_path'] == '':
            self.init_save_path()

        update_config()

    def cb_limit_clipboard_size_state_changed(self, int):
        CONFIG_DICT['ss_limit_size'] = self.g_settings_limit_clipboard_size.isChecked()
        self.g_settings_size_val.setEnabled(self.g_settings_limit_clipboard_size.isChecked())

        update_config()

    def cb_cpy2_clip_state_changed(self, int):
        CONFIG_DICT['copy_2_cb'] = self.g_settings_cpy2_clip.isChecked()
        self.g_settings_limit_clipboard_size.setEnabled(self.g_settings_cpy2_clip.isChecked())
        self.g_settings_size_val.setEnabled(self.g_settings_cpy2_clip.isChecked() and
                                            self.g_settings_limit_clipboard_size.isChecked())
        update_config()

    def cb_show_toast_on_monitor_state_changed(self, int):
        CONFIG_DICT['show_toast_on_monitor_change'] = self.g_settings_show_toast_on_monitor_change.isChecked()
        update_config()

    def cb_show_toast_on_capture_state_changed(self, int):
        CONFIG_DICT['show_toast_on_capture'] = self.g_settings_show_toast_on_capture.isChecked()
        update_config()

    def cb_optimize_screenshot(self, int):
        CONFIG_DICT['ss_optimize'] = self.g_settings_optimize_ss.isChecked()
        update_config()

    def init_save_path(self):
        cwd = os.getcwd()
        CONFIG_DICT['ss_path'] = cwd
        update_config()

    def closeEvent(self, event):
        if os.path.exists(TEMP_IMAGE_PATH):
            os.remove(TEMP_IMAGE_PATH)

    def get_custom_hotkey(self):
        global FLAG_CAPTURING_INPUT, HOTKEY_LISTENER
        FLAG_CAPTURING_INPUT = not FLAG_CAPTURING_INPUT

        if FLAG_CAPTURING_INPUT:
            self.g_setting_hotkey_change_button.setText('Enter to Accept, Esc to cancel')
            self.g_settings_hotkey_val.setText('Enter a hotkey...')

            self.g_setting_hotkey_change_button.setStyleSheet('QPushButton { '
                                                              'background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #e74c3c, stop: 1 #c0392b); border: 1px solid #bbb;'
                                                              '} '
                                                              'QPushButton:pressed { '
                                                              'background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #c0392b, stop: 1 #e74c3c); '
                                                              '} '
                                                              'QPushButton:hover {'
                                                              'border: 1px solid #666;'
                                                              '}')
            print("trying to kill process")
            try:
                HOTKEY_LISTENER.kill()
            except Exception as e:
                print(e)

    def set_file_size(self):
        CONFIG_DICT['ss_mb_size_limit'] = self.g_settings_size_val.value()
        update_config()


class ImageResizeTab(QWidget):
    main_widget = None

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.main_layout = QVBoxLayout()
        self.main_widget = QWidget(self)

        file_size_font = QFont('Arial', 10)
        file_size_font.setBold(True)

        self.preview_label = QLabel("Image Size")
        self.preview_label.setFont(file_size_font)
        self.main_layout.addWidget(self.preview_label)

        self.g_settings_size_val = QSpinBox()
        self.g_settings_size_val.setRange(1, 200)
        self.g_settings_size_val.setFixedWidth(75)
        self.g_settings_size_val.setFixedHeight(FIELD_HEIGHT)
        self.g_settings_size_val.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_settings_size_val.setSuffix(" MB")
        # self.g_settings_size_val.valueChanged.connect(self.set_file_size)
        self.g_settings_size_val.setValue(8)

        self.main_layout.addWidget(self.g_settings_size_val)

        self.main_widget.setLayout(self.main_layout)

if __name__ == '__main__':
    freeze_support()
    print("Current Proc", current_process().name)
    print(os.getpid(), "in main gui")
    HOTKEY_LISTENER = HotkeyListener()
    HOTKEY_LISTENER.start()

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
    window.installEventFilter(window)
    start_gui()

