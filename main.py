import os
import platform
os_platform = platform.system()
if os_platform.lower() == "windows":
    os.environ["QT_QPA_PLATFORM"] = "windows"
else:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

import sys
import argparse

from audio import AudioSource
from transcriber import Transcriber
from transcriber_whisper import FasterWhisperTranscriber
from PyQt5 import QtWidgets, QtCore
from utils import extract_text
from overlay import Overlay
from srt import SRTWriter
import threading
from worker import Worker

# MODEL_PATH = "./bin/shared/vosk-model-en-us-0.22-lgraph"
MODEL_PATH = "./bin/shared/vosk-model-small-en-us-0.15"

stop_event = threading.Event()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="system", help="mic, system OR file path")
    parser.add_argument("--srt", help="output srt file")

    args = parser.parse_args()

    audio = AudioSource(args.source, stop_event)
    transcriber = Transcriber(MODEL_PATH)
    # transcriber = FasterWhisperTranscriber()

    app = QtWidgets.QApplication(sys.argv)

    overlay = Overlay()
    overlay.show()

    writer = SRTWriter(args.srt) if args.srt else None

    worker = Worker(audio, transcriber, stop_event, writer)
    worker.signal.connect(overlay.set_text)
    worker.start()

    def handle_exit():
        print("\n Received exit signal...")
        stop_event.set()
        worker.stop()
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