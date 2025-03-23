# GUI.py
import sys
import os
import shutil  # 用於複製資料夾
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QMessageBox, QDialog, QHBoxLayout, QSizePolicy, QSlider, QGraphicsOpacityEffect
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


def load_plan_file(file_path="resources/plan.txt"):
    try:
        abs_path = audio.resource_path(file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        return lines
    except Exception as e:
        print("讀取企劃檔失敗：", e)
        return ["無法讀取企劃檔案。"]


# 基底對話框，供需要自動縮放字型的對話框使用
class AutoScalingDialog(QDialog):
    def __init__(self, parent=None, base_width=400):
        super().__init__(parent)
        self.base_width = base_width
        self.original_font_sizes = {}

    def cache_font_sizes(self):
        self.original_font_sizes.clear()
        for widget in self.findChildren((QLabel, QPushButton)):
            self.original_font_sizes[widget] = widget.font().pointSize()

    def showEvent(self, event):
        super().showEvent(event)
        self.cache_font_sizes()
        self.update_fonts()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_fonts()

    def update_fonts(self):
        scale = self.width() / self.base_width
        for widget, orig_size in self.original_font_sizes.items():
            font = widget.font()
            font.setPointSize(max(8, int(orig_size * scale)))
            widget.setFont(font)


class TestDialog(AutoScalingDialog):
    def __init__(self, parent=None):
        super().__init__(parent, base_width=400)
        self.setWindowTitle("預先音訊測試")
        self.setStyleSheet("QDialog { font-weight: bold; }")
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


# 新增：企劃介紹對話框
class PlanDialog(AutoScalingDialog):
    def __init__(self, plan_lines, parent=None):
        super().__init__(parent, base_width=400)
        self.setWindowTitle("企劃介紹")
        self.setStyleSheet("QDialog { font-weight: bold; }")
        self.plan_lines = plan_lines
        self.current_index = 0
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_text)
        self.timer.start(2000)

    def init_ui(self):
        # 使用堆疊布局來實現背景圖片與文字疊加
        self.stack_layout = QVBoxLayout(self)
        self.bg_label = QLabel(self)
        self.bg_label.setAlignment(Qt.AlignCenter)
        bg_pixmap = QPixmap(audio.resource_path("resources/plan_background.png"))
        self.bg_label.setPixmap(bg_pixmap)
        # 設定透明度50%
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.5)
        self.bg_label.setGraphicsEffect(opacity_effect)
        self.text_label = QLabel("", self)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("background-color: transparent; color: black;")
        self.stack_layout.addWidget(self.bg_label)
        self.stack_layout.addWidget(self.text_label)
        self.setLayout(self.stack_layout)

    def update_text(self):
        if self.current_index < len(self.plan_lines):
            current_line = self.plan_lines[self.current_index]
            existing = self.text_label.text()
            if existing:
                self.text_label.setText(existing + "\n" + current_line)
            else:
                self.text_label.setText(current_line)
            self.current_index += 1
        else:
            self.timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg_label.resize(self.size())


# 更新：禮物合併對話框，包含圖片與語音控制（加進度條與時間標籤）
class GiftCombinedDialog(QDialog):
    def __init__(self, gift_images, gift_audio, parent=None):
        super().__init__(parent)
        self.setWindowTitle("禮物")
        self.gift_images = gift_images
        self.current_index = 0
        self.gift_audio = gift_audio
        self.init_ui()
        self.gift_audio_player = audio.play_gift_audio(self.gift_audio, playback_library="pyaudio")
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(500)

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        # 左側：圖片區域與導航按鈕
        image_layout = QVBoxLayout()
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_label)
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一張", self)
        self.prev_button.clicked.connect(self.show_prev)
        nav_layout.addWidget(self.prev_button)
        self.next_button = QPushButton("下一張", self)
        self.next_button.clicked.connect(self.show_next)
        nav_layout.addWidget(self.next_button)
        image_layout.addLayout(nav_layout)
        main_layout.addLayout(image_layout, stretch=1)

        # 右側：語音控制區域與進度條、時間顯示
        control_layout = QVBoxLayout()
        self.status_label = QLabel("播放中", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.status_label)
        self.pause_resume_button = QPushButton("暫停", self)
        self.pause_resume_button.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.pause_resume_button)
        self.fast_forward_button = QPushButton("快進 1秒", self)
        self.fast_forward_button.clicked.connect(self.fast_forward)
        control_layout.addWidget(self.fast_forward_button)
        self.rewind_button = QPushButton("快退 1秒", self)
        self.rewind_button.clicked.connect(self.rewind)
        control_layout.addWidget(self.rewind_button)
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.sliderReleased.connect(self.slider_released)
        control_layout.addWidget(self.slider)
        self.time_label = QLabel("0:00 / 0:00", self)
        self.time_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.time_label)

        main_layout.addLayout(control_layout, stretch=0)
        self.update_image()

    def update_image(self):
        pixmap = QPixmap(audio.resource_path(self.gift_images[self.current_index]))
        if pixmap.isNull():
            self.image_label.setText("無法載入圖片")
        else:
            self.image_label.setPixmap(pixmap.scaled(450, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image()

    def show_prev(self):
        self.current_index = (self.current_index - 1) % len(self.gift_images)
        self.update_image()

    def show_next(self):
        self.current_index = (self.current_index + 1) % len(self.gift_images)
        self.update_image()

    def toggle_pause(self):
        if self.gift_audio_player.paused:
            self.gift_audio_player.resume()
            self.pause_resume_button.setText("暫停")
            self.status_label.setText("播放中")
        else:
            self.gift_audio_player.pause()
            self.pause_resume_button.setText("繼續")
            self.status_label.setText("暫停中")

    def fast_forward(self):
        self.gift_audio_player.fast_forward(1)

    def rewind(self):
        self.gift_audio_player.rewind(1)

    def update_progress(self):
        if self.gift_audio_player.current_wf is not None:
            total = self.gift_audio_player.total_frames
            current = self.gift_audio_player.current_position
            if total > 0:
                percent = int((current / total) * 100)
                self.slider.setValue(percent)
                duration = total / self.gift_audio_player.framerate
                current_time = current / self.gift_audio_player.framerate
                self.time_label.setText(
                    f"{int(current_time // 60)}:{int(current_time % 60):02d} / {int(duration // 60)}:{int(duration % 60):02d}")

    def slider_released(self):
        if self.gift_audio_player.current_wf is not None:
            total = self.gift_audio_player.total_frames
            new_percent = self.slider.value() / 100.0
            new_pos = int(total * new_percent)
            self.gift_audio_player.set_position(new_pos)

    def closeEvent(self, event):
        self.gift_audio_player.stop()
        super().closeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, narration_lines, thanks_lines, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VTuber 生日賀卡")
        self.setGeometry(100, 100, 600, 700)
        self.narration_lines = narration_lines
        self.thanks_lines = thanks_lines
        self.current_index = 0
        self.base_width = 600
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        self.layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel("VTuber 生日賀卡", self)
        self.title_label.setStyleSheet("font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("特別獻上我們最真摯的祝福", self)
        self.subtitle_label.setStyleSheet("color: gray;")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.subtitle_label)

        self.narrative_label = QLabel("", self)
        self.narrative_label.setWordWrap(True)
        self.narrative_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.narrative_label)

        self.gift_button = QPushButton("打開禮物", self)
        self.gift_button.clicked.connect(self.open_gift)
        self.gift_button.hide()
        self.gift_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.gift_button)

        self.plan_button = QPushButton("企劃介紹", self)
        self.plan_button.clicked.connect(self.open_plan)
        self.plan_button.hide()
        self.plan_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.plan_button)

        self.close_button = QPushButton("再見", self)
        self.close_button.clicked.connect(self.manual_close)
        self.close_button.hide()
        self.close_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.close_button)

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
            self.plan_button.show()
            self.close_button.show()
            self.thanks_label.setText("特別感謝：\n" + "\n".join(self.thanks_lines))

    def open_gift(self):
        if hasattr(self, "bg_player") and self.bg_player is not None:
            self.bg_player.stop()
        gift_audio = "resources/gift_audio.wav"
        gift_images = [
            "resources/reaper.png",
            "resources/solu.png",
            "resources/hasaki.png",
            "resources/fenmeow.png",
            "resources/macaroni",
            "resources/laso.png",
            "resources/zombie.png",
        ]
        combined_dialog = GiftCombinedDialog(gift_images, gift_audio, self)
        combined_dialog.exec_()

    def open_plan(self):
        plan_lines = load_plan_file("resources/plan.txt")
        plan_dialog = PlanDialog(plan_lines, self)
        plan_dialog.exec_()

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
        self.plan_button.setFont(button_font)


class TestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("預先音訊測試")
        self.setStyleSheet("QDialog { font-weight: bold; }")
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
