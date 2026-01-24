import sys
import xlwings as xw
from PyQt5 import QtWidgets, QtCore
import vlc

# -----------------------------
# Excel Widget with Slide-In Animation
# -----------------------------
class ExcelWidget(QtWidgets.QTextEdit):
    def __init__(self, workbook_path, cell_range):
        super().__init__()
        self.workbook_path = workbook_path
        self.cell_range = cell_range

        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                font-size: 30px;
                font-family: Trebuchet MS;
                padding: 10px;
                background: #111;
                color: Yellow;
            }
        """)
        
        # Timer to refresh Excel data
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(2000)  # update every 2 seconds

        self.update_data()
        self.animate_slide_in_right()

    def update_data(self):
        try:
            wb = xw.Book(self.workbook_path)
            sheet = wb.sheets[0]
            data = sheet.range(self.cell_range).value

            # Format data as text
            formatted = ""
            if isinstance(data, list):
                for row in data:
                    formatted += "   ".join(str(x) for x in row) + "\n"
            else:
                formatted = str(data)

            self.setText(formatted)

            # Trigger slide-in animation
            #self.animate_slide_in_left()
            #self.animate_slide_in_right()

        except Exception as e:
            self.setText(f"Error reading Excel: {e}")

    def animate_slide_in_left(self):
        start_rect = QtCore.QRect(-self.width(), self.y(), self.width(), self.height())
        end_rect = QtCore.QRect(0, self.y(), self.width(), self.height())

        self.anim = QtCore.QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(2000)
        self.anim.setStartValue(end_rect)
        self.anim.setEndValue(start_rect)
        self.anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.anim.start()
    
    def animate_slide_in_right(self):
        start_rect = QtCore.QRect(-self.width(), self.y(), self.width(), self.height())
        end_rect = QtCore.QRect(0, self.y(), self.width(), self.height())

        self.anim = QtCore.QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(2000)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.anim.start()

# -----------------------------
# VLC Video Widget
# -----------------------------
class VideoWidget(QtWidgets.QFrame):
    def __init__(self, video_path):
        super().__init__()
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        self.video_path = video_path

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_loop)
        self.timer.start(500)

    def showEvent(self, event):
        super().showEvent(event)
        self.play_video()

    def play_video(self):
        media = self.instance.media_new(self.video_path)
        self.mediaplayer.set_media(media)
        self.mediaplayer.set_hwnd(int(self.winId()))
        self.mediaplayer.play()

    def check_loop(self):
        if self.mediaplayer.get_state() == vlc.State.Ended:
            self.play_video()

# -----------------------------
# Main Window (4-grid layout)
# -----------------------------
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        layout = QtWidgets.QGridLayout()

        # Add four placeholder widgets
        for row in range(2):
            for col in range(2):
                box = QtWidgets.QFrame()
                box.setStyleSheet("background-color: black")
                box.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding,
                    QtWidgets.QSizePolicy.Expanding
                )
                layout.addWidget(box, row, col)

        excel1 = ExcelWidget("C:/Users/evanc/OneDrive/Desktop/Awanas Grand Prix/Awana Timing Tracker.xlsm", "B6:D10")
        #excel2 = ExcelWidget("C:/Users/evanc/OneDrive/Desktop/Awanas Grand Prix/Awana Timing Tracker.xlsm", "E1:H4")
        #video1 = VideoWidget("C:/Users/evanc/OneDrive/Desktop/Awanas Grand Prix/cutscene1.mp4")
        #video2 = VideoWidget("C:/Users/evanc/OneDrive/Desktop/Awanas Grand Prix/cutscene1.mp4")
        video3 = VideoWidget("C:/Recordings/Recording1.mp4")
        video4 = VideoWidget("C:/Recordings/Recording2.mp4")

        layout.addWidget(excel1, 0, 0)
        layout.addWidget(video3, 0, 1)
        #layout.addWidget(excel1, 1, 1)
        layout.addWidget(video4, 1, 1)

        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self.setLayout(layout)
        self.showMaximized()
        self.setWindowTitle("4-Grid Dashboard with Animation")

# -----------------------------
# Run App
# -----------------------------
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
