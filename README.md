```markdown
# RealTimeSRT

RealTimeSRT is a real-time speech-to-text overlay application that captures audio from your system or microphone and displays live transcription subtitles on screen.

It uses:

- **Vosk** for offline speech recognition
- **PyQt5** for the always-on-top subtitle overlay
- **FFmpeg** for audio capture and conversion
- **sounddevice** for microphone/system audio input

The goal is to provide a lightweight local alternative to cloud-based transcription tools.

---

## Features

- Real-time speech transcription
- Offline processing (no internet required)
- Always-on-top subtitle overlay
- Transparent draggable subtitle window
- System audio capture
- Microphone capture
- File transcription support
- Cross-platform support:
  - Linux
  - Windows
  - macOS (experimental)

---

## Demo

The application listens to audio and displays:

```

this is a live transcription example
appearing directly on your screen

````

The overlay stays visible above other applications.

---

# Installation

## Requirements

- Python 3.10+
- FFmpeg
- Vosk speech model

---

## Create virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
````

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# Download Speech Model

Download a Vosk model:

[https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)

Example:

```
vosk-model-small-en-us-0.15
```

Place it:

```
bin/shared/
```

Expected structure:

```
bin/
 └── shared/
      └── vosk-model-small-en-us-0.15/
```

---

# FFmpeg

The application automatically searches for FFmpeg.

Recommended structure:

```
bin/
 └── windows/
      └── ffmpeg.exe
```

---

# Running

Default:

```bash
python main.py
```

---

## Audio Sources

### System audio

```bash
python main.py --source system
```

Captures desktop audio.

Example:

* YouTube videos
* Meetings
* Games
* Browser audio

---

### Microphone

```bash
python main.py --source mic
```

Uses your microphone input.

---

### Audio file

```bash
python main.py --source path/to/file.wav
```

---

# Windows Audio Notes

Windows system audio capture depends on available audio devices.

Supported methods:

* WASAPI loopback devices
* Stereo Mix devices
* Virtual audio devices

Some systems do not expose loopback capture by default.

If no system audio device is available:

Enable:

```
Control Panel
 → Sound
 → Recording
 → Stereo Mix
 → Enable
```

or install a virtual audio device.

Examples:

* VB-CABLE
* VoiceMeeter

---

# Linux Audio

Linux uses PulseAudio capture:

```
-f pulse
```

The default audio source is:

```
default
```

If required, modify:

```python
_system_stream_linux()
```

to select another PulseAudio source.

---

# Project Structure

```
RealTimeSRT/

├── main.py
├── audio.py
├── overlay.py
├── transcriber.py
├── srt.py
├── utils.py
│
├── bin/
│    ├── shared/
│    │    └── vosk-model/
│    │
│    └── windows/
│         └── ffmpeg.exe
│
└── requirements.txt
```

---

# How It Works

Audio pipeline:

```
Audio Source
      |
      v
FFmpeg / sounddevice
      |
      v
PCM 16-bit audio stream
      |
      v
Vosk Speech Recognition
      |
      v
PyQt Overlay
      |
      v
Live subtitles
```

---

# Controls

* Drag the subtitle window with the mouse
* Close application normally to stop audio capture

---

# Performance

The application runs fully locally.

Performance depends on:

* CPU speed
* Vosk model size
* Audio source quality

The small English model is optimized for lower latency.

For better accuracy use a larger model.

---

# Troubleshooting

## No transcription

Check:

* Audio source is correct
* Microphone permissions
* System audio device availability

---

## Windows: No system audio

Run:

```bash
python main.py --source system
```

If no device appears, enable Stereo Mix or install a virtual audio device.

---

## Overlay text overflow

The overlay intentionally keeps the newest transcription visible and limits the display area.

---
