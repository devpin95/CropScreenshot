from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QPushButton, QLabel, QCheckBox
from PyQt5.QtGui import QFont, QCursor
from PyQt5 import QtCore, Qt
import os
from io import BytesIO
import win32clipboard as cb
import time
from PIL import ImageGrab
import win32gui, win32con

# https://stackoverflow.com/questions/49043570/pyqt5-qfiledialog-does-not-work-with-pywinauto-import
import sys
sys.coinit_flags = 2  # STA
from pywinauto import Desktop

import constants


class CustomComboBox(QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def showPopup(self):
        self.popupWork()
        self.popupAboutToBeShown.emit()
        super(CustomComboBox, self).showPopup()

    def popupWork(self):
        pass


class WindowCaptureTab(QWidget):
    main_widget = None

    focused = False

    req_height = constants.FIELD_HEIGHT * 2 + constants.APP_BOTTOM_PADDING
    req_width = constants.APP_WIDTH
    height_correction = 0

    window_filter_list = [
        'Taskbar',
        'Program Manager'
    ]
    windows = []
    win_names = []
    current_selected_window = None

    first_load = True
    first_index_change = True

    window_combo_ready = False

    def __init__(self, parent, config):
        super(QWidget, self).__init__(parent)

        self.config = config

        self.main_layout = QVBoxLayout()
        self.main_layout.addStretch()
        self.main_widget = QWidget(self)

        self.main_widget.setStyleSheet('background-color: #f00;')

        self.main_widget.setStyleSheet("""
                                       QWidget {
                                            background-color:#34495e;
                                            color: #efefef;
                                       }
                                       QToolTip {
                                            color: #efefef;
                                            background-color: #1E2B37;
                                            border: 1px solid #111;
                                        }
                                       """)

        # self.window_picker_label = QLabel("Select Window")
        # self.window_picker_label.setFixedHeight(constants.FIELD_HEIGHT)
        # self.window_picker_label.setFont(QFont('Arial', 10))
        # self.main_layout.addWidget(self.window_picker_label)

        # WINDOW PICKER GROUP ------------------------------------------------------------------------------------------
        self.window_picker_group = QWidget()
        self.window_picker_group.layout = QHBoxLayout()

        self.window_picker_group.setFixedWidth(constants.WIDGET_WIDTH)
        self.window_picker_group.setFixedHeight(constants.FIELD_HEIGHT)

        self.window_combo = CustomComboBox()
        self.window_combo.setFixedHeight(constants.FIELD_HEIGHT)
        self.window_combo.view().window().setWindowFlags(Qt.Qt.Popup | Qt.Qt.FramelessWindowHint)
        self.window_combo.view().window().setAttribute(Qt.Qt.WA_TranslucentBackground)

        self.window_combo.setStyleSheet("""
                                        QComboBox {
                                            border: 1px solid #bbb;
                                            background-color: qlineargradient(
                                                x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #fff, stop: 1 #aaa);
                                            color: #111;
                                            border-radius: 2px;
                                            padding-left: 10px;
                                            padding-right: 15px;
                                        }
                                        QComboBox:hover {
                                            border: 1px solid #111;
                                        }
                                        QComboBox::drop-down {
                                            border: 0px;
                                        }
                                        QComboBox::down-arrow {
                                            image: url(assets/dropdown-arrow.png);
                                            width: 10px;
                                            height: 10px;
                                            margin-right: 15px;
                                        }
                                        QComboBox::on {
                                            border-bottom-left-radius: 0;
                                            border-bottom-right-radius: 0;
                                        }
                                        QComboBox QAbstractItemView {                                        
                                            border: 1px solid #111;
                                            background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #34495e, stop: 1 #2c3e50);
                                            color: #efefef;
                                            selection-background-color: #2980b9;
                                            selection-color: #efefef;
                                            border-bottom-left-radius: 5px;
                                            border-bottom-right-radius: 5px;
                                            outline: none;
                                        }
                                        """)

        self.window_combo.setFont(QFont('Arial', 10))
        self.window_combo.addItem('Select a window...')

        # self.window_combo.activated.connect(self._index_change)
        self.window_combo.currentIndexChanged.connect(self._index_change)
        self.window_combo.currentTextChanged.connect(self._update_current_text)

        # self.window_combo.popupWork = self._populatePopup
        self._populatePopup()

        self.window_picker_group.layout.addWidget(self.window_combo)

        # REFRESH BUTTON
        self.window_refresh = QPushButton()
        self.window_refresh.setToolTip("Refresh window list")
        self.window_refresh.setFixedWidth(constants.FIELD_HEIGHT)
        self.window_refresh.setFixedHeight(constants.FIELD_HEIGHT)
        self.window_refresh.setStyleSheet("""
                                          QPushButton {
                                            border-radius: 2px;
                                            background-image: url(assets/refresh.png);
                                            background-position: center center;
                                            background-color: qlineargradient(
                                                x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #fff, stop: 1 #aaa);
                                            border: 1px solid #bbb;
                                          }
                                          QPushButton:pressed {
                                            background-color: qlineargradient(
                                                x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #ccc, stop: 1 #ccc); 
                                          }
                                          QPushButton:hover {
                                            border: 1px solid #111;
                                          }
                                          """)
        self.window_refresh.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.window_refresh.clicked.connect(self._populatePopup)

        self.window_picker_group.layout.addWidget(self.window_refresh)

        # FOCUS BUTTON
        self.window_focus = QPushButton()
        self.window_focus.setToolTip("Bring selected window to front")
        self.window_focus.setFixedWidth(constants.FIELD_HEIGHT)
        self.window_focus.setFixedHeight(constants.FIELD_HEIGHT)
        self.window_focus.setStyleSheet("""
                                                  QPushButton {
                                                    border-radius: 2px;
                                                    background-image: url(assets/bring-forward.png);
                                                    background-position: center center;
                                                    background-color: qlineargradient(
                                                        x1: 0, y1: 0, x2: 0, y2: 1,
                                                        stop: 0 #fff, stop: 1 #aaa);
                                                    border: 1px solid #bbb;
                                                  }
                                                  QPushButton:pressed {
                                                    background-color: qlineargradient(
                                                        x1: 0, y1: 0, x2: 0, y2: 1,
                                                        stop: 0 #ccc, stop: 1 #ccc); 
                                                  }
                                                  QPushButton:hover {
                                                    border: 1px solid #111;
                                                  }
                                                  """)
        self.window_focus.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.window_focus.clicked.connect(lambda: self._bring_forward(self.window_combo.currentText()))
        self.window_picker_group.layout.addWidget(self.window_focus)
        self.window_focus.hide()

        # CAPTURE BUTTON
        self.window_capture = QPushButton()
        self.window_capture.setToolTip("Capture window image")
        self.window_capture.setFixedWidth(constants.FIELD_HEIGHT)
        self.window_capture.setFixedHeight(constants.FIELD_HEIGHT)
        self.window_capture.setStyleSheet("""
                                                          QPushButton {
                                                            border-radius: 2px;
                                                            background-image: url(assets/capture.png);
                                                            background-position: center center;
                                                            background-color: qlineargradient(
                                                                x1: 0, y1: 0, x2: 0, y2: 1,
                                                                stop: 0 #fff, stop: 1 #aaa);
                                                            border: 1px solid #bbb;
                                                          }
                                                          QPushButton:pressed {
                                                            background-color: qlineargradient(
                                                                x1: 0, y1: 0, x2: 0, y2: 1,
                                                                stop: 0 #ccc, stop: 1 #ccc); 
                                                          }
                                                          QPushButton:hover {
                                                            border: 1px solid #111;
                                                          }
                                                          """)
        self.window_capture.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.window_capture.clicked.connect(lambda: self._capture_window(self.window_combo.currentText()))
        self.window_picker_group.layout.addWidget(self.window_capture)
        self.window_capture.hide()

        self.window_picker_group.layout.setContentsMargins(0, 0, 0, 0)
        self.window_picker_group.setLayout(self.window_picker_group.layout)

        self.main_layout.addWidget(self.window_picker_group)

        # ACTION GROUP -------------------------------------------------------------------------------------------------
        self.settings_group = QWidget()
        self.settings_group.layout = QFormLayout()
        self.settings_group.layout.setContentsMargins(0, 0, 0, 0)
        self.settings_group.setFixedWidth(constants.WIDGET_WIDTH)
        self.settings_group.setFixedHeight(constants.FIELD_HEIGHT)
        self.settings_group.setStyleSheet("""
                                            QGroupBox{
                                                border: none;
                                                margin-top: 15px;
                                            }
                                            """)
        # self.settings_group.setStyleSheet('background-color: #2c3e50;')

        self.settings_group.window_state_label = QLabel("Maintain window state")
        self.settings_group.window_state_label.setFixedHeight(constants.FIELD_HEIGHT)
        self.settings_group.window_state_label.setFont(QFont('Arial', 10))
        self.settings_group.window_state_label.setFixedWidth(150)
        self.settings_group.window_state_label.setToolTip("Return the window to the state it was in before capture.")

        self.settings_group.window_state_checkbox = QCheckBox()
        self.settings_group.window_state_checkbox.setFixedHeight(constants.FIELD_HEIGHT)
        self.settings_group.window_state_checkbox.setToolTip("Return the window to the state it was in before capture.")

        self.settings_group.layout.addRow(self.settings_group.window_state_label, self.settings_group.window_state_checkbox)

        self.settings_group.setLayout(self.settings_group.layout)
        self.main_layout.addWidget(self.settings_group)

        self.main_layout.addStretch()
        self.main_widget.setLayout(self.main_layout)

    def _index_change(self, index):
        if index != -1 and index != 0 and self.window_combo_ready and self.first_index_change:
            print("removing empyte")
            self.window_combo.removeItem(0)
            self.first_index_change = False
            self.window_focus.show()
            self.window_capture.show()

    def _populatePopup(self):
        self.window_combo.clear()

        if self.first_load:
            self.window_combo.addItem(' ')
            self.first_load = False

        self.windows = Desktop(backend="uia").windows()
        self.win_names = []
        for w in self.windows:
            if not w.window_text() == '' and w.window_text() not in self.window_filter_list:
                self.win_names.append(w.window_text())

        self.win_names = sorted(self.win_names, key=str.lower)

        for win in self.win_names:
            self.window_combo.addItem(win)

        win32gui.EnumWindows(self._enum_windows, None)
        self.window_combo_ready = True

    def _enum_windows(self, hwnd, results):
        pass
        if not win32gui.GetWindowText(hwnd) == '' and win32gui.IsWindowVisible(hwnd):
            if win32gui.GetWindowText(hwnd) in self.win_names:
                self.win_names.append(win32gui.GetWindowText(hwnd))

    def _update_current_text(self):
        self.current_selected_window = self.window_combo.currentText()

    def _find_window_handle(self, win_name):
        target_window_found = False
        target_window_handle = ''

        def enum_windows_callback(hwnd, results):
            nonlocal target_window_found, target_window_handle

            if target_window_found:
                return
            if not win32gui.GetWindowText(hwnd) == '' and win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(
                    hwnd) == win_name:
                target_window_found = True
                target_window_handle = hwnd

        win32gui.EnumWindows(enum_windows_callback, None)

        return target_window_handle if target_window_found else None

    def _bring_forward(self, win_name):
        print("bringing forward", win_name)

        target_window_handle = self._find_window_handle(win_name)

        if target_window_handle is None:
            print("Could not find window...")
            return

        if win32gui.IsIconic(target_window_handle):
            win32gui.ShowWindow(target_window_handle, 9)

        win32gui.SetForegroundWindow(target_window_handle)

    def _capture_window(self, win_name):
        print("capturing forward", win_name)

        target_window_handle = self._find_window_handle(win_name)

        if target_window_handle is None:
            print("Could not find window...")
            return

        starting_bbox = win32gui.GetWindowRect(target_window_handle)
        ox, oy, c, d = starting_bbox
        owidth = c - ox
        oheight = d - oy

        needs_move = ox < 0 or oy < 0

        # print(target_window_handle, win32gui.GetWindowText(target_window_handle), starting_bbox, (ox, oy, owidth, oheight))
        try:
            minimized = win32gui.IsIconic(target_window_handle)

            nx = ox
            ny = oy
            nwidth = owidth
            nheight = oheight

            if minimized:
                win32gui.ShowWindow(target_window_handle, 9)
                shifted_bbox = win32gui.GetWindowRect(target_window_handle)
                nx, ny, c, d = shifted_bbox
                nwidth = c - nx
                nheight = d - ny

                needs_move = nx < 0 or ny < 0

            win32gui.ShowWindow(target_window_handle, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(target_window_handle)

            if needs_move:
                win32gui.MoveWindow(target_window_handle, 0, 0, nwidth, nheight, True)
                # print(win32gui.GetWindowRect(target_window_handle))

            time.sleep(1)

            wind_rect = win32gui.GetWindowRect(target_window_handle)
            a, b, c, d = wind_rect

            # get the state of the window so we can decide how to trim the rect
            tup = win32gui.GetWindowPlacement(target_window_handle)
            wind_state = tup[1]

            if wind_state == win32con.SW_SHOWMAXIMIZED:
                wind_rect = (a + constants.WINDOWS_RECT_BORDER,
                             b + constants.WINDOWS_RECT_BORDER,
                             c - constants.WINDOWS_RECT_BORDER,
                             d - constants.WINDOWS_RECT_BORDER)

            elif wind_state == win32con.SW_SHOWNORMAL:
                wind_rect = (a + constants.WINDOWS_RECT_BORDER,
                             b + 1,
                             c - constants.WINDOWS_RECT_BORDER,
                             d - constants.WINDOWS_RECT_BORDER)

            img = ImageGrab.grab(wind_rect)
            img.show()

            if self.settings_group.window_state_checkbox.isChecked():
                if needs_move:
                    win32gui.MoveWindow(target_window_handle, nx, ny, nwidth, nheight, True)

                if minimized:
                    win32gui.ShowWindow(target_window_handle, 6)

        except:
            print("Could not show " + win32gui.GetWindowText(target_window_handle))
