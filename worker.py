from PyQt5 import QtCore

class Worker(QtCore.QThread):
    signal = QtCore.pyqtSignal(str)

    def __init__(self, audio, transcriber, stop_event, writer=None):
        super().__init__()
        self.audio = audio
        self.transcriber = transcriber
        self.writer = writer

        self.stop_event = stop_event
        self.seg_start = 0
        self.full_text = ""

    def run(self):
        try:
            for chunk in self.audio.stream():

                if self.isInterruptionRequested() or self.stop_event.is_set():
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
        finally:
            self.audio.shutdown()
    
    def stop(self):
         # stop worker gracefully (NOT terminate)
        self.requestInterruption()
        try:
            self.audio.shutdown()
        except Exception:
            pass
   