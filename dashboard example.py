import sys
import vlc
from PyQt5 import QtWidgets, QtCore, QtGui

VIDEO_PATH = "C:/Users/evanc/OneDrive/Desktop/Awanas Grand Prix/cutscene1.mp4"
VIDEO_PATH_2 = "C:/Users/evanc/OneDrive/Desktop/Awanas Grand Prix/cutscene1.mp4"
VIDEO_PATH_3 = "C:/Recordings/recording1.mp4"

class VideoWidget(QtWidgets.QFrame):
    def __init__(self, video_path):
        super().__init__()

        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()

        # Make widget black
        self.setStyleSheet("background-color: black;")

    def play(self, video_path):
        media = self.instance.media_new(video_path)

        # Loop forever
        media.add_option("input-repeat=65535")

        self.mediaplayer.set_media(media)

        # Bind VLC output to this widget
        if sys.platform.startswith("linux"):
            self.mediaplayer.set_xwindow(self.winId())
        elif sys.platform == "win32":
            self.mediaplayer.set_hwnd(self.winId())
        elif sys.platform == "darwin":
            self.mediaplayer.set_nsobject(int(self.winId()))

        self.mediaplayer.play()

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create 4 grid cells
        self.boxes = []

        for i in range(4):
            frame = QtWidgets.QFrame()
            frame.setStyleSheet("background-color: #222;")
            frame.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                QtWidgets.QSizePolicy.Expanding)
            self.boxes.append(frame)

        # Insert into grid
        layout.addWidget(self.boxes[0], 0, 0)
        layout.addWidget(self.boxes[1], 0, 1)
        layout.addWidget(self.boxes[2], 1, 0)
        layout.addWidget(self.boxes[3], 1, 1)

        # Equal stretch
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self.setLayout(layout)

        # Create VLC video widgets in 2 squares
        self.video1 = VideoWidget(VIDEO_PATH)
        #self.video2 = VideoWidget(VIDEO_PATH_2)
        self.video3 = VideoWidget(VIDEO_PATH_3)

        layout.replaceWidget(self.boxes[0], self.video1)
        layout.replaceWidget(self.boxes[3], self.video3)

        self.boxes[2].deleteLater()
        self.boxes[3].deleteLater()

        # Fullscreen
        self.showMaximized()

        # Start playback after window is visible
        QtCore.QTimer.singleShot(300, self.start_videos)

    def start_videos(self):
        self.video1.play(VIDEO_PATH)
        self.video3.play(VIDEO_PATH_3)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
