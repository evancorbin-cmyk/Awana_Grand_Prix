import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QMovie
print(QMovie.supportedFormats())


class GifTest(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GIF Loop Test")
        layout = QVBoxLayout()

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.setLayout(layout)

        # Load GIF
        self.movie = QMovie("Journey_qt.gif")
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(100)

        self.label.setMovie(self.movie)
        self.movie.start()

app = QApplication(sys.argv)
window = GifTest()
window.show()
sys.exit(app.exec_())
