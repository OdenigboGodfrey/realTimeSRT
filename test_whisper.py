import ctranslate2
import faulthandler
faulthandler.enable()

import os
os.environ["CT2_VERBOSE"] = "1"

from faster_whisper import WhisperModel

print("before")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="float32"
)

print("after")