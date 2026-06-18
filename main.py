import os
import platform
os_platform = platform.system()

if os_platform.lower() == "windows":
    os.environ["QT_QPA_PLATFORM"] = "windows"
elif os_platform.lower() == "darwin":
    os.environ["QT_QPA_PLATFORM"] = "cocoa"
else:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

import sys
import signal
import argparse
import threading
from PyQt5 import QtWidgets
from audio import AudioSource
from transcriber import Transcriber
from overlay import Overlay
from worker import Worker
from srt import SRTWriter
from startup_window import StartupWindow

stop_event = threading.Event()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default="system",
        help="mic, system OR file path"
    )
    parser.add_argument(
        "--srt",
        help="output srt file"
    )

    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    startup = StartupWindow()
    startup.show()

    objects = {}

    def start_transcription():
        startup.start_btn.setEnabled(False)
        selected_model = startup.selected_model()
        overlay = Overlay()
        audio = AudioSource(
            args.source,
            stop_event
        )
        transcriber = Transcriber()
        writer = (
            SRTWriter(args.srt)
            if args.srt
            else None
        )
        worker = Worker(
            audio=audio,
            transcriber=transcriber,
            stop_event=stop_event,
            model_size=selected_model,
            writer=writer
        )
        worker.signal.connect(
            overlay.set_text
        )
        worker.status_signal.connect(
            startup.set_status
        )

        def show_overlay_when_ready(msg):
            if msg == "Model loaded":
                startup.hide()
                overlay.show()
        worker.status_signal.connect(
            show_overlay_when_ready
        )
        worker.start()
        objects["overlay"] = overlay
        objects["worker"] = worker

    startup.start_btn.clicked.connect(
        start_transcription
    )

    def handle_exit():
        # print("\nReceived exit signal...")
        stop_event.set()
        worker = objects.get("worker")
        if worker:
            worker.stop()
            worker.quit()
            worker.wait(2000)
        app.quit()

    app.aboutToQuit.connect(
        handle_exit
    )

    signal.signal(
        signal.SIGINT,
        lambda *args: handle_exit()
    )

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()