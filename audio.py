import queue
import subprocess
import sounddevice as sd
import numpy as np
import platform
import threading
import os
import time
from ffmpeg_binary_manager import get_ffmpeg_binary

stop_event = threading.Event()

FFMPEG = get_ffmpeg_binary("ffmpeg")


class AudioSource:
    def __init__(self, source, sample_rate=16000):
        self.source = source
        self.sample_rate = sample_rate
        self.q = queue.Queue()
        self.system = platform.system().lower()

    # ---------------------------------------
    # SILENCE DETECTION
    # ---------------------------------------
    def is_silent(self, chunk, threshold=1000):
        audio = np.frombuffer(chunk, dtype=np.int16)
        return np.abs(audio).mean() < threshold

    # ---------------------------------------
    # MIC
    # ---------------------------------------
    def _mic_callback(self, indata, frames, time_info, status):
        if status:
            print(status)
        self.q.put(bytes(indata))

    def _mic_stream(self):
        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._mic_callback
        ):
            while not stop_event.is_set():
                try:
                    yield self.q.get(timeout=0.5)
                except queue.Empty:
                    continue

    # ---------------------------------------
    # MAKE FFmpeg NON-BLOCKING
    # ---------------------------------------
    def __make_nonblocking(self, process):
        import fcntl
        fd = process.stdout.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    
    # ---------------------------------------
    # UNIVERSAL NON-BLOCKING FOR FFmpeg
    # ---------------------------------------
    def __make_nonblocking(self, process):
        process._stdout_queue = queue.Queue(maxsize=500)
        process._is_eof = False
        
        def _reader():
            print("reader started")
            while not stop_event.is_set():
                try:
                    chunk = real_read(4096)
                    if not chunk:
                        process._is_eof = True
                        break
                    print("reader got", len(chunk))
                    process._stdout_queue.put(chunk)
                except Exception:
                    process._is_eof = True
                    break
            try:
                process.stdout.close()
            except Exception:
                pass

        process._stdout_thread = threading.Thread(target=_reader, daemon=True)
        process._stdout_thread.start()

        # FIXED: Pop whatever is available instantly without trapping execution
        def _non_blocking_read(n):
            data = b""
            try:
                # Grab just one chunk from the queue if available
                data = process._stdout_queue.get_nowait()
            except queue.Empty:
                pass
            return data

        real_read = process.stdout.read
        process.stdout.read = _non_blocking_read

    # ---------------------------------------
    # UNIVERSAL NON-BLOCKING FOR FFmpeg
    # ---------------------------------------
    def _make_nonblocking(self, process):
        real_read = process.stdout.read

        process._stdout_queue = queue.Queue(maxsize=500)
        process._is_eof = False

        def _reader():
            while not stop_event.is_set():
                try:
                    chunk = real_read(4096)

                    if not chunk:
                        process._is_eof = True
                        break

                    try:
                        process._stdout_queue.put_nowait(chunk)
                    except queue.Full:
                        # Drop oldest chunk if queue is full
                        try:
                            process._stdout_queue.get_nowait()
                            process._stdout_queue.put_nowait(chunk)
                        except queue.Empty:
                            pass

                except Exception:
                    process._is_eof = True
                    break

            try:
                process.stdout.close()
            except Exception:
                pass

        process._stdout_thread = threading.Thread(
            target=_reader,
            daemon=True
        )
        process._stdout_thread.start()

        def _non_blocking_read(n=4096):
            chunks = []
            total = 0

            while total < n:
                try:
                    chunk = process._stdout_queue.get_nowait()
                    chunks.append(chunk)
                    total += len(chunk)
                except queue.Empty:
                    break

            return b"".join(chunks)

        process.stdout.read = _non_blocking_read

    # ---------------------------------------
    # SYSTEM AUDIO - LINUX
    # ---------------------------------------
    def _system_stream_linux(self):
        command = [
           FFMPEG,
            "-loglevel", "quiet",
            "-f", "pulse",
            "-i", "default",
            "-ar", str(self.sample_rate),
            "-ac", "1",
            "-f", "s16le",
            "-"
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=0)
        self._make_nonblocking(process)

        while not stop_event.is_set():
            try:
                data = process.stdout.read(16000)
                if data:
                    yield data
            except:
                time.sleep(0.01)

        self._terminate(process)

    # ---------------------------------------
    # SYSTEM AUDIO - WINDOWS
    # ---------------------------------------
    def _system_stream_windows(self):
        command = [
            FFMPEG,
            "-loglevel", "quiet",
            "-f", "wasapi",
            "-i", "default",
            "-ac", "1",
            "-ar", str(self.sample_rate),
            "-f", "s16le",
            "-"
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=0)

        self._make_nonblocking(process)

        while not stop_event.is_set():
            try:
                data = process.stdout.read(16000)
                if data:
                    yield data
                else:
                    time.sleep(0.01)
            except Exception:
                time.sleep(0.01)

        self._terminate(process)

    # ---------------------------------------
    # SYSTEM AUDIO - MAC
    # ---------------------------------------
    def _system_stream_macos(self):
        command = [
            FFMPEG,
            "-loglevel", "quiet",
            "-f", "avfoundation",
            "-i", ":0",
            "-ar", str(self.sample_rate),
            "-ac", "1",
            "-f", "s16le",
            "-"
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=0)
        self._make_nonblocking(process)

        while not stop_event.is_set():
            try:
                data = process.stdout.read(16000)
                if data:
                    yield data
            except:
                time.sleep(0.01)

        self._terminate(process)

    # ---------------------------------------
    # FILE STREAM
    # ---------------------------------------
    def _file_stream(self):
        command = [
            FFMPEG,
            "-loglevel", "quiet",
            "-i", self.source,
            "-ar", str(self.sample_rate),
            "-ac", "1",
            "-f", "s16le",
            "-"
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=0)
        self._make_nonblocking(process)

        while not stop_event.is_set():
            try:
                data = process.stdout.read(16000)
                if data:
                    yield data
            except:
                time.sleep(0.01)

        self._terminate(process)

    # ---------------------------------------
    # SAFE TERMINATION
    # ---------------------------------------
    def _terminate(self, process):
        try:
            process.terminate()
            process.wait(timeout=2)
        except Exception:
            process.kill()

    # ---------------------------------------
    # ENTRY
    # ---------------------------------------
    def stream(self):
        print(f"source mode: {self.source} | system {self.system}")

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