from faster_whisper import WhisperModel
import numpy as np
import traceback


class FasterWhisperTranscriber:

    def __init__(
        self,
        model_size="base",
        device="cpu",
        compute_type="int8"
    ):
        self.init(model_size, device, compute_type)


    def init(self, model_size, device, compute_type):
        try:
            print("Loading faster whisper model...")
            # whisperModel = WhisperModel(
            #     'base',
            #     device='cpu',
            #     compute_type='int8'
            # )
            whisperModel = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
            print("Whisper ready")
            self.buffer = b""
            self.model = whisperModel
            print("Whisper booted")
        except Exception as e:
            print(e)
            traceback.print_exc()
            raise
    
    def process(self, chunk):
        # accumulate audio
        self.buffer += chunk
        # wait until enough audio exists
        # 16000 samples/sec * 2 bytes * 2 seconds
        if len(self.buffer) < 64000:
            return {
                "partial": ""
            }

        audio = np.frombuffer(
            self.buffer,
            dtype=np.int16
        )

        self.buffer = b""
        # normalize int16 -> float32
        audio = audio.astype(
            np.float32
        ) / 32768.0

        segments, info = self.model.transcribe(
            audio,
            language="en",
            beam_size=5
        )
        text = " ".join(
            segment.text
            for segment in segments
        )

        return {
            "partial": text.strip()
        }