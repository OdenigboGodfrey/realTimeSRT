from pathlib import Path
from PyQt5 import QtCore

from audio import AudioSource
from transcriber import Transcriber
from vosk_model_manager import VoskModelManager


class Worker(QtCore.QThread):

    signal = QtCore.pyqtSignal(str)
    status_signal = QtCore.pyqtSignal(str)

    def __init__(
        self,
        audio: AudioSource,
        transcriber: Transcriber,
        stop_event,
        model_size="small",
        writer=None
    ):
        super().__init__()

        self.audio = audio
        self.transcriber = transcriber
        self.writer = writer

        self.stop_event = stop_event
        self.model_size = model_size

        self.seg_start = 0
        self.full_text = ""

    def init_vosk(self):

        self.status_signal.emit(
            f"Loading {self.model_size} Vosk model..."
        )

        vosk_model_manager = VoskModelManager(
            self.model_size,
            self.status_signal
        )

        model_path = vosk_model_manager.ensure_model()

        self.transcriber.load_model(
            str(Path(model_path))
        )

        self.status_signal.emit("Model loaded")

    def run(self):

        self.init_vosk()

        try:
            for chunk in self.audio.stream():

                if (
                    self.isInterruptionRequested()
                    or self.stop_event.is_set()
                ):
                    break

                partial = self.transcriber.process(chunk)

                txt = partial.get("partial", "")

                if txt:
                    self.signal.emit(txt)

        except Exception as e:

            import traceback

            print("WORKER CRASHED:")
            print(e)
            traceback.print_exc()

        finally:
            self.audio.shutdown()

    def stop(self):

        self.requestInterruption()

        try:
            self.audio.shutdown()
        except Exception:
            pass