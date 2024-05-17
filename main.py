import sys
import os
import json
import time
import threading
import pyautogui
from pynput import mouse, keyboard
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QListWidget, QListWidgetItem, QInputDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, pyqtSignal, QObject, Qt

class Recorder(QObject):
    warning_signal = pyqtSignal()  # Signal to show warning

    def __init__(self):
        super().__init__()
        self.input_data = []
        self.start_time = None
        self.recording = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.recording_name = ""

    def on_click(self, x, y, button, pressed):
        if self.recording:
            if pressed:
                if self.start_time is None:
                    self.start_time = time.time()
                self.input_data.append({
                    'event': 'click',
                    'button': str(button),
                    'position': (x, y),
                    'time': time.time() - self.start_time
                })

    def on_press(self, key):
        if self.recording:
            if self.start_time is None:
                self.start_time = time.time()
            try:
                self.input_data.append({
                    'event': 'press',
                    'key': key.char,
                    'time': time.time() - self.start_time
                })
            except AttributeError:
                self.input_data.append({
                    'event': 'press',
                    'key': str(key),
                    'time': time.time() - self.start_time
                })

    def start_recording(self):
        self.input_data = []
        self.start_time = None
        self.recording = True
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop_recording(self):
        self.recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        # Remove the last action if exists
        if self.input_data:
            self.input_data.pop()

        # Only prompt for a name if there are recorded events
        if self.input_data:
            # Prompt the user for a recording name
            name, ok = QInputDialog.getText(None, 'Save Recording', 'Enter a name for the recording:')
            if ok and name:
                self.recording_name = name
                with open(f'{self.recording_name}.json', 'w') as f:
                    json.dump(self.input_data, f)

    def play_recording(self, filename):
        try:
            with open(filename, 'r') as f:
                input_data = json.load(f)
        except FileNotFoundError:
            self.warning_signal.emit()  # Emit the warning signal
            return

        start_time = time.time()
        for event in input_data:
            sleep_time = event['time'] - (time.time() - start_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            if event['event'] == 'click':
                pyautogui.click(event['position'][0], event['position'][1])
            elif event['event'] == 'press':
                self.press_key(event['key'])

    def press_key(self, key):
        special_keys = {
            'Key.backspace': 'backspace',
            'Key.tab': 'tab',
            'Key.enter': 'enter',
            'Key.shift': 'shift',
            'Key.ctrl': 'ctrl',
            'Key.alt': 'alt',
            'Key.esc': 'esc',
            'Key.space': 'space',
            'Key.left': 'left',
            'Key.up': 'up',
            'Key.right': 'right',
            'Key.down': 'down',
            'Key.delete': 'delete'
        }
        if key in special_keys:
            pyautogui.press(special_keys[key])
        elif len(key) == 1:  # Check if the key is a single character
            pyautogui.typewrite(key)
        else:
            print(f"Unknown key: {key}")  # Log unknown keys

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = Recorder()
        self.recorder.warning_signal.connect(self.show_warning)  # Connect the signal to the slot
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Recorder')
        layout = QVBoxLayout()

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.realpath(__file__))

        # Create record button
        self.record_button = QPushButton()
        self.record_button.setIcon(QIcon(os.path.join(script_dir, "record_icon.png")))
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
            self.record_button.setIcon(QIcon(os.path.join(script_dir, "stop_icon.png")))
        else:
            self.recorder.stop_recording()
            self.record_button.setIcon(QIcon(os.path.join(script_dir, "record_icon.png")))
            self.populate_recordings_list()

    def play_selected_recording(self, item):
        threading.Thread(target=self.recorder.play_recording, args=(item.text(),)).start()

    def populate_recordings_list(self):
        self.recordings_list.clear()
        for filename in os.listdir('.'):
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
