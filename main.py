import os
import platform
os_platform = platform.system()
if os_platform.lower() == "windows":
    os.environ["QT_QPA_PLATFORM"] = "windows"
else:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

import sys
import argparse
from PyQt5 import QtWidgets, QtCore

from audio import AudioSource
from transcriber import Transcriber
from transcriber_whisper import FasterWhisperTranscriber
from overlay import Overlay
from srt import SRTWriter
from utils import extract_text
import threading

# MODEL_PATH = "/home/back/Documents/src/python/localSRT-RT/bin/shared/vosk-model-en-us-0.22-lgraph"
MODEL_PATH = "./bin/shared/vosk-model-small-en-us-0.15"

stop_event = threading.Event()

class Worker(QtCore.QThread):
    signal = QtCore.pyqtSignal(str)

    def __init__(self, audio, transcriber, writer=None):
        super().__init__()
        self.audio = audio
        self.transcriber = transcriber
        self.writer = writer

        self.seg_start = 0

    def run(self):
        try:
            for chunk in self.audio.stream():

                if self.isInterruptionRequested() or stop_event.is_set():
                    break

                print("audio active")

                partial = self.transcriber.process(chunk)

                txt = partial.get("partial", "")

                if txt:
                    self.signal.emit(txt)
        except Exception as e:
            import traceback
            print("WORKER CRASHED:")
            print(e)
            traceback.print_exc()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="system", help="mic, system OR file path")
    parser.add_argument("--srt", help="output srt file")

    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    overlay = Overlay()
    overlay.show()

    audio = AudioSource(args.source)
    transcriber = Transcriber(MODEL_PATH)
    # transcriber = FasterWhisperTranscriber()

    writer = SRTWriter(args.srt) if args.srt else None

    worker = Worker(audio, transcriber, writer)
    worker.signal.connect(overlay.set_text)
    worker.start()

    def handle_exit():
        print("\nStopping...")
        stop_event.set()
         # stop worker gracefully (NOT terminate)
        worker.requestInterruption()
        worker.quit()
        worker.wait(2000)

        app.quit()

    # catch Qt close
    app.aboutToQuit.connect(handle_exit)

    # catch Ctrl+C
    import signal
    signal.signal(signal.SIGINT, lambda *args: handle_exit())

    sys.exit(app.exec_())


print(__name__)
if __name__ == "__main__":
    main()