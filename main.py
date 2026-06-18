import os
import platform
os_platform = platform.system()
if os_platform.lower() == "windows":
    os.environ["QT_QPA_PLATFORM"] = "windows"
elif os_platform == "darwin":
    os.environ["QT_QPA_PLATFORM"] = "cocoa"
else:
    os.environ["QT_QPA_PLATFORM"] = "xcb" # Linux

import sys
import argparse
from audio import AudioSource
from transcriber import Transcriber
from PyQt5 import QtWidgets
from overlay import Overlay
from srt import SRTWriter
import threading
from worker import Worker
from vosk_model_manager import VoskModelManager
from pathlib import Path

# MODEL_PATH = "./bin/shared/vosk-model-en-us-0.22-lgraph"
# MODEL_PATH = "./bin/shared/vosk-model-small-en-us-0.15"
MODEL_PATH = "C:\\Users\\black\\AppData\\Local\\RealTimeSRT\\models\\vosk-model-small-en-us-0.15"

stop_event = threading.Event()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="system", help="mic, system OR file path")
    parser.add_argument("--srt", help="output srt file")

    args = parser.parse_args()
    
    app = QtWidgets.QApplication(sys.argv)
    overlay = Overlay()
    overlay.show()
    
    
    audio = AudioSource(args.source, stop_event)
    transcriber = Transcriber()


    writer = SRTWriter(args.srt) if args.srt else None

    worker = Worker(audio, transcriber, stop_event, overlay, writer)
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


if __name__ == "__main__":
    main()