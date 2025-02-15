# GUI.py
import sys
import os
import shutil  # 用來複製資料夾
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QMessageBox, QDialog, QHBoxLayout
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap
import audio  # 匯入音訊模組

def load_message_file(file_path="resources/message.txt"):
    """
    從指定文字檔中讀取敘述文字，每行視為一段。
    """
    try:
        abs_path = audio.resource_path(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        return lines
    except Exception as e:
        print("讀取訊息檔失敗：", e)
        return ["無法讀取訊息檔案。"]

def load_thanks_file(file_path="resources/thanks.txt"):
    """
    從指定文字檔中讀取特別感謝內容，每行視為一筆資料。
    """
    try:
        abs_path = audio.resource_path(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        return lines
    except Exception as e:
        print("讀取感謝檔失敗：", e)
        return ["感謝您的支持！"]

class GiftDialog(QDialog):
    """
    禮物對話框：顯示多張禮物圖片，可使用上一張/下一張按鈕切換。
    """
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
            self.image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def show_prev(self):
        self.current_index = (self.current_index - 1) % len(self.gift_images)
        self.update_image()

    def show_next(self):
        self.current_index = (self.current_index + 1) % len(self.gift_images)
        self.update_image()

class MainWindow(QMainWindow):
    """
    主介面：整合主標題、小標題、逐行敘述、打開禮物按鈕、特別感謝表與手動關閉按鈕，
    並將所有文字置中對齊。
    """
    def __init__(self, narration_lines, thanks_lines, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VTuber 生日賀卡")
        self.setGeometry(100, 100, 600, 700)
        self.narration_lines = narration_lines
        self.thanks_lines = thanks_lines
        self.current_index = 0
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setAlignment(Qt.AlignCenter)  # 整個 layout 置中

        # 主標題
        self.title_label = QLabel("VTuber 生日賀卡", self)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        # 小標題
        self.subtitle_label = QLabel("特別獻上我們最真摯的祝福", self)
        self.subtitle_label.setStyleSheet("font-size: 18px; color: gray;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.subtitle_label)

        # 敘述文字區域
        self.narrative_label = QLabel("", self)
        self.narrative_label.setWordWrap(True)
        self.narrative_label.setStyleSheet("font-size: 16px;")
        self.narrative_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.narrative_label)

        # 打開禮物按鈕（初始隱藏）
        self.gift_button = QPushButton("打開禮物", self)
        self.gift_button.setStyleSheet("font-size: 18px; padding: 10px;")
        self.gift_button.clicked.connect(self.open_gift)
        self.gift_button.hide()
        self.gift_button.setFixedWidth(200)
        self.layout.addWidget(self.gift_button)

        # 手動關閉按鈕（初始隱藏）
        self.close_button = QPushButton("再見", self)
        self.close_button.setStyleSheet("font-size: 18px; padding: 10px;")
        self.close_button.clicked.connect(self.manual_close)
        self.close_button.hide()
        self.close_button.setFixedWidth(200)
        self.layout.addWidget(self.close_button)

        # 特別感謝區域
        self.thanks_label = QLabel("", self)
        self.thanks_label.setWordWrap(True)
        self.thanks_label.setStyleSheet("font-size: 14px; color: blue;")
        self.thanks_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.thanks_label)

        # QTimer 用來逐行更新敘述文字
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_narrative)
        self.timer.start(2000)  # 每 2000 毫秒更新一次

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
            # 敘述全部顯示完畢後，顯示打開禮物按鈕與手動關閉按鈕，
            # 並更新特別感謝表
            self.gift_button.show()
            self.close_button.show()
            self.thanks_label.setText("特別感謝：\n" + "\n".join(self.thanks_lines))

    def open_gift(self):
        """
        按下「打開禮物」後，播放禮物錄音並顯示禮物圖片對話框（含上下切換）。
        """
        gift_audio = "resources/gift_audio.wav"
        audio.play_audio_files([gift_audio], playback_library="pyaudio")
        gift_images = [
            "resources/gift_image1.png",
            "resources/gift_image2.png",
            "resources/gift_image3.png"
        ]
        gift_dialog = GiftDialog(gift_images, self)
        gift_dialog.exec_()

    def manual_close(self):
        """
        按下「再見」按鈕後，將 resources 資料夾全部複製到一個新資料夾「生日快樂」，
        然後彈出提醒視窗，告知使用者可直接開啟該資料夾觀看語音及圖片，
        按下確認後程式自動結束。
        """
        # 取得資源資料夾的路徑（假設在執行檔同目錄下）
        src_folder = audio.resource_path("resources")
        # 將複製目的地設為與 src_folder 同層的新資料夾 "生日快樂"
        dest_folder = os.path.join(os.path.dirname(src_folder), "生日快樂")
        try:
            # 使用 shutil.copytree 複製（Python 3.8+ 可用 dirs_exist_ok=True）
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

        # 彈出提醒視窗
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("提醒")
        msg_box.setText("如果想要直接聽語音或是看圖片的話可以直接打開生日快樂資料夾去看")
        msg_box.setStandardButtons(QMessageBox.Ok)
        ok_button = msg_box.button(QMessageBox.Ok)
        ok_button.setText("好，我知道了")
        msg_box.exec_()

        # 結束程式
        sys.exit(0)

class TestDialog(QDialog):
    """
    預先測試對話框：讓使用者確認測試音訊是否正常播放。
    """
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

    # 先進行音訊測試：使用預設測試音檔 (test1.wav 與 test2.wav)
    try:
        audio.test_audio_file_playback()
    except Exception as e:
        QMessageBox.critical(
            None,
            "音訊測試錯誤",
            f"音訊測試失敗，請聯絡開發人員。\nEmail: a0903932792@gmail.com\nDC: the_reaper_of_soul\n錯誤：{e}"
        )
        sys.exit(1)

    # 顯示預先測試對話框，讓使用者確認音訊測試結果
    test_dialog = TestDialog()
    if test_dialog.exec_() != QDialog.Accepted:
        sys.exit(0)

    # 啟動背景音效（播放背景音樂）
    background_files = ["resources/background.wav"]
    bg_player = audio.play_audio_files(background_files, playback_library="pyaudio")

    # 從外部文字檔讀取敘述訊息與特別感謝表
    narration_lines = load_message_file("resources/message.txt")
    thanks_lines = load_thanks_file("resources/thanks.txt")

    # 建立主介面（整合逐行敘述、打開禮物、特別感謝與手動關閉）
    main_window = MainWindow(narration_lines, thanks_lines)
    main_window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    start_gui()
