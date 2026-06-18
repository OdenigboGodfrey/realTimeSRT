import queue
import subprocess
import sounddevice as sd
import numpy as np
import platform
import threading
import time
import re

from ffmpeg_binary_manager import get_ffmpeg_binary


# stop_event = threading.Event()

FFMPEG = get_ffmpeg_binary("ffmpeg")


class AudioSource:

    def __init__(self, source, stop_event, sample_rate=16000):
        self.source = source
        self.sample_rate = sample_rate
        self.q = queue.Queue()
        self.system = platform.system().lower()
        self.input_channels = 1
        self.stop_event = stop_event
        self.process = None

    # ---------------------------------------
    # CALLBACK
    # ---------------------------------------

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(status)

        audio = np.frombuffer(
            indata,
            dtype=np.int16
        )

        if self.input_channels > 1:
            audio = audio.reshape(
                -1,
                self.input_channels
            )
            audio = audio.mean(axis=1)

        self.q.put(
            audio.astype(np.int16).tobytes()
        )


    # ---------------------------------------
    # MICROPHONE
    # ---------------------------------------

    def _mic_stream(self):
        self.input_channels = 1
        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._callback
        ):
            while not self.stop_event.is_set():
                try:
                    yield self.q.get(
                        timeout=0.5
                    )
                except queue.Empty:
                    continue




    # ---------------------------------------
    # SYSTEM AUDIO WINDOWS
    # ---------------------------------------
    def _system_stream_windows(self):
        import soundcard as sc
        speakers = sc.default_speaker()

        if speakers is None:
            raise RuntimeError(
                "No Windows speaker found"
            )

        print(
            "Capturing:",
            speakers.name
        )

        with sc.get_microphone(
            id=str(speakers.name),
            include_loopback=True
        ).recorder(
            samplerate=self.sample_rate,
            channels=1
        ) as mic:

            while not self.stop_event.is_set():
                data = mic.record(
                    numframes=1024
                )
                if data.size == 0:
                    continue
                pcm = (data * 32767).astype(np.int16)

                yield pcm.tobytes()


    # ---------------------------------------
    # SYSTEM AUDIO LINUX
    # ---------------------------------------
    def _system_stream_linux(self):
        command = [
            FFMPEG,
            "-loglevel",
            "quiet",
            "-f",
            "pulse",
            "-i",
            "default",
            "-ar",
            str(self.sample_rate),
            "-ac",
            "1",
            "-f",
            "s16le",
            "-"
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            bufsize=0
        )

        process = self.process


        while not self.stop_event.is_set():
            data = process.stdout.read(4096)
            if data:
                yield data
            else:
                time.sleep(0.01)

        self._terminate(process)

    # ---------------------------------------
    # MAC
    # ---------------------------------------
    def _system_stream_macos(self):
        command = [
            FFMPEG,
            "-loglevel",
            "quiet",
            "-f",
            "avfoundation",
            "-i",
            ":0",
            "-ar",
            str(self.sample_rate),
            "-ac",
            "1",
            "-f",
            "s16le",
            "-"
        ]


        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            bufsize=0
        )

        process = self.process

        while not self.stop_event.is_set():
            data = process.stdout.read(4096)

            if data:
                yield data

            else:
                time.sleep(0.01)

        self._terminate(process)



    # ---------------------------------------
    # FILE
    # ---------------------------------------
    def _file_stream(self):
        command = [
            FFMPEG,
            "-loglevel",
            "quiet",
            "-i",
            self.source,
            "-ar",
            str(self.sample_rate),
            "-ac",
            "1",
            "-f",
            "s16le",
            "-"
        ]


        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            bufsize=0
        )
        process = self.process


        while not self.stop_event.is_set():
            data = process.stdout.read(4096)
            if data:
                yield data

            else:
                time.sleep(0.01)

        self._terminate(process)


    # ---------------------------------------
    # TERMINATE
    # ---------------------------------------
    def _terminate(self, process):
        if process is None:
            return

        try:
            if process.poll() is None:

                try:
                    process.stdout.close()
                except Exception:
                    pass

                process.terminate()

                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

        except Exception as e:
            print("terminate error:", e)    

    # ---------------------------------------
    # SHUTDOWN
    # ---------------------------------------
    def shutdown(self):
        print("Audio service shutdown")

        self.stop_event.set()

        if self.process:
            self._terminate(self.process)
            self.process = None



    # ---------------------------------------
    # ENTRY
    # ---------------------------------------
    def stream(self):
        print(
            f"source mode: {self.source} | system {self.system}"
        )
        if self.source == "mic":
            return self._mic_stream()


        if self.source == "system":
            if self.system == "windows":
                return self._system_stream_windows()
            elif self.system == "linux":
                return self._system_stream_linux()
            elif self.system == "darwin":
                return self._system_stream_macos()

        return self._file_stream()