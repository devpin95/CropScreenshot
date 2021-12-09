from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QPushButton, QHBoxLayout, QFileDialog, QGraphicsDropShadowEffect
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragLeaveEvent, QMouseEvent, QPixmap, QCursor, QColor
from PyQt5 import QtCore, Qt
from PIL import Image
from io import BytesIO
import win32clipboard as cb
import time

import constants
import globals
from QtKeyValueToKeyboardValue import letters as letter, modifiers as mods
import utilities as utils


class ImageCropTab(QWidget):
    main_layout = None
    main_widget = None

    focused = False

    req_width = constants.APP_WIDTH
    req_height = constants.WIDGET_HEIGHT_HD_RATIO + constants.APP_BOTTOM_PADDING
    height_correction = 0

    current_image_path = ''
    dragging = False
    dragging_start_pos = (-1, -1)
    dragging_end_pos = (-1, -1)
    maxx = 0
    maxy = 0

    ready_to_crop = False
    ready_to_copy = False
    ready_to_save = False

    quadrant = "I"

    COPY_TIMEOUT = 0.25
    last_copy_2_clipboard = 0

    def __init__(self, parent, config):
        super(QWidget, self).__init__(parent)

        self.config = config
        globals.keyEvent.subscribe_to_press_event(self.crop_image,
                                                  keyfilter=[mods['enter']])
        globals.keyEvent.subscribe_to_combo_event(self.shortcut_copy_1_clipboard,
                                                  [
                                                      mods['ctrl'],
                                                      mods['shift'],
                                                      letter['c']
                                                  ])

        globals.keyEvent.subscribe_to_combo_event(self.shortcut_save_image,
                                                  [
                                                      mods['ctrl'],
                                                      mods['shift'],
                                                      letter['s']
                                                  ])

        self.main_layout = QVBoxLayout()
        self.main_widget = QWidget(self)


        self.drop_area = QLabel()
        self.drop_area.setFixedWidth(constants.WIDGET_WIDTH)
        self.drop_area.setFixedHeight(constants.WIDGET_HEIGHT_HD_RATIO)
        self.drop_area.setStyleSheet("""
                                    QLabel {
                                        border: 3px dashed #bbb;
                                        margin: 0;
                                    }
                                    """)
        self.drop_area.setAcceptDrops(True)
        self.drop_area.dragEnterEvent = self.dragEnterEvent
        self.drop_area.dragLeaveEvent = self.dragLeaveEvent
        self.drop_area.dropEvent = self.dropEvent

        self.dropshadow = QGraphicsDropShadowEffect()
        self.dropshadow.setYOffset(3)
        self.dropshadow.setXOffset(0)
        self.dropshadow.setColor(QColor(0, 0, 0))
        self.dropshadow.setBlurRadius(10)

        self.drop_area.setGraphicsEffect(None)

        self.drop_area.setMouseTracking(True)
        self.drop_area.mousePressEvent = self.mousePressEvent
        self.drop_area.mouseReleaseEvent = self.mouseReleaseEvent
        self.drop_area.mouseMoveEvent = self.mouseMoveEvent
        self.drop_area.setCursor(QCursor(QtCore.Qt.ArrowCursor))

        self.crop_mask = QWidget(self.drop_area)
        self.crop_mask.resize(50, 50)
        self.crop_mask.setStyleSheet("""
                                     QWidget {
                                        background-image: none;
                                        background-color: #fff;
                                        border: 1px solid #111;
                                     }
                                     """)
        self.crop_mask.move(0, 0)

        op = QGraphicsOpacityEffect(self)
        op.setOpacity(0.5)  # 0 to 1 will cause the fade effect to kick in
        self.crop_mask.setGraphicsEffect(op)
        self.crop_mask.setAutoFillBackground(True)

        self.crop_mask.hide()
        self.main_layout.addWidget(self.drop_area)

        # ACTIONS GROUP
        self.actions_group = QWidget()
        self.actions_group.setFixedWidth(constants.WIDGET_WIDTH)
        self.actions_group.setFixedHeight(constants.FIELD_HEIGHT)

        self.actions_group.layout = QHBoxLayout()
        self.actions_group.setFixedWidth(constants.WIDGET_WIDTH)
        self.actions_group.setFixedHeight(constants.FIELD_HEIGHT + 15)
        self.actions_group.layout.setAlignment(Qt.Qt.AlignRight)

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

        self.actions_group.setLayout(self.actions_group.layout)

        self.main_layout.addWidget(self.actions_group)
        self.main_widget.setLayout(self.main_layout)

    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        if self.dragging:
            ox, oy = self.dragging_start_pos  # origin point
            nx, ny = a0.x(), a0.y()  # current mouse pos

            if nx > self.maxx:
                nx = self.maxx
            elif nx < 0:
                nx = 0

            if ny > self.maxy:
                ny = self.maxy
            elif ny < 0:
                ny = 0

            disx = nx - ox  # vector from the origin point in the x direction
            disy = ny - oy  # vector from the origin point in the y direction
            absx = abs(disx)  # distance in the x direction
            absy = abs(disy)  # distance in the y direction

            if disx >= 0 and disy >= 0:
                # down and to the right
                self.crop_mask.resize(disx, disy)

                if self.quadrant != 'I':
                    self.quadrant = 'I'
                    print("Moved to quadrant I")

            elif disx >= 0 and disy < 0:
                # up and to the right
                self.crop_mask.move(ox, ny)
                self.crop_mask.resize(disx, absy)

                if self.quadrant != 'II':
                    self.quadrant = 'II'
                    print("Moved to quadrant II")

            elif disx < 0 and disy < 0:
                # up and to the left
                self.crop_mask.move(nx, ny)
                self.crop_mask.resize(absx, absy)

                if self.quadrant != 'III':
                    self.quadrant = 'III'
                    print("Moved to quadrant III")

            elif disx < 0 and disy >= 0:
                # down and to the right
                self.crop_mask.move(nx, oy)
                self.crop_mask.resize(absx, disy)

                if self.quadrant != 'IV':
                    self.quadrant = 'IV'
                    print("Moved to quadrant IV")

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        print("Click!")
        self.dragging = True
        self.crop_mask.show()
        self.crop_mask.move(a0.x(), a0.y())
        self.crop_mask.resize(0, 0)
        self.dragging_start_pos = (a0.x(), a0.y())

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        print("Release!!")
        x, y = self.dragging_start_pos

        if a0.x() == x and a0.y() == y:
            # hide the box
            self.crop_mask.resize(1, 1)
            self.crop_mask.hide()
            self.dragging_start_pos = (-1, -1)
            self.ready_to_crop = False
        else:
            # set the dropped pos
            self.dragging_end_pos = (a0.x(), a0.y())
            self.ready_to_crop = True

        print(a0.x(), x, a0.y(), y)

        self.dragging = False

    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        m = a0.mimeData()
        if m.hasUrls():
            a0.accept()
        else:
            a0.ignore()

    def dragLeaveEvent(self, a0: QDragLeaveEvent) -> None:
        a0.accept()

    def dropEvent(self, a0: QDropEvent) -> None:
        m = a0.mimeData()
        if m.hasImage:
            a0.accept()

            file_path = m.urls()[0].toLocalFile()
            self.current_image_path = file_path

            self._set_area_image(file_path)
            self.drop_area.setCursor(QCursor(QtCore.Qt.CrossCursor))

            self.actions_group.save_button.hide()
            self.actions_group.copy_button.hide()
            self.ready_to_copy = False

            self.drop_area.setGraphicsEffect(self.dropshadow)

        else:
            a0.ignore()

    def crop_image(self, key, params=None):
        if not self.ready_to_crop:
            return

        self.ready_to_crop = False

        startx, starty = self.dragging_start_pos
        endx, endy = self.dragging_end_pos

        # switch the start and end position components if we didn't drag down and to the right
        if endx < startx:
            startx, endx = endx, startx
        if endy < starty:
            starty, endy = endy, starty

        print("Crop at ({}, {}) ({}, {})".format(startx, starty, endx, endy))

        img = Image.open(self.current_image_path)
        target_img_width, target_img_height = img.size
        preview_img_width, preview_img_height = self.drop_area.width(), self.drop_area.height()

        prop_startx, prop_starty = (startx / preview_img_width, starty / preview_img_height)
        prop_endx, prop_endy = (endx / preview_img_width, endy / preview_img_height)
        prop_startx = self._clamp01(prop_startx)
        prop_starty = self._clamp01(prop_starty)
        prop_endx = self._clamp01(prop_endx)
        prop_endy = self._clamp01(prop_endy)

        target_startx, target_starty = (prop_startx * target_img_width, prop_starty * target_img_height)
        target_endx, target_endy = (prop_endx * target_img_width, prop_endy * target_img_height)

        target_startx = int(target_startx)
        target_starty = int(target_starty)
        target_endx = int(target_endx)
        target_endy = int(target_endy)

        print("Mapping from {} -> {}".format((target_img_width, target_img_height), (preview_img_width, preview_img_height)))
        print("Prop {} {}".format((prop_startx, prop_starty),
                                             (prop_endx, prop_endy)))
        print("Mapped {}, {}".format((target_startx, target_starty),
                                     (target_endx, target_endy)))

        box = (target_startx, target_starty, target_endx, target_endy)

        try:
            img = img.crop(box)
            img.save('temp/temp_cropped_image.jpg', format="JPEG")

            self._set_area_image('temp/temp_cropped_image.jpg', show_options=True)
            self.current_image_path = 'temp/temp_cropped_image.jpg'

            self.actions_group.save_button.show()
            self.actions_group.copy_button.show()
            self.ready_to_copy = True
        except:
            print('could not crop image')

    def _set_area_image(self, file_path, show_options=False):
        pixmap = QPixmap(file_path)

        w = pixmap.width()
        h = pixmap.height()

        print(w, h)

        target_width = constants.WIDGET_WIDTH * 3

        scale = True

        if w < target_width:
            target_width = w
            scale = False

            if w < constants.WIDGET_WIDTH:
                scale = True
                target_width = constants.WIDGET_WIDTH

        target_height = (target_width * h) / w

        if scale:
            pixmap = pixmap.scaled(target_width, target_height, QtCore.Qt.KeepAspectRatio)

        pixmap.save("temp/temp_crop_image_preview.png", quality=100)

        self.maxx = target_width
        self.maxy = target_height
        self.req_width = target_width + 40
        self.req_height = target_height + constants.APP_BOTTOM_PADDING

        if show_options:
            self.req_height += constants.FIELD_HEIGHT + 15

        self.resize_window(self.req_height, self.req_width)
        self.actions_group.setFixedWidth(target_width)
        self.drop_area.setFixedWidth(target_width)
        self.drop_area.setFixedHeight(target_height)
        self.drop_area.setStyleSheet("""
                                     QLabel {
                                         background-image: url(%s);
                                         background-repeat:no-repeat;
                                         background-position: center;
                                         border: 1px solid #111;
                                         border-radius: 2px;
                                     }
                                     """ % 'temp/temp_crop_image_preview.png')

        self.crop_mask.setStyleSheet("""
                                     QWidget {
                                        background-image: none;
                                        background-color: #fff;
                                        border: 1px solid #111;
                                     }
                                     """)
        self.crop_mask.move(0, 0)
        self.crop_mask.resize(0, 0)
        self.crop_mask.show()

    def _clamp01(self, val):
        if val < 0:
            val = 0
        if val > 1:
            val = 1
        return val

    def shortcut_copy_1_clipboard(self):
        if not self.focused:
            return

        print("COPY!")

        current_time = time.time()

        if current_time - self.last_copy_2_clipboard > self.COPY_TIMEOUT:
            self.copy_2_clipboard()

    def copy_2_clipboard(self):
        if not self.ready_to_copy:
            return

        print("Copying to clipboard")

        output = BytesIO()
        img = Image.open(self.current_image_path)
        img.save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        print(len(data) / constants.BYTES_PER_MEGABYTE)

        utils.send_to_clipboard(cb.CF_DIB, data)

    def shortcut_save_image(self):
        if not self.focused:
            return

        print("SAVE!")

        self.save_image()

    def save_image(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Image", r"{}".format(self.config['ss_path']), "Images (*{})".format('.jpg'), options=options
        )

        if filename:
            # _, ext = os.path.splitext(fileName)
            img = Image.open('temp/temp_cropped_image.jpg')
            img.save(filename)

        globals.keyEvent.force_key_clear()

