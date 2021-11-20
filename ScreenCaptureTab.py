from PyQt5.QtWidgets import QLabel, QPushButton, QFileDialog, QWidget, QVBoxLayout, QCheckBox, QHBoxLayout, QSpinBox, QErrorMessage
from PyQt5.QtGui import QFont, QCursor
from PyQt5 import QtCore
import mss
from PIL import Image
import os
from filelock import FileLock

from QtKeyValueToKeyboardValue import qt_modifier_to_keyboard
import constants
import utilities as utils
import globals


class ScreenCaptureTab(QWidget):
    main_layout = None
    main_widget = None

    focused = False

    key_list = []

    FLOCK = FileLock(constants.CONFIG_LOCK_FILE)

    def __init__(self, parent, config, hotkey_listener):
        super(QWidget, self).__init__(parent)

        self.config = config
        self.hotkey_listener = hotkey_listener
        globals.keyEvent.subscribe_to_press_event(self.capture_hotkey)

        self.monitor_buttons = []

        self.main_layout = QVBoxLayout()
        self.main_widget = QWidget(self)
        # self.main_widget.setFixedWidth(APP_WIDTH)
        # self.main_widget.setFixedHeight(APP_HEIGHT)

        # Instruction --------------------------------------------------------------------------------------------------
        self.g_instructions = QWidget(self)
        self.g_instructions.setFixedWidth(constants.WIDGET_WIDTH)
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
            'ctrl+alt+[monitor number] - Set active monitor\n{} - Take screenshot'.format(self.config['ss_hotkey']))
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
        self.g_settings.setFixedWidth(constants.WIDGET_WIDTH)
        self.g_settings.setFixedHeight(325)
        self.g_settings.setStyleSheet('padding: 0; margin: 0;')
        # self.g_settings.setStyleSheet('QWidget{background-color:#f00;} QWidget QCheckBox {padding: 0; margin: 0; background-color: #0f0;}')

        g_settings_layout = QVBoxLayout()
        g_settings_layout.setContentsMargins(0, 0, 0, 0)

        # Hotkey -------------------------------------------------------------------------------------------------------
        self.g_settings_set_hotkey_label = QLabel('Capture Hotkey', self)
        self.g_settings_set_hotkey_label.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_settings_set_hotkey_label.setFont(QFont('Arial', 10))
        self.g_settings_set_hotkey_label.setStyleSheet("border: none;")
        g_settings_layout.addWidget(self.g_settings_set_hotkey_label)

        self.g_settings_set_hotkey = QWidget(self)
        self.g_settings_set_hotkey.setFixedHeight(30)
        self.g_settings_set_hotkey.setFixedWidth(constants.WIDGET_WIDTH)
        self.g_settings_set_hotkey.setStyleSheet("""
                                                QLabel{
                                                    padding-left: 5px;
                                                    border: 1px solid #bbb;
                                                    border-radius: 2px;
                                                }
                                                """)

        hotkey_layout = QHBoxLayout()
        hotkey_layout.setContentsMargins(0, 0, 0, 0)

        self.g_settings_hotkey_val = QLabel(self.config['ss_hotkey'], self)
        self.g_settings_hotkey_val.setFixedHeight(constants.FIELD_HEIGHT)

        hotkey_layout.addWidget(self.g_settings_hotkey_val)

        self.g_setting_hotkey_change_button = QPushButton("Set")
        self.g_setting_hotkey_change_button.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_setting_hotkey_change_button.setFocusPolicy(QtCore.Qt.NoFocus)
        # self.g_setting_hotkey_change_button.setFixedWidth(100)
        self.g_setting_hotkey_change_button.setStyleSheet("""
                                                        QPushButton {
                                                            border-radius: 2px;
                                                            background-color: qlineargradient(
                                                                x1: 0, y1: 0, x2: 0, y2: 1,
                                                                stop: 0 #fff, stop: 1 #eee);
                                                            border: 1px solid #bbb;
                                                        }
                                                        QPushButton:pressed {
                                                            background-color: qlineargradient(
                                                                x1: 0, y1: 0, x2: 0, y2: 1,
                                                                stop: 0 #eee, stop: 1 #fff); 
                                                        }
                                                        QPushButton:hover {
                                                            border: 1px solid #666;
                                                        }
                                                        """)
        self.g_setting_hotkey_change_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_setting_hotkey_change_button.clicked.connect(self.get_custom_hotkey)
        hotkey_layout.addWidget(self.g_setting_hotkey_change_button)

        self.g_settings_set_hotkey.setLayout(hotkey_layout)
        g_settings_layout.addWidget(self.g_settings_set_hotkey)

        # Save SS Checkbox ---------------------------------------------------------------------------------------------
        self.g_settings_save_file_cb = QCheckBox('Save Screenshot', self)
        self.g_settings_save_file_cb.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_settings_save_file_cb.setFont(QFont('Arial', 10))
        self.g_settings_save_file_cb.setStyleSheet("border: none;")
        self.g_settings_save_file_cb.stateChanged.connect(self.cb_save_file_state_changed)
        self.g_settings_save_file_cb.setFocusPolicy(QtCore.Qt.NoFocus)
        # Checked after we create the path widget

        if self.config['ss_path'] == '':
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
        self.g_settings_set_path.setFixedWidth(constants.WIDGET_WIDTH)
        self.g_settings_set_path.setStyleSheet("""
                                               QLabel {
                                                    padding-left: 5px;
                                                    border: 1px solid #bbb;
                                                    border-radius: 2px;
                                               }
                                               QLabel:hover {
                                                    border:1px solid #000;
                                               }
                                               """)
        self.g_settings_set_path.setEnabled(self.config['save_ss'])

        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)

        self.g_settings_path_val = QLabel("Path: {}".format(self.config['ss_path']), self)
        self.g_settings_path_val.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_settings_path_val.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_settings_path_val.mouseReleaseEvent = lambda event: os.startfile(self.config['ss_path'])

        path_layout.addWidget(self.g_settings_path_val)

        self.g_setting_path_change_button = QPushButton("")
        self.g_setting_path_change_button.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_setting_path_change_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.g_setting_path_change_button.setFixedWidth(constants.FIELD_HEIGHT)
        self.g_setting_path_change_button.setStyleSheet("""
                                                    QPushButton {
                                                        border-radius: 2px;
                                                        background-image: url(assets/folder.png);
                                                        background-repeat: no-repeat;
                                                        background-position: center center;
                                                        background-color: qlineargradient(
                                                            x1: 0, y1: 0, x2: 0, y2: 1,
                                                            stop: 0 #fff, stop: 1 #eee);
                                                        border: 1px solid #bbb;
                                                    }
                                                    QPushButton:pressed {
                                                        background-color: qlineargradient(
                                                            x1: 0, y1: 0, x2: 0, y2: 1,
                                                            stop: 0 #eee, stop: 1 #fff);
                                                    }
                                                    QPushButton:hover {
                                                        border: 1px solid #666;
                                                    }""")
        self.g_setting_path_change_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_setting_path_change_button.mouseReleaseEvent = lambda event: self.get_ss_save_path()
        path_layout.addWidget(self.g_setting_path_change_button)

        self.g_settings_set_path.setLayout(path_layout)

        g_settings_layout.addWidget(self.g_settings_save_file_cb)
        g_settings_layout.addWidget(self.g_settings_set_path)

        # Optimize Screenshot ------------------------------------------------------------------------------------------
        self.g_settings_optimize_ss = QCheckBox('Optimize Saved Image', self)
        self.g_settings_optimize_ss.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_settings_optimize_ss.setFont(QFont('Arial', 10))
        self.g_settings_optimize_ss.setStyleSheet('border: none;')
        self.g_settings_optimize_ss.setToolTip('Extra pass to lower file size. Increases time to save file.')
        self.g_settings_optimize_ss.stateChanged.connect(self.cb_optimize_screenshot)
        self.g_settings_optimize_ss.setChecked(self.config['ss_optimize'])
        self.g_settings_optimize_ss.setFocusPolicy(QtCore.Qt.NoFocus)
        g_settings_layout.addWidget(self.g_settings_optimize_ss)

        # now we can check it after the path widget has been made
        self.g_settings_save_file_cb.setChecked(self.config['save_ss'])

        # Copy to clipboard cb -----------------------------------------------------------------------------------------
        self.g_settings_cpy2_clip = QCheckBox('Copy to Clipboard', self)
        self.g_settings_cpy2_clip.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_settings_cpy2_clip.setFont(QFont('Arial', 10))
        self.g_settings_cpy2_clip.setStyleSheet('border: none;')
        self.g_settings_cpy2_clip.stateChanged.connect(self.cb_cpy2_clip_state_changed)
        # We need to set checked after we make the size limit elements
        # self.g_settings_cpy2_clip.setChecked(CONFIG_DICT['copy_2_cb'])
        self.g_settings_cpy2_clip.setFocusPolicy(QtCore.Qt.NoFocus)
        g_settings_layout.addWidget(self.g_settings_cpy2_clip)

        # Clipboard Size Limit------------------------------------------------------------------------------------------
        self.g_settings_limit_clipboard_size = QCheckBox('Limit Clipboard Size', self)
        self.g_settings_limit_clipboard_size.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_settings_limit_clipboard_size.setFont(QFont('Arial', 10))
        self.g_settings_limit_clipboard_size.setStyleSheet('border: none;')
        self.g_settings_limit_clipboard_size.setToolTip(
            'Set the size limit of clipboard')
        self.g_settings_limit_clipboard_size.stateChanged.connect(self.cb_limit_clipboard_size_state_changed)
        self.g_settings_limit_clipboard_size.setFocusPolicy(QtCore.Qt.NoFocus)
        g_settings_layout.addWidget(self.g_settings_limit_clipboard_size)

        self.g_settings_set_size_limit = QWidget(self)
        self.g_settings_set_size_limit.setFixedHeight(30)
        self.g_settings_set_size_limit.setFixedWidth(constants.WIDGET_WIDTH)
        self.g_settings_set_size_limit.setEnabled(self.config['copy_2_cb'])

        size_layout = QHBoxLayout()
        size_layout.setContentsMargins(0, 0, 0, 0)

        self.g_settings_size_val = QSpinBox()
        self.g_settings_size_val.setRange(8, 200)
        self.g_settings_size_val.setFixedWidth(75)
        self.g_settings_size_val.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_settings_size_val.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.g_settings_size_val.setSuffix(" MB")
        self.g_settings_size_val.setFocusPolicy(QtCore.Qt.NoFocus)
        self.g_settings_size_val.valueChanged.connect(self.set_file_size)
        self.g_settings_size_val.setValue(self.config['ss_mb_size_limit'])
        self.g_settings_size_val.setEnabled(self.config['ss_limit_size'])

        self.g_settings_limit_clipboard_size.setChecked(self.config['ss_limit_size'])

        size_layout.addWidget(self.g_settings_size_val)
        size_layout.addStretch()
        self.g_settings_set_size_limit.setLayout(size_layout)

        g_settings_layout.addWidget(self.g_settings_set_size_limit)

        # Check the copy_2_cb checkbox now
        self.g_settings_cpy2_clip.setChecked(self.config['copy_2_cb'])

        # Show toast on monitor change ---------------------------------------------------------------------------------
        self.g_settings_show_toast_on_monitor_change = QCheckBox('Toast on Monitor Change', self)
        self.g_settings_show_toast_on_monitor_change.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_settings_show_toast_on_monitor_change.setFont(QFont('Arial', 10))
        self.g_settings_show_toast_on_monitor_change.setStyleSheet('border: none;')
        self.g_settings_show_toast_on_monitor_change.setToolTip(
            'Show notification when the active monitor has been changed')
        self.g_settings_show_toast_on_monitor_change.stateChanged.connect(self.cb_show_toast_on_monitor_state_changed)
        self.g_settings_show_toast_on_monitor_change.setChecked(self.config['show_toast_on_monitor_change'])
        self.g_settings_show_toast_on_monitor_change.setFocusPolicy(QtCore.Qt.NoFocus)
        g_settings_layout.addWidget(self.g_settings_show_toast_on_monitor_change)

        # Show toast on capture ----------------------------------------------------------------------------------------
        self.g_settings_show_toast_on_capture = QCheckBox('Toast on Capture', self)
        self.g_settings_show_toast_on_capture.setFixedHeight(constants.FIELD_HEIGHT)
        self.g_settings_show_toast_on_capture.setFont(QFont('Arial', 10))
        self.g_settings_show_toast_on_capture.setStyleSheet('border: none;')
        self.g_settings_show_toast_on_capture.setToolTip('Show notification when screenshot has been captured')
        self.g_settings_show_toast_on_capture.stateChanged.connect(self.cb_show_toast_on_capture_state_changed)
        self.g_settings_show_toast_on_capture.setChecked(self.config['show_toast_on_capture'])
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
        self.image_preview.setFixedWidth(constants.WIDGET_WIDTH)
        self.image_preview.setFixedHeight(constants.WIDGET_HEIGHT_HD_RATIO)
        self.image_preview.setStyleSheet("""
                                        background-color:#eee;
                                        border: 1px solid #bbb;
                                        border-radius: 2px;
                                        background-color:#eee;
                                        background-image: url({});
                                        background-repeat: no-repeat;
                                        background-position: center center;
                                        border: 1px solid #bbb;
                                        """.format(constants.DEFAULT_PREVIEW_PATH))
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
        self.config['ss_path'] = file
        utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)

    def gen_monitor_list(self):
        with mss.mss() as scr:
            for i in range(0, len(scr.monitors)):
                button = QPushButton(self)
                button.setText(str(i))
                button.setFixedWidth(40)
                button.setFixedHeight(40)
                button.setStyleSheet("""
                                    QPushButton {
                                        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #fff, stop: 1 #eee); border: 1px solid #bbb;
                                    }
                                    QPushButton:pressed {
                                        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #eee, stop: 1 #fff);
                                    }
                                    QPushButton:hover {
                                        border: 1px solid #666;
                                    }
                                    """)
                button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
                button.setFocusPolicy(QtCore.Qt.NoFocus)
                button.clicked.connect(lambda: self.preview_screen())
                self.monitor_buttons.append(button)

    def preview_screen(self):
        mid = int(self.sender().text())
        with mss.mss() as scr:
            scr_img = scr.grab(scr.monitors[mid])

            img = Image.frombytes("RGB", scr_img.size, scr_img.bgra, "raw", "BGRX")
            img.thumbnail((constants.THUMBNAIL_WIDTH, constants.THUMBNAIL_HEIGHT))
            img.save(constants.TEMP_IMAGE_PATH)

            self.image_preview.setStyleSheet("""
                                            background-color:#eee; 
                                            background-image: url({});
                                            background-repeat: no-repeat;
                                            background-position: center center; 
                                            border: 1px solid #bbb;
                                            """.format(constants.TEMP_IMAGE_PATH))

    def cb_save_file_state_changed(self, int):
        self.g_settings_set_path.setEnabled(self.g_settings_save_file_cb.isChecked())
        self.g_settings_optimize_ss.setEnabled(self.g_settings_save_file_cb.isChecked())
        self.config['save_ss'] = self.g_settings_save_file_cb.isChecked()

        if self.config['ss_path'] == '':
            self.init_save_path()

        utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)

    def cb_limit_clipboard_size_state_changed(self, int):
        self.config['ss_limit_size'] = self.g_settings_limit_clipboard_size.isChecked()
        self.g_settings_size_val.setEnabled(self.g_settings_limit_clipboard_size.isChecked())

        utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)

    def cb_cpy2_clip_state_changed(self, int):
        self.config['copy_2_cb'] = self.g_settings_cpy2_clip.isChecked()
        self.g_settings_limit_clipboard_size.setEnabled(self.g_settings_cpy2_clip.isChecked())
        self.g_settings_size_val.setEnabled(self.g_settings_cpy2_clip.isChecked() and
                                            self.g_settings_limit_clipboard_size.isChecked())
        utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)

    def cb_show_toast_on_monitor_state_changed(self, int):
        self.config['show_toast_on_monitor_change'] = self.g_settings_show_toast_on_monitor_change.isChecked()
        utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)

    def cb_show_toast_on_capture_state_changed(self, int):
        self.config['show_toast_on_capture'] = self.g_settings_show_toast_on_capture.isChecked()
        utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)

    def cb_optimize_screenshot(self, int):
        self.config['ss_optimize'] = self.g_settings_optimize_ss.isChecked()
        utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)

    def init_save_path(self):
        cwd = os.getcwd()
        self.config['ss_path'] = cwd
        utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)

    def closeEvent(self, event):
        if os.path.exists(constants.TEMP_IMAGE_PATH):
            os.remove(constants.TEMP_IMAGE_PATH)

    def get_custom_hotkey(self):
        globals.flag_capturing_input = not globals.flag_capturing_input

        if globals.flag_capturing_input:
            self.g_setting_hotkey_change_button.setText('Enter to Accept, Esc to cancel')
            self.g_settings_hotkey_val.setText('Enter a hotkey...')

            self.g_setting_hotkey_change_button.setStyleSheet("""
                                                            QPushButton {
                                                                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #e74c3c, stop: 1 #c0392b); border: 1px solid #bbb;
                                                            }
                                                            QPushButton:pressed {
                                                                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #c0392b, stop: 1 #e74c3c);
                                                            }
                                                            QPushButton:hover {
                                                                border: 1px solid #666;
                                                            }
                                                            """)
            print("trying to kill process")
            try:
                self.hotkey_listener.kill()
            except Exception as e:
                print(e)

    def set_file_size(self):
        self.config['ss_mb_size_limit'] = self.g_settings_size_val.value()
        utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)

    def capture_hotkey(self, key, params):
        if not globals.flag_capturing_input:
            return

        input_flags = ['esc', 'enter']

        try:
            name = chr(key)
        except:
            name = qt_modifier_to_keyboard(key)

        if name not in self.key_list and name not in input_flags:
            self.key_list.append(name)
            self.g_settings_hotkey_val.setText('+'.join(self.key_list))

        resetting = False
        if name == 'esc':
            self.key_list = []
            resetting = True
        elif name == 'enter':
            if len(self.key_list) == 0:
                error_dialog = QErrorMessage()
                error_dialog.showMessage('Must enter a sequence of keys...')
                error_dialog.exec_()
            else:
                self.config['ss_hotkey'] = '+'.join(self.key_list)
                utils.update_config(self.FLOCK, constants.CONFIG_FILE, self.config)
                resetting = True
                params['proc_start'] = True

        if resetting:
            self.key_list = []
            globals.flag_capturing_input = False
            self.g_settings_hotkey_val.setText(self.config['ss_hotkey'])
            self.g_setting_hotkey_change_button.setStyleSheet("""
                                                            QPushButton {
                                                                border-radius: 2px;
                                                                background-color: qlineargradient(
                                                                    x1: 0, y1: 0, x2: 0, y2: 1,
                                                                    stop: 0 #fff, stop: 1 #eee); 
                                                                border: 1px solid #bbb;
                                                            }
                                                            QPushButton:pressed {
                                                                background-color: qlineargradient(
                                                                x1: 0, y1: 0, x2: 0, y2: 1,
                                                                stop: 0 #eee, stop: 1 #fff);
                                                            }
                                                            QPushButton:hover {
                                                                border: 1px solid #666;
                                                            }
                                                            """)
            self.g_setting_hotkey_change_button.setText('Set')
            self.g_instructions_hotkeys.setText('ctrl+alt+[monitor number] - Set active monitor\n{} - Take screenshot'.format(self.config['ss_hotkey']))

            if 'proc_start' in params and params['proc_start']:
                print("trying to start process")
                try:
                    self.hotkey_listener.start()
                except Exception as e:
                    print(e)
