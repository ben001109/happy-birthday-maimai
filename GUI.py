# GUI.py
import sys
import os
import shutil  # 用於複製資料夾
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QMessageBox, QDialog, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QFont
import audio  # 匯入音訊模組

def load_message_file(file_path="resources/message.txt"):
    try:
        abs_path = audio.resource_path(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        return lines
    except Exception as e:
        print("讀取訊息檔失敗：", e)
        return ["無法讀取訊息檔案。"]

def load_thanks_file(file_path="resources/thanks.txt"):
    try:
        abs_path = audio.resource_path(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        return lines
    except Exception as e:
        print("讀取感謝檔失敗：", e)
        return ["感謝您的支持！"]

class GiftDialog(QDialog):
    def __init__(self, gift_images, parent=None):
        super().__init__(parent)
        self.setWindowTitle("禮物")
        self.gift_images = gift_images
        self.current_index = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一張", self)
        self.prev_button.clicked.connect(self.show_prev)
        nav_layout.addWidget(self.prev_button)
        self.next_button = QPushButton("下一張", self)
        self.next_button.clicked.connect(self.show_next)
        nav_layout.addWidget(self.next_button)
        layout.addLayout(nav_layout)

        self.update_image()

    def update_image(self):
        pixmap = QPixmap(audio.resource_path(self.gift_images[self.current_index]))
        if pixmap.isNull():
            self.image_label.setText("無法載入圖片")
        else:
            self.image_label.setPixmap(pixmap.scaled(450, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def show_prev(self):
        self.current_index = (self.current_index - 1) % len(self.gift_images)
        self.update_image()

    def show_next(self):
        self.current_index = (self.current_index + 1) % len(self.gift_images)
        self.update_image()

class MainWindow(QMainWindow):
    def __init__(self, narration_lines, thanks_lines, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VTuber 生日賀卡")
        self.setGeometry(100, 100, 600, 700)
        self.narration_lines = narration_lines
        self.thanks_lines = thanks_lines
        self.current_index = 0
        self.base_width = 600  # 基準寬度
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setAlignment(Qt.AlignCenter)

        # 主標題
        self.title_label = QLabel("VTuber 生日賀卡", self)
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        # 小標題
        self.subtitle_label = QLabel("特別獻上我們最真摯的祝福", self)
        self.subtitle_label.setStyleSheet("color: gray;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.subtitle_label)

        # 敘述文字區域
        self.narrative_label = QLabel("", self)
        self.narrative_label.setWordWrap(True)
        self.narrative_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.narrative_label)

        # 打開禮物按鈕（初始隱藏）
        self.gift_button = QPushButton("打開禮物", self)
        self.gift_button.clicked.connect(self.open_gift)
        self.gift_button.hide()
        self.gift_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.gift_button)

        # 手動關閉按鈕（初始隱藏）
        self.close_button = QPushButton("再見", self)
        self.close_button.clicked.connect(self.manual_close)
        self.close_button.hide()
        self.close_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.close_button)

        # 特別感謝區域
        self.thanks_label = QLabel("", self)
        self.thanks_label.setWordWrap(True)
        self.thanks_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.thanks_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_narrative)
        self.timer.start(2000)

        self.update_fonts()

    def update_narrative(self):
        if self.current_index < len(self.narration_lines):
            current_line = self.narration_lines[self.current_index]
            existing_text = self.narrative_label.text()
            if existing_text:
                self.narrative_label.setText(existing_text + "\n" + current_line)
            else:
                self.narrative_label.setText(current_line)
            self.current_index += 1
        else:
            self.timer.stop()
            self.gift_button.show()
            self.close_button.show()
            self.thanks_label.setText("特別感謝：\n" + "\n".join(self.thanks_lines))

    def open_gift(self):
        if hasattr(self, "bg_player") and self.bg_player is not None:
            self.bg_player.stop()
        gift_audio = "resources/gift_audio.wav"
        audio.play_audio_files([gift_audio], playback_library="pyaudio")
        gift_images = [
            "resources/gift_image1.png",
            "resources/gift_image2.png",
            "resources/gift_image3.png",
            "resources/gift_image4.png",
            "resources/gift_image5.png",
            "resources/gift_image6.png",
            "resources/gift_image7.png",
            "resources/gift_image8.png",
            "resources/gift_image9.png",
            "resources/gift_image0.png"
        ]
        gift_dialog = GiftDialog(gift_images, self)
        gift_dialog.exec_()

    def manual_close(self):
        self.timer.stop()
        if hasattr(self, "bg_player") and self.bg_player is not None:
            self.bg_player.stop()

        src_folder = audio.resource_path("resources")
        dest_folder = os.path.join(os.path.dirname(src_folder), "生日快樂")
        try:
            import shutil
            shutil.copytree(src_folder, dest_folder, dirs_exist_ok=True)
        except Exception as e:
            QMessageBox.critical(
                self,
                "複製錯誤",
                f"無法複製資源資料夾：{e}",
                QMessageBox.Ok
            )
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("提醒")
        msg_box.setText("如果想要直接聽語音或是看圖片的話，請直接打開「生日快樂」資料夾去看")
        msg_box.setStandardButtons(QMessageBox.Ok)
        ok_button = msg_box.button(QMessageBox.Ok)
        ok_button.setText("好，我知道了")
        msg_box.exec_()

        sys.exit(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_fonts()

    def update_fonts(self):
        scale = self.width() / self.base_width
        title_font = QFont()
        title_font.setPointSize(max(10, int(24 * scale)))
        self.title_label.setFont(title_font)
        subtitle_font = QFont()
        subtitle_font.setPointSize(max(8, int(18 * scale)))
        self.subtitle_label.setFont(subtitle_font)
        narrative_font = QFont()
        narrative_font.setPointSize(max(8, int(16 * scale)))
        self.narrative_label.setFont(narrative_font)
        thanks_font = QFont()
        thanks_font.setPointSize(max(8, int(14 * scale)))
        self.thanks_label.setFont(thanks_font)
        button_font = QFont()
        button_font.setPointSize(max(8, int(18 * scale)))
        self.gift_button.setFont(button_font)
        self.close_button.setFont(button_font)

class TestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("預先音訊測試")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.info_label = QLabel("請確認測試音訊是否正常播放。", self)
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        self.test_button = QPushButton("確認", self)
        self.test_button.clicked.connect(self.confirm)
        layout.addWidget(self.test_button)
        self.setLayout(layout)

    def confirm(self):
        response = QMessageBox.question(
            self,
            "音訊檢查",
            "測試音訊已播放，是否繼續？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if response == QMessageBox.Yes:
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "檢查未通過",
                "音訊測試未通過，請聯絡開發人員。\nEmail: a0903932792@gmail.com\nDC: the_reaper_of_soul",
                QMessageBox.Ok
            )
            self.reject()

def start_gui():
    app = QApplication(sys.argv)

    try:
        audio.test_audio_file_playback()
    except Exception as e:
        QMessageBox.critical(
            None,
            "音訊測試錯誤",
            f"音訊測試失敗，請聯絡開發人員。\nEmail: a0903932792@gmail.com\nDC: the_reaper_of_soul\n錯誤：{e}"
        )
        sys.exit(1)

    test_dialog = TestDialog()
    if test_dialog.exec_() != QDialog.Accepted:
        sys.exit(0)

    background_files = ["resources/background.wav"]
    bg_player = audio.play_audio_files(background_files, playback_library="pyaudio")

    narration_lines = load_message_file("resources/message.txt")
    thanks_lines = load_thanks_file("resources/thanks.txt")

    main_window = MainWindow(narration_lines, thanks_lines)
    main_window.bg_player = bg_player
    main_window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    start_gui()
