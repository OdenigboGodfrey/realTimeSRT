from PyQt5 import QtWidgets
from shared import APP_NAME
from vosk_model_manager import VOSK_MODELS


class StartupWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.setFixedSize(500, 250)

        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
                color: white;
                font-size: 14px;
            }

            QComboBox {
                padding: 8px;
            }

            QPushButton {
                background: #0078d7;
                color: white;
                padding: 10px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background: #1084e2;
            }
        """)

        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("Select Model")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
        """)
        layout.addWidget(title)

        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.addItems(VOSK_MODELS.keys())
        layout.addWidget(self.model_combo)

        self.model_info = QtWidgets.QLabel()
        self.model_info.setWordWrap(True)
        layout.addWidget(self.model_info)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)
        self.start_btn = QtWidgets.QPushButton(
            "Start Transcription"
        )
        layout.addWidget(self.start_btn)
        
        layout.addStretch()
        self.setLayout(layout)
        self.model_combo.currentTextChanged.connect(
            self.update_model_info
        )
        self.update_model_info(
            self.model_combo.currentText()
        )

    def update_model_info(self, model_key):
        model = VOSK_MODELS[model_key]
        self.model_info.setText(
            f"<b>{model['name']}</b><br>"
            f"{model['description']}<br><br>"
            f"Download Size: ~{model['size']} MB"
        )

    def selected_model(self):
        return self.model_combo.currentText()

    def set_status(self, text):
        self.status_label.setText(text)