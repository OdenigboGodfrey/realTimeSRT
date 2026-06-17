from PyQt5 import QtWidgets, QtCore, QtGui
import signal

# 1. Allow Python's default signal handler to catch Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, signal.SIG_DFL)


class DraggableLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._window = None
        self._drag_pos = None
        self.setCursor(QtGui.QCursor(QtCore.Qt.SizeAllCursor))

    def set_window(self, window):
        self._window = window

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            # self._drag_pos = event.globalPos() - self._window.frameGeometry().topLeft()
            self._drag_pos = event.globalPos() - self._window.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self._drag_pos is not None:
            self._window.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = None
            event.accept()


class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # --- main label ---
        self.label = DraggableLabel("", self)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("""
            color: white;
            font-size: 26px;
            background-color: rgba(0, 0, 0, 160);
            padding: 12px;
            border-radius: 8px;
        """)
        self.label.set_window(self)

        # --- close button ---
        self.close_btn = QtWidgets.QPushButton("✕")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 80, 80, 180);
                color: white;
                border-radius: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 80, 80, 240);
            }
        """)

        self.close_btn.clicked.connect(self.request_shutdown)

        # --- layout wrapper ---
        container = QtWidgets.QWidget(self)
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.label)

        # overlay button on top-right
        self.close_btn.setParent(container)
        self.close_btn.move(container.width() - 35, 5)

        container_layout.addWidget(self.label)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        self.setLayout(layout)

        self.setFixedSize(900, 170)

        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            screen.height() - 180
        )

        # keep button positioned on resize
        self.container = container
        self.container.resizeEvent = self._reposition_close_button

    def _reposition_close_button(self, event):
        self.close_btn.move(self.container.width() - 35, 5)

    def request_shutdown(self):
        # emit a signal-like callback via parent traversal or global hook
        QtWidgets.QApplication.quit()

    def set_text(self, text):
        print(f"text: {text}")

        text = text.strip()

        if not text:
            return

        # Keep only the latest part that fits
        max_chars = 200

        if len(text) > max_chars:
            text = "..." + text[-max_chars:]

        self.label.setText(text)
