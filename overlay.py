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

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setFixedSize(900, 170)

        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            screen.height() - 180
        )

        # 2. Add the heartbeat timer to periodically return control to Python
        self.interrupt_timer = QtCore.QTimer(self)
        self.interrupt_timer.setInterval(500)  # Check every 500ms
        self.interrupt_timer.timeout.connect(lambda: None)  # Dummy function, no action
        self.interrupt_timer.start()

    def set_text(self, text):
        print(f"text: {text}")

        text = text.strip()

        if not text:
            return

        # Keep only the latest part that fits
        max_chars = 140

        if len(text) > max_chars:
            text = "..." + text[-max_chars:]

        self.label.setText(text)