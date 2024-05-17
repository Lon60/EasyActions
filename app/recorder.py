import json
import time
import os
import pyautogui
from pynput import mouse, keyboard
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QInputDialog

class Recorder(QObject):
    warning_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.input_data = []
        self.start_time = None
        self.recording = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.recording_name = ""

        self.json_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'json')
        os.makedirs(self.json_dir, exist_ok=True)

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
        if not self.recording:
            return

        self.recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

        if self.input_data:
            self.input_data.pop()

        if self.input_data and self.recording_name == "":
            name, ok = QInputDialog.getText(None, 'Save Recording', 'Enter a name for the recording:')
            if ok and name:
                self.recording_name = name
                filepath = os.path.join(self.json_dir, f'{self.recording_name}.json')
                with open(filepath, 'w') as f:
                    json.dump(self.input_data, f)
                self.recording_name = ""  # Reset the recording name after saving

    def play_recording(self, filepath):
        try:
            with open(filepath, 'r') as f:
                input_data = json.load(f)
        except FileNotFoundError:
            self.warning_signal.emit()
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
        special_keys = [
            'backspace', 'tab', 'enter', 'shift', 'ctrl', 'alt', 'esc',
            'space', 'left', 'up', 'right', 'down', 'delete'
        ]
        key_name = key.replace('Key.', '')
        if key_name in special_keys:
            pyautogui.press(key_name)
        elif len(key) == 1:
            pyautogui.typewrite(key)
        else:
            print(f"Unknown key: {key}")
