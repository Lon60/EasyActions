import sys
import os
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QListWidget, QListWidgetItem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

from app.recorder import Recorder  # Import the Recorder class from recorder.py

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = Recorder()
        self.recorder.warning_signal.connect(self.show_warning)  # Connect the signal to the slot

        # Ensure the json directory exists in app/json
        self.json_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'app', 'json')
        os.makedirs(self.json_dir, exist_ok=True)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Recorder')
        layout = QVBoxLayout()

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.realpath(__file__))

        # Create record button
        self.record_button = QPushButton()
        self.record_button.setIcon(QIcon(os.path.join(script_dir, "app/record_icon.png")))
        self.record_button.setIconSize(QSize(100, 100))
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        # Create recordings list
        self.recordings_list = QListWidget()
        self.recordings_list.itemClicked.connect(self.play_selected_recording)
        self.populate_recordings_list()
        layout.addWidget(self.recordings_list)

        self.setLayout(layout)

    def toggle_recording(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        if self.record_button.isChecked():
            self.recorder.start_recording()
            self.record_button.setIcon(QIcon(os.path.join(script_dir, "app/stop_icon.png")))
        else:
            self.recorder.stop_recording()
            self.record_button.setIcon(QIcon(os.path.join(script_dir, "app/record_icon.png")))
            self.populate_recordings_list()

    def play_selected_recording(self, item):
        recording_path = os.path.join(self.json_dir, item.text())
        threading.Thread(target=self.recorder.play_recording, args=(recording_path,)).start()

    def populate_recordings_list(self):
        self.recordings_list.clear()
        for filename in os.listdir(self.json_dir):
            if filename.endswith('.json'):
                item = QListWidgetItem(filename)
                item.setToolTip(f'Click to play {filename}')
                self.recordings_list.addItem(item)

    def show_warning(self):
        QMessageBox.warning(self, "Warning", "No recording file found.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.aboutToQuit.connect(lambda: ex.recorder.stop_recording())
    ex.show()
    sys.exit(app.exec_())
