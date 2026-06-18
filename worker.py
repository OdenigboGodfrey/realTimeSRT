from pathlib import Path
from PyQt5 import QtCore

from audio import AudioSource
from overlay import Overlay
from transcriber import Transcriber
from vosk_model_manager import VoskModelManager

class Worker(QtCore.QThread):
    signal = QtCore.pyqtSignal(str)

    def __init__(self, audio: AudioSource, transcriber: Transcriber, stop_event, overlay: Overlay, writer=None):
        super().__init__()
        self.audio = audio
        self.transcriber = transcriber
        self.writer = writer

        self.stop_event = stop_event
        self.seg_start = 0
        self.full_text = ""
        self.overlay = overlay

        

    def init_vosk(self):
        # todo: ensure model is auto downloaded
        vosk_model_manager = VoskModelManager("small", self.signal)
        model_path = vosk_model_manager.ensure_model()
        vosk_model_path = Path(model_path)
        self.transcriber.load_model(str(vosk_model_path))
    
    def run(self):
        self.init_vosk()
        try:
            for chunk in self.audio.stream():

                if self.isInterruptionRequested() or self.stop_event.is_set():
                    break

                # print("audio active")

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
         # stop worker gracefully (NOT terminate)
        self.requestInterruption()
        try:
            self.audio.shutdown()
        except Exception:
            pass
   