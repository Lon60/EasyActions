import sys
from PyQt5.QtWidgets import QApplication
from app.ui import App
from app.recorder import Recorder

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = Recorder()
    ex = App(recorder)
    app.aboutToQuit.connect(lambda: recorder.stop_recording())
    ex.show()
    sys.exit(app.exec_())
