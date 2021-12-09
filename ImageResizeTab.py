from PIL import Image
from PyQt5.QtWidgets import QLabel, QPushButton, QFileDialog, QWidget, QGroupBox, QVBoxLayout, QFormLayout, QCheckBox, QHBoxLayout, QGridLayout, QSpinBox, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PyQt5.QtGui import QFont, QCursor, QDragEnterEvent, QDropEvent, QDragLeaveEvent, QPixmap, QColor
from PyQt5 import QtCore, Qt
import os
from io import BytesIO
import win32clipboard as cb
import time

import constants
import utilities as utils
from QtKeyValueToKeyboardValue import letters as letter, modifiers as mods
import globals


class ImageResizeTab(QWidget):
    main_widget = None

    focused = False

    mod_req_height = constants.FIELD_HEIGHT * 4 + constants.APP_BOTTOM_PADDING
    req_height = constants.FIELD_HEIGHT * 4 + constants.WIDGET_HEIGHT_HD_RATIO + constants.APP_BOTTOM_PADDING
    req_width = constants.APP_WIDTH
    height_correction = 0

    target_image_path = ""
    temp_path = 'temp/temp_resize_image'
    temp_path_ext = '.jpg'

    resize_window = None
    resized_image = None

    green = '#2ecc71'
    red = '#e74c3c'
    blue = '#2980b9'

    COPY_TIMEOUT = 0.25
    last_copy_2_clipboard = 0

    preview_ready = False

    def __init__(self, parent, config):
        super(QWidget, self).__init__(parent)

        self.config = config

        globals.keyEvent.subscribe_to_combo_event(self.shortcut_save_image,
                                                  [
                                                      mods['ctrl'],
                                                      mods['shift'],
                                                      letter['s']
                                                  ])

        globals.keyEvent.subscribe_to_combo_event(self.shortcut_copy_2_clipboard,
                                                  [
                                                      mods['ctrl'],
                                                      mods['shift'],
                                                      letter['c']
                                                  ])

        self.main_layout = QVBoxLayout()
        self.main_widget = QWidget(self)

        self.main_widget.setStyleSheet("""
                                       background-color:#34495e;
                                       color: #efefef;
                                       """)

        # FORM ---------------------------------------------------------
        self.image_size_group = QGroupBox()
        self.image_size_group.setFixedWidth(220)
        self.image_size_group.setContentsMargins(0, 0, 0, 0)
        self.image_size_group.setStyleSheet("""
                                            QGroupBox{
                                                border: none;
                                                margin-bottom: 15px;
                                            }
                                            """)

        self.image_size_form_layout = QFormLayout()
        self.image_size_form_layout.setContentsMargins(0, 0, 0, 0)

        self.setting_label = QLabel("Image Resize Options")
        font = QFont('Arial', 10)
        font.setBold(True)
        self.setting_label.setFont(font)
        self.setting_label.setFixedWidth(150)
        self.setting_label.setFixedHeight(constants.FIELD_HEIGHT)

        self.image_size_form_layout.addRow(self.setting_label)

        # IMAGE SIZE ---------------------------------------------------------------------------------------------------
        self.image_size_label = QLabel("Image Size")
        font.setBold(False)
        self.image_size_label.setFont(font)
        self.image_size_label.setFixedWidth(75)
        self.image_size_label.setFixedHeight(constants.FIELD_HEIGHT)
        # self.image_size_form_layout.addWidget(self.image_size_label)

        self.image_size_spin_box = QSpinBox()
        self.image_size_spin_box.setRange(1, 50)
        self.image_size_spin_box.setFixedWidth(75)
        self.image_size_spin_box.setFixedHeight(constants.FIELD_HEIGHT)
        self.image_size_spin_box.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.image_size_spin_box.setSuffix(" MB")
        # self.g_settings_size_val.valueChanged.connect(self.set_file_size)
        self.image_size_spin_box.setValue(8)

        self.image_size_form_layout.addRow(self.image_size_label, self.image_size_spin_box)

        # Conserve Extention -------------------------------------------------------------------------------------------
        self.conserve_extention_label = QLabel("Keep file extension")
        font = QFont('Arial', 10)
        self.conserve_extention_label.setFont(font)
        self.conserve_extention_label.setFixedWidth(125)
        self.conserve_extention_label.setFixedHeight(constants.FIELD_HEIGHT)
        self.conserve_extention_label.setToolTip("If unchecked, image will be converted to JPEG format.")

        self.conserve_extention_check_box = QCheckBox('', self)
        font = QFont('Arial', 10)
        # self.copy_2_clipboard_check_box.setFont(font)
        self.conserve_extention_check_box.setStyleSheet('border: none;')
        self.conserve_extention_check_box.setFixedHeight(constants.FIELD_HEIGHT)
        self.conserve_extention_check_box.setToolTip("If unchecked, image will be converted to JPEG format.")

        self.conserve_extention_label.mousePressEvent = lambda a0: self.conserve_extention_check_box.setChecked(not self.conserve_extention_check_box.isChecked())

        self.image_size_form_layout.addRow(self.conserve_extention_label, self.conserve_extention_check_box)

        self.image_size_group.setLayout(self.image_size_form_layout)
        self.main_layout.addWidget(self.image_size_group)

        # STATS --------------------------------------------------------------------------------------------------------
        self.stats_group = QWidget()
        self.stats_group.layout = QVBoxLayout()
        self.stats_group.layout.setContentsMargins(10, 0, 0, 0)
        self.stats_group.setFixedWidth(constants.WIDGET_WIDTH)
        self.stats_group.setFixedHeight(50)
        # self.stats_group.setStyleSheet("""
        #                                         QWidget {
        #                                             border: 1px solid #ccc;
        #                                             border-radius: 2px;
        #                                             background-color: #eee;
        #                                         }
        #                                         QLabel {
        #                                             border: none;
        #                                             background-color: none;
        #                                         }
        #                                         """)

        # self.stats_group.top_spacer = QLabel("")
        # self.stats_group.top_spacer.setFixedHeight(10)
        # self.stats_group.top_spacer.setStyleSheet("border: 1px solid #ccc; border-bottom: none; border-left: none;")
        # self.stats_group.layout.addWidget(self.stats_group.top_spacer)

        # Path Label
        self.stats_group.path_label = QLabel("Path: " + self.target_image_path)
        self.stats_group.path_label.setFixedWidth(constants.WIDGET_WIDTH)
        self.stats_group.path_label.setFixedHeight(15)
        self.stats_group.layout.addWidget(self.stats_group.path_label)
        # File Size
        self.stats_group.file_size_label = QLabel("File Size: 0 MB")
        self.stats_group.file_size_label.setFixedWidth(constants.WIDGET_WIDTH)
        self.stats_group.file_size_label.setFixedHeight(15)
        self.stats_group.layout.addWidget(self.stats_group.file_size_label)

        # self.stats_group.bottom_spacer = QLabel("")
        # self.stats_group.bottom_spacer.setFixedHeight(10)
        # self.stats_group.bottom_spacer.setStyleSheet("border: 1px solid #ccc; border-top: none; border-left: none;")
        # self.stats_group.layout.addWidget(self.stats_group.bottom_spacer)

        self.stats_group.setLayout(self.stats_group.layout)

        self.stats_group.hide()
        self.main_layout.addWidget(self.stats_group)

        # DRAG AND DROP AREA -------------------------------------------------------------------------------------------
        self.drag_n_drop_area = QWidget()
        self.drag_n_drop_area.setFixedWidth(constants.WIDGET_WIDTH)
        self.drag_n_drop_area.setFixedHeight(constants.WIDGET_HEIGHT_HD_RATIO)
        self.drag_n_drop_area.setStyleSheet("""
                                            QWidget {
                                                border: 3px dashed #bbb;
                                                margin: 0;
                                            }
                                            """)
        self.drag_n_drop_area.layout = QVBoxLayout()

        self.drag_n_drop_area.setAcceptDrops(True)
        self.drag_n_drop_area.dragEnterEvent = self.dragEnterEvent
        self.drag_n_drop_area.dragLeaveEvent = self.dragLeaveEvent
        self.drag_n_drop_area.dropEvent = self.dropEvent
        self.main_layout.setAlignment(self.drag_n_drop_area, Qt.Qt.AlignCenter)

        self.main_layout.addWidget(self.drag_n_drop_area)
        self.main_layout.setAlignment(self.drag_n_drop_area, Qt.Qt.AlignHCenter)

        font = QFont('Arial', 15)
        self.drag_n_drop_label = QLabel()
        self.drag_n_drop_label.setFont(font)
        self.drag_n_drop_label.setText("DRAG AND DROP IMAGE")
        self.drag_n_drop_label.setStyleSheet("""
                                             border:none;
                                             text-align:center;
                                             color: #bbb;
                                             background-image: none;
                                             """)
        self.drag_n_drop_label.setAlignment(Qt.Qt.AlignCenter)
        self.drag_n_drop_area.layout.addWidget(self.drag_n_drop_label)

        # set up the opacity effect
        # self.drag_n_drop_area.opacityEffect = QGraphicsOpacityEffect()
        # self.drag_n_drop_area.setOpacity = lambda opacity: (
        #     self.drag_n_drop_area.opacityEffect.setOpacity(opacity),
        #     self.drag_n_drop_area.setGraphicsEffect(self.drag_n_drop_area.opacityEffect)
        # )
        self.drag_n_drop_area.setAutoFillBackground(True)

        self.dropshadow = QGraphicsDropShadowEffect()
        self.dropshadow.setYOffset(3)
        self.dropshadow.setXOffset(0)
        self.dropshadow.setColor(QColor(0, 0, 0))
        self.dropshadow.setBlurRadius(10)

        self.image_preview = QWidget()
        self.image_preview.dropshadow = QGraphicsDropShadowEffect()
        self.image_preview.dropshadow.setYOffset(3)
        self.image_preview.dropshadow.setXOffset(0)
        self.image_preview.dropshadow.setColor(QColor(0, 0, 0))
        self.image_preview.dropshadow.setBlurRadius(10)
        self.image_preview.setGraphicsEffect(self.image_preview.dropshadow)
        self.image_preview.hide()
        self.drag_n_drop_area.layout.addWidget(self.image_preview)

        self.drag_n_drop_area.setLayout(self.drag_n_drop_area.layout)

        # ACTIONS ------------------------------------------------------------------------------------------------------
        self.actions_group = QWidget()
        self.actions_group.setFixedWidth(constants.WIDGET_WIDTH)
        self.actions_group.setFixedHeight(constants.FIELD_HEIGHT)

        # self.actions_group.setStyleSheet("""background-color: #F00""")

        self.actions_group.layout = QHBoxLayout()
        self.actions_group.setFixedWidth(constants.WIDGET_WIDTH)
        self.actions_group.setFixedHeight(constants.FIELD_HEIGHT + 15)

        # image resize status
        self.actions_group.size_reduction_label = QLabel("")
        self.actions_group.size_reduction_label.setFixedWidth(constants.WIDGET_WIDTH)
        font = QFont('Arial', 10)
        font.setBold(True)
        self.actions_group.size_reduction_label.setFont(font)
        font.setBold(False)
        self.actions_group.size_reduction_label.setText("15% reduction")
        self.actions_group.size_reduction_label.setStyleSheet('color: {};'.format(self.green))
        self.actions_group.size_reduction_label.hide()
        self.actions_group.layout.addWidget(self.actions_group.size_reduction_label)

        # save button
        self.actions_group.save_button = QPushButton("")
        self.actions_group.save_button.setFixedHeight(constants.FIELD_HEIGHT)
        self.actions_group.save_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.actions_group.save_button.setFixedWidth(constants.FIELD_HEIGHT)
        self.actions_group.save_button.setStyleSheet("""
                                                            QPushButton {
                                                                border-radius: 2px;
                                                                background-image: url(assets/save.png);
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
                                                            }
                                                             """)
        self.actions_group.save_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.actions_group.save_button.clicked.connect(self.save_image)
        self.actions_group.save_button.setToolTip("Save")
        self.actions_group.save_button.hide()
        self.actions_group.layout.addWidget(self.actions_group.save_button)

        # copy button
        self.actions_group.layout.setAlignment(Qt.Qt.AlignLeft)
        self.actions_group.copy_button = QPushButton("")
        self.actions_group.copy_button.setFixedHeight(constants.FIELD_HEIGHT)
        self.actions_group.copy_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.actions_group.copy_button.setFixedWidth(constants.FIELD_HEIGHT)
        self.actions_group.copy_button.setStyleSheet("""
                                                    QPushButton {
                                                        border-radius: 2px;
                                                        background-image: url(assets/copy.png);
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
                                                    }
                                                     """)
        self.actions_group.copy_button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.actions_group.copy_button.clicked.connect(self.copy_2_clipboard)
        self.actions_group.copy_button.setToolTip("Copy to clipboard")
        self.actions_group.copy_button.hide()
        self.actions_group.layout.addWidget(self.actions_group.copy_button)

        # resize button
        self.actions_group.layout.setAlignment(Qt.Qt.AlignRight)
        self.actions_group.resize_button = QPushButton("Resize")
        self.actions_group.resize_button.setFixedHeight(constants.FIELD_HEIGHT)
        self.actions_group.resize_button.setFixedWidth(75)
        self.actions_group.resize_button.setStyleSheet("""
                                                        QPushButton {
                                                            border-radius: 2px;
                                                            background-color: qlineargradient(
                                                                x1: 0, y1: 0, x2: 0, y2: 1,
                                                                stop: 0 #fff, stop: 1 #eee); 
                                                            border: 1px solid #bbb;
                                                            color: #111;
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
        self.actions_group.resize_button.clicked.connect(self.resize_image)
        self.actions_group.layout.addWidget(self.actions_group.resize_button)

        self.actions_group.layout.setContentsMargins(0, 0, 0, 0)
        self.actions_group.setLayout(self.actions_group.layout)

        self.actions_group.hide()
        self.main_layout.addWidget(self.actions_group)

        self.main_widget.setLayout(self.main_layout)

    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        m = a0.mimeData()
        if m.hasUrls():
            a0.accept()

            if self.preview_ready:
                self.image_preview.setStyleSheet("""
                                background-image: url({}); 
                                background-repeat: no-repeat; 
                                background-position: center center;
                                border: none;
                                border-radius: 5px;
                            """.format("temp/temp_resize_image_alpha_preview.png"))

        else:
            a0.ignore()

    def dragLeaveEvent(self, a0: QDragLeaveEvent) -> None:
        a0.accept()
        if self.preview_ready:
            self.image_preview.setStyleSheet("""
                            background-image: url({}); 
                            background-repeat: no-repeat; 
                            background-position: center center;
                            border: none;
                            border-radius: 5px;
                        """.format("temp/temp_resize_image_preview.png"))

    def dropEvent(self, a0: QDropEvent) -> None:
        m = a0.mimeData()
        if m.hasImage:
            self.drag_n_drop_area.setGraphicsEffect(None)
            self.image_preview.setGraphicsEffect(self.image_preview.dropshadow)

            a0.setDropAction(Qt.Qt.CopyAction)
            file_path = m.urls()[0].toLocalFile()
            print("File Path", file_path)
            self.target_image_path = file_path

            _, file_ext = os.path.splitext(file_path)

            pixmap = QPixmap(file_path)
            pixmap = pixmap.scaled(constants.WIDGET_WIDTH, constants.WIDGET_HEIGHT_HD_RATIO, QtCore.Qt.KeepAspectRatio)
            pixmap.save("temp/temp_resize_image_preview.png", quality=100)

            trans_img = Image.open('temp/temp_resize_image_preview.png')
            alpha = Image.new("L", trans_img.size, 127)
            trans_img.putalpha(alpha)
            trans_img.save('temp/temp_resize_image_alpha_preview.png')
            trans_img.close()
            self.preview_ready = True

            image_margin = 0
            if pixmap.width() < constants.WIDGET_WIDTH:
                dif = constants.WIDGET_WIDTH - pixmap.width()
                image_margin = dif / 2

            self.drag_n_drop_area.setFixedWidth(pixmap.width())
            self.drag_n_drop_area.setFixedHeight(pixmap.height())

            self.req_height = self.mod_req_height + self.drag_n_drop_area.height()
            self.resize_window(self.req_height)

            self.drag_n_drop_area.setStyleSheet("""
                    border: none:
                    background-color: transparent;
                    """)
            self.drag_n_drop_label.setText("")
            self.drag_n_drop_label.hide()
            self.image_preview.show()
            self.image_preview.setStyleSheet("""
                background-image: url({}); 
                background-repeat: no-repeat; 
                background-position: center center;
                border: none;
                border-radius: 5px;
            """.format("temp/temp_resize_image_preview.png"))

            self.stats_group.path_label.setText("Path: " + self.target_image_path)
            self.stats_group.file_size_label.setText("File Size: " + str(round(os.stat(self.target_image_path).st_size / constants.BYTES_PER_MEGABYTE, 2)) + "MB")

            self.actions_group.show()
            self.stats_group.show()

            self.req_height += 50 + constants.FIELD_HEIGHT * 2
            self.resize_window(self.req_height)

            self.actions_group.size_reduction_label.hide()
            self.actions_group.copy_button.hide()
            self.actions_group.save_button.hide()

            a0.accept()
        else:
            a0.ignore()

    def resize_image(self):
        print("resizing image at " + self.target_image_path)

        _, self.temp_path_ext = os.path.splitext(self.target_image_path)
        target_temp_path = self.temp_path
        self.resized_image = Image.open(self.target_image_path)

        # if the user doesnt want to conserve the file ext, just convert the temp image to a jpeg to
        # optimize the file, that way we might not need to resize the image
        if not self.conserve_extention_check_box.isChecked():
            self.resized_image.save(self.temp_path + '.jpg', optimize=True, format="JPEG")
            self.temp_path_ext = '.jpg'
            target_temp_path += self.temp_path_ext
            self.resized_image = Image.open(target_temp_path)
        else:
            target_temp_path += self.temp_path_ext
            self.resized_image.save(target_temp_path, optimize=True, format=constants.IMAGE_FORMATS[self.temp_path_ext])

        self.resized_image = Image.open(target_temp_path)
        size = os.stat(target_temp_path).st_size / constants.BYTES_PER_MEGABYTE
        starting_size = size

        print("Saving temp file at", target_temp_path)
        print("Starting size", starting_size)

        while size > self.image_size_spin_box.value():
            img_width, img_height = self.resized_image.size

            print("resizing", img_width, img_height, img_width - int(img_width * 0.25),
                  img_height - int(img_height * 0.25))

            self.resized_image = self.resized_image.resize((img_width - int(img_width * 0.25), img_height - int(img_height * 0.25)), Image.ANTIALIAS)
            print(self.resized_image.size)
            self.resized_image.save(target_temp_path, optimize=True, format=constants.IMAGE_FORMATS[self.temp_path_ext])
            size = os.stat(target_temp_path).st_size / constants.BYTES_PER_MEGABYTE

            print('file size after resize', size)

        reduction = starting_size - size
        reduction = reduction / starting_size
        self.actions_group.size_reduction_label.setText(str(round(size, 2)) + "MB")

        self.actions_group.size_reduction_label.show()
        self.actions_group.copy_button.show()
        self.actions_group.save_button.show()

        # close the image so that we can delete it when the app is exited
        self.resized_image.close()

    def shortcut_copy_2_clipboard(self):
        if not self.focused:
            return

        current_time = time.time()

        if current_time - self.last_copy_2_clipboard > self.COPY_TIMEOUT:
            self.copy_2_clipboard()

    def copy_2_clipboard(self):
        print("Copying to clipboard")

        output = BytesIO()
        img = Image.open(self.temp_path + self.temp_path_ext)
        img.save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        print(len(data) / constants.BYTES_PER_MEGABYTE)

        utils.send_to_clipboard(cb.CF_DIB, data)

    def shortcut_save_image(self):
        if not self.focused:
            return

        self.save_image()

    def save_image(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Image", r"{}".format(self.config['ss_path']), "Images (*{})".format(self.temp_path_ext), options=options
        )

        if filename:
            # _, ext = os.path.splitext(fileName)
            self.resized_image.save(filename)

        globals.keyEvent.force_key_clear()
