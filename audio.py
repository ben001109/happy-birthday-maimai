# audio.py
import sys
import os
import threading
import time
import wave

def resource_path(relative_path: str) -> str:
    """
    取得資源檔案的絕對路徑，適用於開發環境與打包成 exe 後。
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 僅使用 PyAudio
try:
    import pyaudio
except ImportError:
    pyaudio = None

class AudioPlayer(threading.Thread):
    def __init__(self, file_list, delay: float = 0.1, playback_library: str = 'pyaudio'):
        """
        撥放一般音訊檔案。
        """
        super().__init__()
        self.file_list = file_list
        self.delay = delay
        self.playback_library = playback_library.lower()
        self._stop_event = threading.Event()

    def run(self):
        if self.playback_library == 'pyaudio':
            self.play_with_pyaudio()
        else:
            print("目前僅支援 pyaudio，請確認設定。")

    def play_with_pyaudio(self):
        if pyaudio is None:
            print("pyaudio 模組未安裝！")
            return
        for file_path in self.file_list:
            if self._stop_event.is_set():
                break
            try:
                abs_path = resource_path(file_path)
                wf = wave.open(abs_path, 'rb')
            except Exception as e:
                print(f"開啟 {file_path} 失敗：{e}")
                continue
            p = pyaudio.PyAudio()
            try:
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True)
            except Exception as e:
                print(f"建立 pyaudio stream 失敗 ({file_path})：{e}")
                wf.close()
                p.terminate()
                continue
            chunk = 1024
            data = wf.readframes(chunk)
            while data and not self._stop_event.is_set():
                stream.write(data)
                data = wf.readframes(chunk)
            stream.stop_stream()
            stream.close()
            wf.close()
            p.terminate()
            time.sleep(self.delay)

    def stop(self):
        self._stop_event.set()

def play_audio_files(file_list, delay: float = 0.1, playback_library: str = 'pyaudio'):
    """
    撥放一般音訊檔案。
    """
    player = AudioPlayer(file_list, delay, playback_library)
    player.start()
    return player

def check_audio_installation() -> str:
    if pyaudio is not None:
        print("檢查結果：pyaudio 已安裝。")
        return "pyaudio"
    else:
        print("檢查結果：pyaudio 未安裝！")
        return "None"

def test_audio_file_playback(playback_library: str = check_audio_installation()):
    test_files = ["resources/test1.wav", "resources/test2.wav"]
    print(f"使用 {playback_library} 撥放音效測試中...")
    player = play_audio_files(test_files, playback_library=playback_library)
    player.join()

#-------------------------------
# 以下為禮物錄音播放控制功能

class GiftAudioPlayer(AudioPlayer):
    def __init__(self, file, delay: float = 0.1, playback_library: str = 'pyaudio'):
        # 將 file 包裝成單一元素列表
        super().__init__([file], delay, playback_library)
        self.paused = False
        self.current_wf = None  # 當前播放的 wave 物件

    def play_with_pyaudio(self):
        if pyaudio is None:
            print("pyaudio 模組未安裝！")
            return
        file_path = self.file_list[0]
        try:
            abs_path = resource_path(file_path)
            wf = wave.open(abs_path, 'rb')
            self.current_wf = wf
        except Exception as e:
            print(f"開啟 {file_path} 失敗：{e}")
            return
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)
        except Exception as e:
            print(f"建立 pyaudio stream 失敗 ({file_path})：{e}")
            wf.close()
            p.terminate()
            return
        chunk = 1024
        data = wf.readframes(chunk)
        while data and not self._stop_event.is_set():
            if self.paused:
                time.sleep(0.1)
                continue
            stream.write(data)
            data = wf.readframes(chunk)
        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def fast_forward(self, seconds):
        if self.current_wf is not None:
            current_pos = self.current_wf.tell()
            framerate = self.current_wf.getframerate()
            new_pos = current_pos + int(seconds * framerate)
            if new_pos > self.current_wf.getnframes():
                new_pos = self.current_wf.getnframes()
            self.current_wf.setpos(new_pos)

    def rewind(self, seconds):
        if self.current_wf is not None:
            current_pos = self.current_wf.tell()
            framerate = self.current_wf.getframerate()
            new_pos = current_pos - int(seconds * framerate)
            if new_pos < 0:
                new_pos = 0
            self.current_wf.setpos(new_pos)

def play_gift_audio(file, delay: float = 0.1, playback_library: str = 'pyaudio'):
    gift_player = GiftAudioPlayer(file, delay, playback_library)
    gift_player.start()
    return gift_player

#-------------------------------
if __name__ == "__main__":
    pass
