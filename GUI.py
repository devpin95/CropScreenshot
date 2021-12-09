# pyinstaller -F -i C:\Users\devpi\Documents\projects\CropScreenshot\assets\icon-pink-256x256.ico -n PowerSS --debug GUI.py

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QGraphicsDropShadowEffect
from PyQt5.QtGui import QIcon, QCloseEvent, QFont, QCursor, QMouseEvent, QColor
from PyQt5 import QtCore, Qt
import sys
from multiprocessing import Process, current_process, freeze_support
from threading import RLock
from CaptureScreen import start_listening_for_hotkeys
import json
import ctypes
import os
import globals
import constants
from KeyEventListener import KeyEventListener
import glob
import traceback

# tabs
from ScreenCaptureTab import ScreenCaptureTab
from ImageResizeTab import ImageResizeTab
from ImageCropTab import ImageCropTab
from WindowCaptureTab import WindowCaptureTab

# https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
# for setting the taskbar icon in windows
myappid = 'devin.projects.powerss.1'  # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

GLOBAL_DICT = {"hello": "World!"}
DICT_LOCK = RLock()

WINDOW_TITLE = 'PowerSS'
HOTKEY_LISTENER = None


def start_gui():
    sys.excepthook = excepthook
    sys.exit(app.exec_())


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    app.quit()
    # or QtWidgets.QApplication.exit(0)


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

    def __init__(self, config):
        super().__init__()

        self.config = config

        # self.setStyleSheet("padding: 5px 10px 5px 10px")
        self.setFixedWidth(constants.APP_WIDTH)
        self.setFixedHeight(constants.APP_HEIGHT + 50)
        self.setWindowTitle(WINDOW_TITLE)
        self.setDocumentMode(True)
        self.setAutoFillBackground(False)
        # self.setAcceptDrops(True)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        #
        # window_dropshadow = QGraphicsDropShadowEffect()
        # window_dropshadow.setYOffset(1)
        # window_dropshadow.setXOffset(0)
        # window_dropshadow.setColor(QColor(0, 0, 0))
        # window_dropshadow.setBlurRadius(25)
        #
        # self.setGraphicsEffect(window_dropshadow)

        self.setStyleSheet(""" 
                           QMainWindow {
                                background-image: url(assets/background-gradient.png);
                                background-position: top;
                                background-repeat: repeat-x;
                                background-color: #34495e;
                                border: 1px solid #111;
                           }                          
                           QTabWidget {
                                background-color: transparent;
                                border:none;
                                padding: 0;
                                margin: 0;
                           }
                           QTabWidget QTabBar {
                                background-color: transparent;
                           }
                           QTabBar::tab {
                                background-color: transparent;
                                padding: 7px 10px 5px 10px;
                                min-width: 50px;
                                color: #aaa;
                                font-weight: normal;
                           }
                           QTabBar::tab:selected {
                                /*font-weight: bold;*/
                                /*background: qradialgradient(cx:0.5, cy:0, radius: 1,
                                                            fx:0.5, fy:0, stop:0 #aaffffff, stop:0.4 transparent);*/
                                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                            stop: 0 #fff, stop: 0.3 #fff,
                                                            stop: 0.3 #fff, stop: 1 #bfbfbf);
                                /*background-color: #efefef;*/
                                color: #111;
                                border-bottom-right-radius: 2px;
                                border-bottom-left-radius: 2px;
                                border-top: 1px solid #aaa;
                           }
                            
                           QTabBar::tab:!selected {
                                color: #95a5a6;
                           }
                           QTabWidget::pane {
                                background-color: #34495e;
                                color: #efefef;
                                border: 1px solid #111;
                                border-top: none;
                           }
                           """)

        # self.setWindowIcon(app_icon)

        # self.setAcceptDrops(True)

        self.main_widget = QWidget()
        self.main_widget.layout = QVBoxLayout()
        self.main_widget.layout.setSpacing(0)
        self.main_widget.layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setMinimumWidth(constants.APP_WIDTH)
        self.main_widget.setMinimumHeight(constants.APP_HEADER_HEIGHT)
        # self.main_widget.setAcceptDrops(True)

        # self.main_widget.setStyleSheet('background-color:#0f0;')
        # self.main_widget.dragEnterEvent = self.dragEnterEvent
        # self.main_widget.dragLeaveEvent = self.dragLeaveEvent
        # self.main_widget.dropEvent = self.dropEvent

        self.header = QWidget()
        self.header.layout = QHBoxLayout()
        self.header.layout.setContentsMargins(0, 0, 0, 0)
        self.header.setFixedWidth(constants.APP_WIDTH)
        self.header.setFixedHeight(50)
        self.header.setStyleSheet('''
                                    QWidget {
                                        border: none;
                                        background-color: #1E2B37;
                                        border: 1px solid #111;
                                    }
                                    QPushButton {
                                        color: #aaa;
                                        outline: none;
                                        border: none;
                                    }
                                    QPushButton:hover {
                                        color: #efefef;
                                    }
                                  ''')

        dropshadow = QGraphicsDropShadowEffect()
        dropshadow.setYOffset(1)
        dropshadow.setXOffset(0)
        dropshadow.setColor(QColor(0, 0, 0))
        dropshadow.setBlurRadius(25)

        self.header.setGraphicsEffect(dropshadow)

        self.header.mousePressEvent = self.cmousePressEvent
        self.header.mouseReleaseEvent = self.cmouseReleaseEvent
        self.header.mouseMoveEvent = self.cmouseMoveEvent

        self.header.image = QWidget()
        self.header.image.setFixedHeight(50)
        self.header.image.setFixedWidth(137)
        self.header.image.setStyleSheet('''
                                        background-image: url(assets/header-icon.png);
                                        background-repeat: none;
                                        background-position: left;
                                        background-color: transparent;
                                        border: none;
                                        margin-left: 7px;
                                        ''')
        self.header.layout.addWidget(self.header.image)
        self.header.layout.setAlignment(self.header.image, Qt.Qt.AlignLeft)

        self.header.action_items = QWidget()
        self.header.action_items.layout = QHBoxLayout()
        self.header.action_items.setStyleSheet('border: none; background: transparent;')

        # MINIMIZE BUTTON
        self.header.action_items.minimize_btn = QPushButton('-')
        self.header.action_items.minimize_btn.setFixedWidth(30)
        self.header.action_items.minimize_btn.setFixedHeight(30)
        self.header.action_items.minimize_btn.setFont(QFont('Arial', 15))
        self.header.action_items.minimize_btn.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.header.action_items.minimize_btn.clicked.connect(self.showMinimized)
        self.header.action_items.layout.addWidget(self.header.action_items.minimize_btn)

        # CLOSE BUTTON
        self.header.action_items.close_btn = QPushButton('x')
        self.header.action_items.close_btn.setFixedWidth(30)
        self.header.action_items.close_btn.setFixedHeight(30)
        self.header.action_items.close_btn.setFont(QFont('Arial', 15))
        self.header.action_items.close_btn.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.header.action_items.close_btn.clicked.connect(self.close)
        self.header.action_items.layout.addWidget(self.header.action_items.close_btn)

        self.header.action_items.setLayout(self.header.action_items.layout)
        self.header.layout.addWidget(self.header.action_items)
        self.header.layout.setAlignment(self.header.action_items, Qt.Qt.AlignRight)

        self.header.setLayout(self.header.layout)

        self.main_widget.layout.addWidget(self.header)

        self.tabs = QTabWidget()
        self.tabs.tabBar().setCursor(QtCore.Qt.PointingHandCursor)

        self.tabs.currentChanged.connect(self.tab_change_event)
        self.tabs.tabBarClicked.connect(lambda: globals.keyEvent.raise_explicit_press_event(constants.ESCAPE_KEY_CODE, params={'proc_start': False}, ignore=True))

        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tabs.resize(constants.APP_WIDTH, constants.APP_HEIGHT - 100)

        self.screen_cap_tab = ScreenCaptureTab(self, self.config, HOTKEY_LISTENER)
        self.image_resize_tab = ImageResizeTab(self, self.config)
        self.image_crop_tab = ImageCropTab(self, self.config)
        self.window_capture_tab = WindowCaptureTab(self, self.config)

        self.tab_list = []
        self.tab_list.append(self.screen_cap_tab)
        self.tab_list.append(self.image_resize_tab)
        self.tab_list.append(self.image_crop_tab)
        self.tab_list.append(self.window_capture_tab)
        self.current_focus_index = 0
        self.previous_focus_index = -1

        self.tab1_ui()
        self.tab2_ui()
        self.tab3_ui()
        self.tab4_ui()

        self.tabs.setCurrentIndex(3)

        self.main_widget.layout.addWidget(self.tabs)
        self.main_widget.layout.setAlignment(self.tabs, Qt.Qt.AlignTop)

        self.main_widget.setLayout(self.main_widget.layout)
        self.setCentralWidget(self.main_widget)
        self.show()

    def tab1_ui(self):
        # Screen Capture tab
        self.tab1.layout = QVBoxLayout(self)

        self.screen_cap_tab.resize_window = self.resize_window
        # self.screen_cap_tab.setAcceptDrops(False)
        self.tab1.layout.addWidget(self.screen_cap_tab.main_widget)
        self.tab1.setLayout(self.tab1.layout)

        self.tabs.addTab(self.tab1, "Screen Capture")

    def tab2_ui(self):
        self.tabs.addTab(self.tab2, "Resize Image")

        self.tab2.layout = QVBoxLayout(self)

        self.image_resize_tab.resize_window = self.resize_window
        # self.image_resize_tab.setAcceptDrops(True)
        self.tab2.layout.addWidget(self.image_resize_tab.main_widget)
        self.tab2.setLayout(self.tab2.layout)

    def tab3_ui(self):
        self.tabs.addTab(self.tab3, "Crop Image")

        self.tab3.layout = QVBoxLayout(self)

        self.image_crop_tab.resize_window = self.resize_window
        # self.image_crop_tab.setAcceptDrops(True)
        self.tab3.layout.addWidget(self.image_crop_tab.main_widget)
        self.tab3.setLayout(self.tab3.layout)

    def tab4_ui(self):
        self.tabs.addTab(self.tab4, "Window Capture")

        self.tab4.layout = QVBoxLayout(self)

        self.window_capture_tab.resize_window = self.resize_window
        # self.window_capture_tab.setAcceptDrops(False)
        self.tab4.layout.addWidget(self.window_capture_tab.main_widget)
        self.tab4.setLayout(self.tab4.layout)

    def tab_change_event(self, index):
        if index == 1 and globals.flag_capturing_input:
            self.capture_hotkey('esc')

        self._set_tab_focus(index)
        tab = self.tab_list[self.current_focus_index]
        self.resize_window(tab.req_height + tab.height_correction, tab.req_width)

    def _set_tab_focus(self, focus_index):
        self.previous_focus_index = self.current_focus_index
        self.current_focus_index = focus_index

        self.tab_list[self.previous_focus_index].focused = False
        self.tab_list[self.current_focus_index].focused = True

    def eventFilter(self, obj, event):
        # eventFilter for the main window
        if event.type() == QtCore.QEvent.KeyPress:
            globals.keyEvent.raise_explicit_press_event(event.key())

        elif event.type() == QtCore.QEvent.KeyRelease:
            globals.keyEvent.raise_explicit_release_event(event.key())

        # elif event.type() == QtCore.QEvent.DragEnter:
        #     print("drag enter!")
        #
        # elif event.type() == QtCore.QEvent.DragLeave:
        #     print("drag Leave!")
        #
        # elif event.type() == QtCore.QEvent.Drop:
        #     print("Drop!")

        return super(Window, self).eventFilter(obj, event)

    def resize_window(self, height, width=constants.APP_WIDTH):
        self.main_widget.setFixedHeight(height + constants.APP_HEADER_HEIGHT)
        self.setFixedHeight(height + constants.APP_HEADER_HEIGHT)
        self.setFixedWidth(width)
        self.header.setFixedWidth(width)

    def cmousePressEvent(self, a0: QMouseEvent) -> None:
        self.oldPosition = a0.globalPos()

    def cmouseReleaseEvent(self, a0: QMouseEvent) -> None:
        pass

    def cmouseMoveEvent(self, a0: QMouseEvent) -> None:
        delta = self.oldPosition - a0.globalPos()
        self.move(self.x() - delta.x(), self.y() - delta.y())
        self.oldPosition = a0.globalPos()

    def closeEvent(self, a0: QCloseEvent) -> None:
        print("Cleaning up...")

        print("cleaning up temp files...")
        files = glob.glob(os.getcwd() + '\\temp\\*')
        for file in files:
            try:
                os.remove(file)
            except:
                print("could not remove temp file " + file)

        print("killing child processes...")
        try:
            HOTKEY_LISTENER.kill()
        except:
            print("Could not kill hotkey listener")

        print("Done cleaning...")

        self.deleteLater()


if __name__ == '__main__':
    freeze_support()

    # make sure a temp dir exists
    if not os.path.isdir(os.getcwd() + '\\temp'):
        os.mkdir(os.getcwd() + '\\temp')

    # set up the process that will listen for the screenshot hotkey
    print("Current Proc", current_process().name)
    print(os.getpid(), "in main gui")
    HOTKEY_LISTENER = HotkeyListener()
    HOTKEY_LISTENER.start()

    # set up an event that will notify listeners of a key press
    globals.keyEvent = KeyEventListener()

    # load config file
    with open(constants.CONFIG_FILE) as config:
        CONFIG_DICT = json.load(config)

    app = QApplication([])

    app_icon = QIcon()
    app_icon.addFile('./assets/icon-16x16.png', QtCore.QSize(16, 16))
    app_icon.addFile('./assets/icon-24x24.png', QtCore.QSize(24, 24))
    app_icon.addFile('./assets/icon-32x32.png', QtCore.QSize(32, 32))
    app_icon.addFile('./assets/icon-48x48.png', QtCore.QSize(48, 48))
    app_icon.addFile('./assets/icon-256x256.png', QtCore.QSize(256, 256))

    app.setWindowIcon(app_icon)

    window = Window(CONFIG_DICT)
    window.installEventFilter(window)

    start_gui()
