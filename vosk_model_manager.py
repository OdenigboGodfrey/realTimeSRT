import os
import zipfile
import requests
from pathlib import Path
import platform

APP_NAME = "RealTimeSRT"

if platform.system() == "Windows":
    data_dir = Path(os.environ["LOCALAPPDATA"]) / APP_NAME
else:
    data_dir = Path.home() / ".local" / "share" / APP_NAME

MODEL_ROOT = data_dir / "models"

VOSK_MODELS = {
    "small": {
        "name": "vosk-model-small-en-us-0.15",
        "download_url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "description": "Fastest model with lowest memory usage",
        "size": 40,
    },
    "medium": {
        "name": "vosk-model-en-us-0.22-lgraph",
        "download_url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip",
        "description": "Model with good balance between speed and accuracy",
        "size": 125,
    },
    "large": {
        "name": "vosk-model-en-us-0.22",
        "download_url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
        "description": "Highest accuracy, much larger in size and heavier",
        "size": 1800,
    },
}

# MODEL_DIR = "models/vosk-model-small-en-us-0.15"

class VoskModelManager:
    def __init__(self, model_name, progress_signal=None):
        if model_name not in VOSK_MODELS:
            raise ValueError(f"Invalid model name: {model_name}")
        
        self.model_name = model_name
        self.model = VOSK_MODELS[self.model_name]
        self.model_dir = self.model_path()
        self.model_url = self.model["download_url"]
        self.progress_signal = progress_signal


    def get_supported_vosk_models(self):
        return [model["name"] for model in VOSK_MODELS.values()]

    def model_path(self):
        model_root = MODEL_ROOT / self.model["name"]
        model_root.mkdir(parents=True, exist_ok=True)
        return model_root
    
    def ensure_model(self):
        if self.validate_model_folder():
            return self.model_dir

        zip_path = str(self.model_dir) + f"{self.model['name']}.zip"

        if os.path.exists(zip_path):
            if not self.validate_model_zip(zip_path):
                # download file as the existing one is too small
                os.remove(zip_path)
                self.download_file(zip_path)
        else:
            self.download_file(zip_path)

        print("Extracting...")

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(self.model_dir)
        # move extracted content out of the inner dir created to self.model_dir
        for path in self.model_dir.rglob("*"):
            path.rename(self.model_dir / path.name)

        os.remove(zip_path)
        return self.model_dir
    
    def download_file(self, zip_path):
        with requests.get(self.model_url, stream=True) as r:
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            
            r.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = downloaded * 100 / total
                    msg = f"Downloading Vosk model... {percent:.2f}%"
                    self._emit(msg)

    def get_directory_size_mb(self):
        total = 0

        for path in self.model_dir.rglob("*"):
            if path.is_file():
                total += path.stat().st_size

        return total / (1024 * 1024)
    
    def get_file_size_mb(self, path):
        return Path(path).stat().st_size / (1024 * 1024)

    def validate_model_zip(self, zip_path):
        # check file size
        actual_size = self.get_file_size_mb(zip_path)
        expected_size = self.model["size"]

        # allow 20% variance
        min_size = expected_size * 0.8

        return actual_size > min_size

    def validate_model_folder(self):
        if not self.model_dir.exists():
            return False

        actual_size = self.get_directory_size_mb()
        expected_size = self.model["size"]

        # allow 20% variance
        min_size = expected_size * 0.8

        return actual_size >= min_size

    def _emit(self, msg: str):
        if self.progress_signal:
            try:
                self.progress_signal.emit(msg)
            except Exception:
                pass

