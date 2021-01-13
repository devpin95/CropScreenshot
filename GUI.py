from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QFileDialog, QWidget, QVBoxLayout, QCheckBox, QHBoxLayout
from PyQt5.QtGui import QFont
import sys
import mss
from PIL import Image


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # self.setStyleSheet("padding: 5px 10px 5px 10px")
        self.setMinimumWidth(550)
        self.setMinimumHeight(250)

        self.monitor_buttons = []

        main_layout = QVBoxLayout()
        main_layout.addStretch()
        self.main_widget = QWidget(self)
        self.main_widget.setFixedWidth(500)
        self.main_widget.setFixedHeight(250)

        self.g_settings = QWidget(self)
        self.g_settings.setFixedWidth(500)
        self.g_settings.setFixedHeight(100)
        # self.g_settings.setStyleSheet('background-color: #f00')

        g_settings_layout = QVBoxLayout()
        g_settings_layout.addStretch()

        self.g_settings_savecb = QCheckBox('Save Screenshot', self)
        self.g_settings_savecb.setFixedHeight(30)
        self.g_settings_savecb.setFont(QFont('Arial', 10))
        # self.g_settings_label.setStyleSheet('background-color:#f00; padding: 0; margin: 0;')
        # self.g_settings_label.setStyleSheet('margin-bottom: 10px')

        # set up a box to hold the options for saving a screenshot
        g_settings_options_layout = QVBoxLayout()
        g_settings_options_layout.addStretch()
        self.g_settings_options = QWidget(self)
        self.g_settings_options.setFixedHeight(50)
        self.g_settings_options.setStyleSheet('background-color: #000;')
        self.g_settings_options.setStyleSheet('border: 1px solid #000; border-radius: 2px')
        self.g_settings_options.mouseReleaseEvent = lambda event: self.get_ss_save_path()

        # Path label and path string
        self.g_settings_options_savess_label = QLabel("Path:", self)
        self.g_settings_options_savess_label.setStyleSheet('border: none;')
        self.gg_settings_options_savess_path = QLabel("C:/Documents", self)
        self.gg_settings_options_savess_path.setStyleSheet('border: none; padding-left: 10px;')

        # add the path label and string
        g_settings_options_layout.addWidget(self.g_settings_options_savess_label)
        g_settings_options_layout.addWidget(self.gg_settings_options_savess_path)

        self.g_settings_options.setLayout(g_settings_options_layout)

        g_settings_layout.addWidget(self.g_settings_savecb)
        g_settings_layout.addWidget(self.g_settings_options)

        self.g_settings.setLayout(g_settings_layout)

        # 500x281
        preview_layout = QVBoxLayout()
        preview_layout.addStretch(0)
        self.g_preview = QWidget(self)
        self.g_preview.setFixedHeight(100)
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
        self.gg_settings_options_savess_path.setText(file)

    def gen_monitor_list(self):
        with mss.mss() as scr:
            for i in range(0, len(scr.monitors)):
                button = QPushButton(self)
                button.setText(str(i))
                button.setFixedWidth(40)
                button.setFixedHeight(40)
                button.setStyleSheet('QPushButton{background-color: #aaa; border:1px solid #000;} QPushButton:pressed{background-color: #f00;}')
                self.monitor_buttons.append(button)


app = QApplication([])
app.setStyle('Fusion')

window = Window()

sys.exit(app.exec_())
