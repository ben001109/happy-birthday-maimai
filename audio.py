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
        # PyInstaller 打包後，資源會放在 sys._MEIPASS 目錄中
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
        :param file_list: 要播放的音訊檔案路徑列表（檔案格式須為 WAV）
        :param delay: 每個檔案播放間隔的延遲秒數
        :param playback_library: 撥放使用的套件，目前僅支援 'pyaudio'
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
    啟動一個 AudioPlayer 執行緒來撥放音訊檔案。
    :param file_list: 音訊檔案路徑列表（WAV 格式）
    :param delay: 每個檔案之間的延遲秒數
    :param playback_library: 使用的播放庫，目前僅支援 'pyaudio'
    :return: 回傳 AudioPlayer 執行緒物件
    """
    player = AudioPlayer(file_list, delay, playback_library)
    player.start()
    return player

def check_audio_installation() -> str:
    """
    檢查是否有安裝 pyaudio。
    :return: 若 pyaudio 可用則回傳 "pyaudio"，否則回傳 "None"。
    """
    if pyaudio is not None:
        print("檢查結果：pyaudio 已安裝。")
        return "pyaudio"
    else:
        print("檢查結果：pyaudio 未安裝！")
        return "None"

def test_audio_file_playback(playback_library: str = check_audio_installation()):
    """
    測試音檔撥放功能，使用預設的測試音檔（例如 test1.wav 與 test2.wav）。
    :param playback_library: 指定使用的撥放庫，預設為 check_audio_installation() 的結果。
    """
    test_files = ["resources/test1.wav", "resources/test2.wav"]
    print(f"使用 {playback_library} 撥放音效測試中...")
    player = play_audio_files(test_files, playback_library=playback_library)
    player.join()

# __main__ 區塊保持空白
if __name__ == "__main__":
    pass
