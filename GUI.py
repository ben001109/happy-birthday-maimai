# GUI.py
import sys
import os
import shutil  # 用於複製資料夾
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QMessageBox, QDialog, QHBoxLayout, QSizePolicy,QSlider
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

# 新增：禮物語音控制與圖片顯示合併對話框
class GiftCombinedDialog(QDialog):
    """
    禮物合併對話框：同時顯示禮物圖片與錄音控制面板（使用水平佈局），
    並新增進度條及時間顯示，可拖動調整播放位置。
    """
    def __init__(self, gift_images, gift_audio, parent=None):
        super().__init__(parent)
        self.setWindowTitle("禮物")
        self.gift_images = gift_images
        self.current_index = 0
        self.gift_audio = gift_audio
        self.init_ui()
        # 啟動禮物錄音播放器（獨立執行緒）
        self.gift_audio_player = audio.play_gift_audio(self.gift_audio, playback_library="pyaudio")
        # 建立 timer 用來更新進度條與時間標籤
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(500)  # 每500毫秒更新一次

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        # 左側：圖片區域
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
        
        # 右側：語音控制區域
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
        # 新增進度條
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.sliderReleased.connect(self.slider_released)
        control_layout.addWidget(self.slider)
        # 新增時間顯示標籤
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
                # 計算時間（秒）
                duration = total / self.gift_audio_player.framerate
                current_time = current / self.gift_audio_player.framerate
                self.time_label.setText(f"{int(current_time//60)}:{int(current_time%60):02d} / {int(duration//60)}:{int(duration%60):02d}")
    
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
            self.close_button.show()
            self.thanks_label.setText("特別感謝：\n" + "\n".join(self.thanks_lines))

    def open_gift(self):
        if hasattr(self, "bg_player") and self.bg_player is not None:
            self.bg_player.stop()
        # 直接使用 GiftCombinedDialog 同時顯示圖片與語音控制
        gift_audio = "resources/gift_audio.wav"
        gift_images = [
            "resources/comic_p1.png",
            "resources/comic_p2.png",
            "resources/comic_p3.png",
            "resources/comic_p4.png",
            "resources/the_reaper_of_soul.png",
            "resources/solu.png",
            "resources/hasaki.png",
            "resources/fenmeow.png",
            "resources/macaroni",
            "resources/laso.png",
        ]
        combined_dialog = GiftCombinedDialog(gift_images, gift_audio, self)
        combined_dialog.exec_()

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

class GiftCombinedDialog(QDialog):
    """
    禮物合併對話框：同時顯示禮物圖片與錄音控制面板，使用水平佈局。
    """
    def __init__(self, gift_images, gift_audio, parent=None):
        super().__init__(parent)
        self.setWindowTitle("禮物")
        self.gift_images = gift_images
        self.current_index = 0
        self.gift_audio = gift_audio
        self.init_ui()
        # 啟動禮物錄音播放器（在單獨的執行緒中運行）
        self.gift_audio_player = audio.play_gift_audio(self.gift_audio, playback_library="pyaudio")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        # 左側：圖片區域
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
        main_layout.addLayout(image_layout)
        # 右側：語音控制區域
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
        main_layout.addLayout(control_layout)
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
            self.close_button.show()
            self.thanks_label.setText("特別感謝：\n" + "\n".join(self.thanks_lines))

    def open_gift(self):
        if hasattr(self, "bg_player") and self.bg_player is not None:
            self.bg_player.stop()
        # 使用 GiftCombinedDialog 同時顯示圖片與語音控制
        gift_audio = "resources/gift_audio.wav"
        gift_images = [
            "resources/solu.png",
            "resources/hasaki.png",
            "resources/fenmeow.png",
            "resources/macaroni",
            "resources/laso.png",
        ]
        combined_dialog = GiftCombinedDialog(gift_images, gift_audio, self)
        combined_dialog.exec_()

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

class GiftCombinedDialog(QDialog):
    def __init__(self, gift_images, gift_audio, parent=None):
        super().__init__(parent)
        self.setWindowTitle("禮物")
        self.gift_images = gift_images
        self.current_index = 0
        self.gift_audio = gift_audio
        self.init_ui()
        # 啟動禮物錄音播放器（在獨立執行緒中）
        self.gift_audio_player = audio.play_gift_audio(self.gift_audio, playback_library="pyaudio")
    
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        # 左側：圖片區域
        image_layout = QVBoxLayout()
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_label)
        # 將上一張與下一張按鈕放入一個水平佈局
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一張", self)
        self.prev_button.clicked.connect(self.show_prev)
        nav_layout.addWidget(self.prev_button)
        self.next_button = QPushButton("下一張", self)
        self.next_button.clicked.connect(self.show_next)
        nav_layout.addWidget(self.next_button)
        image_layout.addLayout(nav_layout)
        main_layout.addLayout(image_layout, stretch=1)
        
        # 右側：語音控制區域
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
        main_layout.addLayout(control_layout, stretch=0)
        
        self.update_image()
    
    def update_image(self):
        pixmap = QPixmap(audio.resource_path(self.gift_images[self.current_index]))
        if pixmap.isNull():
            self.image_label.setText("無法載入圖片")
        else:
            # 根據 image_label 的實際大小縮放圖片
            new_width = self.image_label.width() or 450
            new_height = self.image_label.height() or 450
            scaled_pixmap = pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
    
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
    
    def closeEvent(self, event):
        self.gift_audio_player.stop()
        super().closeEvent(event)

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
