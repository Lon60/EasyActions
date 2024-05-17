import sys
import os
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QListWidget, QListWidgetItem, QHBoxLayout, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt

from app.recorder import Recorder

class ListWidgetItem(QWidget):
    def __init__(self, name, list_widget, json_dir):
        super().__init__()
        self.name = name
        self.list_widget = list_widget
        self.json_dir = json_dir

        layout = QHBoxLayout()
        self.label = QLabel(self.name)
        layout.addWidget(self.label)

        self.delete_button = QPushButton("X")
        self.delete_button.setFixedSize(QSize(20, 20))
        self.delete_button.clicked.connect(self.delete_item)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def delete_item(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item_widget = self.list_widget.itemWidget(item)
            if item_widget == self:
                self.list_widget.takeItem(i)
                break
        os.remove(os.path.join(self.json_dir, f"{self.name}.json"))

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = Recorder()
        self.recorder.warning_signal.connect(self.show_warning)

        self.json_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'app', 'json')
        os.makedirs(self.json_dir, exist_ok=True)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Recorder')
        layout = QVBoxLayout()

        script_dir = os.path.dirname(os.path.realpath(__file__))

        self.record_button = QPushButton()
        self.record_button.setIcon(QIcon(os.path.join(script_dir, "app/record_icon.png")))
        self.record_button.setIconSize(QSize(100, 100))
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

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
        item_widget = self.recordings_list.itemWidget(item)
        item_text = item_widget.name if item_widget else ""
        if item_text:
            recording_path = os.path.join(self.json_dir, f"{item_text}.json")
            if os.path.exists(recording_path):
                threading.Thread(target=self.recorder.play_recording, args=(recording_path,)).start()
            else:
                self.show_warning()

    def populate_recordings_list(self):
        self.recordings_list.clear()
        for filename in os.listdir(self.json_dir):
            if filename.endswith('.json'):
                item_name = os.path.splitext(filename)[0]
                item_widget = ListWidgetItem(item_name, self.recordings_list, self.json_dir)
                item = QListWidgetItem()
                item.setSizeHint(item_widget.sizeHint())
                self.recordings_list.addItem(item)
                self.recordings_list.setItemWidget(item, item_widget)

    def show_warning(self):
        QMessageBox.warning(self, "Warning", "No recording file found.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.aboutToQuit.connect(lambda: ex.recorder.stop_recording())
    ex.show()
    sys.exit(app.exec_())
