import json
import time
from vosk import Model, KaldiRecognizer


class Transcriber:
    def __init__(self, model_path, sample_rate=16000):
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        self.start_time = time.time()

    def process(self, chunk):
        # ALWAYS feed audio, never skip
        self.recognizer.AcceptWaveform(chunk)

        partial = json.loads(self.recognizer.PartialResult())
        return partial

    def final(self):
        return json.loads(self.recognizer.Result())

    def now(self):
        return time.time() - self.start_time