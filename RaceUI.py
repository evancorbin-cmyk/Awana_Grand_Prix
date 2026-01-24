from ast import If
import sys
import subprocess
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QScrollArea
)
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QMovie
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QSoundEffect

###############################################################
# Utility: Load CSV into a list of rows
###############################################################
def load_csv(filename):
    try:
        with open(filename, newline="") as f:
            reader = csv.reader(f)
            return list(reader)
    except FileNotFoundError:
        return []

###############################################################
# FINAL RESULTS DIALOG
###############################################################
class FinalResultsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Final Results")
        self.setGeometry(100, 100, 1600, 900)
        self.showMaximized()

        # Background
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(QPixmap("checker_bg.png")))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("<b>Final Leaders</b>")
        title_label.setStyleSheet("font-size: 32px; color: yellow; font-family: 'Comic Sans MS'; font-weight: bold; background-color: black; padding: 10px;")
        main_layout.addWidget(title_label, alignment=Qt.AlignHCenter)

        # Scroll area for categories
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Load final_leaders.csv and group by category
        final_data = load_csv("final_leaders.csv")
        
        if not final_data or len(final_data) < 2:
            error_label = QLabel("No final results available")
            error_label.setStyleSheet("font-size: 20px; color: red; font-family: 'Comic Sans MS';")
            scroll_layout.addWidget(error_label)
        else:
            # Parse headers and data
            headers = final_data[0]
            rows = final_data[1:]

            # Group by category (preserving order)
            categories_dict = {}
            category_order = []
            cat_index = headers.index("Category") if "Category" in headers else 1
            
            for row in rows:
                category = row[cat_index]
                if category not in categories_dict:
                    categories_dict[category] = []
                    category_order.append(category)
                categories_dict[category].append(row)

            # Create table for each category
            category_gifs = {
                "Cubbies": "Cubbies_horizontal_waving.gif",
                "Sparks": "Sparks_horizontal_waving.gif",
                "T&T": "TT_horizontal_waving.gif",
                "Journey": "Journey_horizontal_waving.gif",
                "Trek": "Trek_horizontal_waving.gif",
                "GroupB": "group_b_epic_race.gif"
            }

            for category in category_order:
                cat_rows = categories_dict[category]

                # Category container with horizontal layout
                cat_layout = QHBoxLayout()

                # Create table
                table = QTableWidget()
                table.setFixedWidth(900)
                table.setFixedHeight(250)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                table.verticalHeader().setVisible(False)
                table.horizontalHeader().setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                table.setStyleSheet("""
                    QTableWidget {
                        background-color: black !important;
                        color: yellow;
                        font-size: 20px;
                        font-family: 'Comic Sans MS';
                        font-weight: bold;
                    }
                    QHeaderView::section {
                        background-color: black !important;
                        color: yellow;
                        font-size: 18px;
                        font-family: 'Comic Sans MS';
                        font-weight: bold;
                        padding: 4px;
                        qproperty-alignment: AlignHCenter;
                    }
                """)

                # Populate table
                pretty_headers = [h if h in ["Place", "Car #"] else h.replace("_", " ").title().replace("Ms)", "ms)") for h in headers]
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(pretty_headers)
                table.setRowCount(len(cat_rows))

                for r, row in enumerate(cat_rows):
                    for c, value in enumerate(row):
                        item = QTableWidgetItem(value)
                        item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                        table.setItem(r, c, item)

                cat_layout.addWidget(table)

                # Add GIF if available
                if category in category_gifs:
                    gif_label = QLabel()
                    gif_label.setAlignment(Qt.AlignCenter)
                    
                    # Create movie and get its dimensions
                    movie = QMovie(category_gifs[category])
                    movie.setCacheMode(QMovie.CacheAll)
                    movie.setSpeed(100)
                    
                    # Get the frame size from the movie
                    if movie.frameCount() > 0:
                        frame_size = movie.frameRect().size()
                        if frame_size.height() > 0:
                            # Scale to height of 250 while maintaining aspect ratio
                            scale_factor = 250 / frame_size.height()
                            scaled_width = int(frame_size.width() * scale_factor)
                            gif_label.setFixedWidth(scaled_width)
                            gif_label.setFixedHeight(250)
                    
                    gif_label.setMovie(movie)
                    movie.start()
                    cat_layout.addWidget(gif_label)

                # Add category section to scroll layout
                cat_container = QWidget()
                cat_container.setLayout(cat_layout)
                scroll_layout.addWidget(cat_container)

            scroll_layout.addStretch()

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(120, 40)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #222;
                color: yellow;
                font-size: 18px;
                font-family: 'Comic Sans MS';
                font-weight: bold;
                border: 2px solid yellow;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def resizeEvent(self, event):
        bg = QPixmap("checker_bg.png")
        scaled = bg.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)

        super().resizeEvent(event)


###############################################################
# Reusable Table Panel With Background + Styling + Animation
###############################################################

class DataPanel(QWidget):
    animation_finished = pyqtSignal()

    def __init__(self, title, bg_image, fixed_height=340):
        super().__init__()

        # Background
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(QPixmap(bg_image)))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)

        # Title
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setStyleSheet("font-size: 26px; color: yellow; font-family: 'Comic Sans MS';")
        layout.addWidget(title_label, alignment=Qt.AlignLeft)

        # Table
        self.table = QTableWidget()
        self.table.setFixedWidth(1200)
        self.table.setFixedHeight(200)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: black !important;
                color: yellow;
                font-size: 22px;
                font-family: 'Comic Sans MS';
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: black !important;
                color: yellow;
                font-size: 20px;
                font-family: 'Comic Sans MS';
                font-weight: bold;
                padding: 4px;
                qproperty-alignment: AlignHCenter;
            }
        """)

        layout.addWidget(self.table, alignment=Qt.AlignHCenter)
        self.setLayout(layout)
        self.setMaximumHeight(fixed_height)
        self.setMinimumHeight(200)

        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_next_row)

        # Animation state
        self.pending_rows = []
        self.current_row_index = 0
        self.active_animations = []

        # Swoosh sound (must be WAV)
        self.swoosh = QSoundEffect()
        self.swoosh.setSource(QUrl.fromLocalFile("swoosh.wav"))
        self.swoosh.setVolume(1.0)  # full volume

    ###############################################################
    # Slide‑in animation logic
    ###############################################################
    def animate_next_row(self):
        if self.current_row_index >= len(self.pending_rows):
            self.animation_timer.stop()
            self.animation_finished.emit()
            return

        row_data = self.pending_rows[self.current_row_index]

        # Insert a new row
        r = self.table.rowCount()
        self.table.insertRow(r)

        # Create container widget for the entire row
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        for value in row_data:
            lbl = QLabel(value)
            lbl.setStyleSheet("color: yellow; font-size: 22px; font-family: 'Comic Sans MS';")
            lbl.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            container_layout.addWidget(lbl)

        # Attach container to first column and span full width
        self.table.setCellWidget(r, 0, container)
        self.table.setSpan(r, 0, 1, len(row_data))

        # Position off-screen
        y = self.table.rowViewportPosition(r)
        container.move(-1000, y)

        # Play swoosh sound
        self.swoosh.play()

        # Animate slide-in
        anim = QPropertyAnimation(container, b"pos")
        anim.setDuration(600)
        anim.setStartValue(QPoint(-1000, y))
        anim.setEndValue(QPoint(0, y))

        self.active_animations.append(anim)
        anim.start()

        self.current_row_index += 1

    ###############################################################
    # Update table with optional animation
    ###############################################################
    def update_from_csv(self, filename, animate=True):
        data = load_csv(filename)
        if not data:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        headers = data[0]
        rows = data[1:]

        # Pretty headers
        header_map = {
            "Place": "Place",
            "car_number": "Car #",
            "name": "Racer Name",
            "lane": "Lane #",
            "time_ms": "Time (ms)",
            "category": "Category",
            "heat_number": "Heat #",        
            "avg_time_ms": "Avg Time (ms)"
        }
        pretty_headers = [header_map.get(h, h) for h in headers]

        # Reset table
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(pretty_headers)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.table.setRowCount(0)

        if not animate:
            # Quiet fill
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                    self.table.setItem(r, c, item)

            return

        # Animated fill
        self.pending_rows = rows
        self.current_row_index = 0
        self.active_animations = []
        self.animation_timer.start(600)

###############################################################
# Main Dashboard Window
###############################################################
class MainDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.initialize_race_state()
        self.current_gif_movie = None
        self.upnext_gif_movie = None
        
        self.setWindowTitle("Awana Race Dashboard")
        self.engine_process = None
        self.run_timing_program()
        # Main background PNG
        palette = QPalette()
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Track last heat number to detect new heats
        self.last_heat_number = None

        # Track race engine process
        #self.engine_process = None

        #main_layout = QVBoxLayout()
        main_layout = QHBoxLayout()
        tables_layout = QVBoxLayout()
        top_row = QHBoxLayout()

        # Three stacked panels
        self.heat_panel = DataPanel("-----Last Heat Results------", "heat_bg.png")
        self.setStyleSheet("background-color: black;")

        self.leader_panel = DataPanel("-----Current Leaderboard------", "leaderboard_bg.png")
        self.upnext_panel = DataPanel("-----Up Next-----", "upnext_bg.png")

        # Right‑side GIF column
        self.gif_column = QVBoxLayout()
        self.gif_column.setContentsMargins(0, 0, 0, 0)
        self.gif_column.setSpacing(0)

        self.gif_container = QWidget()
        self.gif_container.setAttribute(Qt.WA_TranslucentBackground)
        self.gif_container.setStyleSheet("background: transparent;")

        self.gif_container.setLayout(self.gif_column)


        # ---------- TOP GIF (current category) ----------
        self.current_gif_label = QLabel()
        self.current_gif_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.current_gif_label.setFixedWidth(300)  # adjust as needed
        self.current_gif_label.setAttribute(Qt.WA_TranslucentBackground)
        self.current_gif_label.setStyleSheet("background: transparent;")

        self.gif_column.addStretch(1)
        self.gif_column.addWidget(self.current_gif_label, alignment=Qt.AlignRight | Qt.AlignVCenter)

        # Spacer to push bottom GIF down
        self.gif_column.addStretch(2)

        # ---------- BOTTOM GIF (upnext category) ----------
        self.upnext_gif_label = QLabel()
        self.upnext_gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.upnext_gif_label.setFixedWidth(300)
        self.upnext_gif_label.setAttribute(Qt.WA_TranslucentBackground)
        self.upnext_gif_label.setStyleSheet("background: transparent;")

        self.gif_column.addWidget(self.upnext_gif_label, alignment=Qt.AlignRight | Qt.AlignBottom)
        #self.gif_column.addStretch(1)
        # Add this column to your main layout
        #main_layout.addLayout(self.gif_column)
        self.load_initial_upnext_gif()


        #main_layout.addWidget(self.heat_panel, alignment=Qt.AlignLeft)
        #main_layout.addWidget(self.leader_panel, alignment=Qt.AlignLeft)
        #main_layout.addWidget(self.upnext_panel, alignment=Qt.AlignLeft)
        tables_layout.addWidget(self.heat_panel)
        tables_layout.addWidget(self.leader_panel)
        tables_layout.addWidget(self.upnext_panel)

        top_row.addLayout(tables_layout)
        top_row.addWidget(self.gif_container)

        main_layout.addLayout(top_row)


        #main_layout.addLayout(tables_layout)
        #main_layout.addLayout(self.gif_column)



        # Buttons at bottom
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)    

        #btn_run = QPushButton("Run Timing Program")
        #btn_run.setFixedSize(180, 40)
        #btn_run.clicked.connect(self.run_timing_program)

        btn_results = QPushButton("Show Final Results")
        btn_results.setFixedSize(180, 40)
        btn_results.clicked.connect(self.show_final_results)
        btn_results.setStyleSheet("""
            QPushButton {
                background-color: #222;
                color: yellow;
                font-size: 16px;
                font-family: 'Comic Sans MS';
                font-weight: bold;
                border: 2px solid yellow;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)

        btn_exit = QPushButton("Exit")
        btn_exit.setFixedSize(120, 40)
        btn_exit.clicked.connect(self.on_exit_button_clicked)
        btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #222;
                color: yellow;
                font-size: 20px;
                font-family: 'Comic Sans MS';
                font-weight: bold;
                border: 2px solid yellow;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)


        #buttons_layout.addWidget(btn_run)
        buttons_layout.addWidget(btn_results)
        buttons_layout.addWidget(btn_exit)
        buttons_layout.setAlignment(Qt.AlignRight)
        buttons_layout.setAlignment(Qt.AlignBottom)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

        # Auto-refresh every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_panels)
        self.timer.start(1000)

        # Start maximized
        self.showMaximized()
    def load_initial_upnext_gif(self):
        upnext = load_csv("upnext.csv")
        if not upnext or len(upnext) < 2:
            return

        headers = upnext[0]
        rows = upnext[1:]

        # Find category column
        try:
            cat_index = headers.index("category")
        except ValueError:
            return

        next_category = rows[0][cat_index]

        category_gifs = {
            "Cubbies": "Cubbies_horizontal_waving.gif",
            "Sparks": "Sparks_horizontal_waving.gif",
            "T&T": "TT_horizontal_waving.gif",
            "Journey": "Journey_horizontal_waving.gif",
            "Trek": "Trek_horizontal_waving.gif",
            "GroupB": "group_b_epic_race.gif"
        }

        if next_category in category_gifs:
            self.set_looping_gif(self.upnext_gif_label, category_gifs[next_category], which="upnext")

    def resizeEvent(self, event):
        bg = QPixmap("checker_bg.png")
        scaled = bg.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)

        super().resizeEvent(event)

    ###########################################################
    # Initialize race state (method to be called externally)
    ###########################################################
    def initialize_race_state(self):
        import csv, os

        # ------------------------------------------------------------
        # 1. Clear current_heat.csv
        # ------------------------------------------------------------
        with open("current_heat.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Place","Category", "heat_number", "car_number", "name", "lane"])

        # ------------------------------------------------------------
        # 2. Clear current_leaderboard.csv
        # ------------------------------------------------------------
        with open("current_leaderboard.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Place","Category", "car_number", "name", "Average Time (ms)"])

        # ------------------------------------------------------------
        # 3. Determine next heat based on heats_results.csv
        # ------------------------------------------------------------
        completed_heats = set()

        if os.path.exists("heats_results.csv"):
            with open("heats_results.csv", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    completed_heats.add(int(row["heat_number"]))

        # ------------------------------------------------------------
        # 4. Build global heat list
        # ------------------------------------------------------------
        # You already load categories in your race engine, but the UI
        # doesn't have them yet. So we reconstruct them from heats.csv.
        heats = {}
        if os.path.exists("heats.csv"):
            with open("heats.csv", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cat = row["category"]
                    heat = int(row["heat_number"])
                    lane = int(row["lane"])

                    heats.setdefault(cat, {})
                    heats[cat].setdefault(heat, {})
                    heats[cat][heat][lane] = row

        # Flatten into global list
        global_heats = []
        for cat, heat_dict in heats.items():
            for h in sorted(heat_dict.keys()):
                global_heats.append((cat, h))

        global_heats.sort(key=lambda x: x[1])

        # ------------------------------------------------------------
        # 5. Find first uncompleted heat
        # ------------------------------------------------------------
        next_heat = None
        for cat, h in global_heats:
            if h not in completed_heats:
                next_heat = (cat, h)
                break

        # ------------------------------------------------------------
        # 6. Write upnext.csv
        # ------------------------------------------------------------
        with open("upnext.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["car_number","name","lane","category", "heat_number"])

            if next_heat is None:
                return  # No heats left

            cat, h = next_heat
            heat_data = heats[cat][h]
            
            for lane in sorted(heat_data.keys()):
                row = heat_data[lane]
                writer.writerow([
                    row["car_number"],
                    row["name"],
                    row["lane"],
                    row["category"],
                    row["heat_number"]
                ])
                
    ###########################################################
    # Button Actions
    ###########################################################
    def run_timing_program(self):
        if self.engine_process is None:
            self.engine_process = subprocess.Popen([sys.executable, "AwanaTiming_Clean.py"])
    ###########################################################
    # Determine last completed and next categories
    ############################################################
    def get_last_and_next_categories(self):
        """
        Returns (last_completed_category, next_category)
        based on heats_results.csv and heats.csv.
        """

        import csv, os

        # ------------------------------------------------------------
        # Load heats.csv into a dict: heats[(heat_number)] = category
        # ------------------------------------------------------------
        heat_to_category = {}
        if os.path.exists("heats.csv"):
            with open("heats.csv", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    heat_num = int(row["heat_number"])
                    heat_to_category[heat_num] = row["category"]

        if not heat_to_category:
            return None, None

        # ------------------------------------------------------------
        # Load completed heats from heats_results.csv
        # ------------------------------------------------------------
        completed_heats = set()
        if os.path.exists("heats_results.csv"):
            with open("heats_results.csv", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    completed_heats.add(int(row["heat_number"]))

        # ------------------------------------------------------------
        # Determine last completed heat
        # ------------------------------------------------------------
        last_completed_heat = max(completed_heats) if completed_heats else None
        last_category = heat_to_category.get(last_completed_heat)

        # ------------------------------------------------------------
        # Determine next heat
        # ------------------------------------------------------------
        all_heats_sorted = sorted(heat_to_category.keys())
        next_heat = None
        for h in all_heats_sorted:
            if h not in completed_heats:
                next_heat = h
                break

        next_category = heat_to_category.get(next_heat)

        return last_category, next_category

    def set_looping_gif(self, label: QLabel, gif_path: str, which="current"):
        label.clear()
        label.setPixmap(QPixmap())  # Clear existing pixmap/movie
        label.setScaledContents(True)
        
        # Scale GroupB GIF to fit table dimensions
        if "group_b" in gif_path.lower():
            original = QPixmap(gif_path)
            scaled_width = int(original.width() * (200 / original.height()))
            label.setFixedWidth(scaled_width)
            label.setFixedHeight(200)
        
        movie = QMovie(gif_path)
        movie.setCacheMode(QMovie.CacheAll)
        movie.setSpeed(100)

        label.setMovie(movie)
        movie.start()

        # Store reference so it never gets garbage-collected
        if which == "current":
            self.current_gif_movie = movie
        else:
            self.upnext_gif_movie = movie


    ###########################################################
    # Auto-refresh panels with animation only on new heat
    ###########################################################
    def refresh_panels(self):
        heat_data = load_csv("current_heat.csv")
        upnext_data = load_csv("upnext.csv")

        if not heat_data or len(heat_data) < 2:
            self.heat_panel.update_from_csv("current_heat.csv", animate=False)
            self.leader_panel.update_from_csv("current_leaderboard.csv", animate=False)
            if upnext_data and len(upnext_data) > 1:
                self.upnext_panel.update_from_csv("upnext.csv", animate=False)
            else:
                self.upnext_panel.table.setRowCount(0)
                self.upnext_panel.table.setColumnCount(0)
            return

        headers = heat_data[0]
        rows = heat_data[1:]
        heat_number_index = headers.index("heat_number")
        current_heat_number = rows[0][heat_number_index]

        is_new_heat = current_heat_number != self.last_heat_number
        self.last_heat_number = current_heat_number

        if is_new_heat:
            self.current_gif_label.clear()
            self.upnext_gif_label.clear()

            # Start animation chain
            self.heat_panel.update_from_csv("current_heat.csv", animate=True)
            self.leader_panel.update_from_csv("current_leaderboard.csv", animate=True)
            if upnext_data and len(upnext_data) > 1:
                self.upnext_panel.update_from_csv("upnext.csv", animate=True)
            else:
                self.upnext_panel.table.setRowCount(0)
                self.upnext_panel.table.setColumnCount(0)
            last_cat, next_cat = self.get_last_and_next_categories()
            #NEED TO TEST THIS PART STILL
            #current_category = self.heat_panel.current_category  # however you store it
            #upnext_category = self.upnext_panel.current_category
            category_gifs = {
                "Cubbies" : "Cubbies_horizontal_waving.gif",
                "Sparks" : "Sparks_horizontal_waving.gif",
                "T&T" : "TT_horizontal_waving.gif",
                "Journey" : "Journey_horizontal_waving.gif",
                "Trek" : "Trek_horizontal_waving.gif",
                "GroupB" : "group_b_epic_race.gif"
            }

            if last_cat in category_gifs:
                self.set_looping_gif(self.current_gif_label, category_gifs[last_cat])

            if next_cat in category_gifs:
                self.set_looping_gif(self.upnext_gif_label, category_gifs[next_cat])

        #    self.leader_panel.table.setRowCount(0)
        #    self.upnext_panel.table.setRowCount(0)
        #else:
            # Quiet refresh
        #    self.heat_panel.update_from_csv("current_heat.csv", animate=False)
        #    self.leader_panel.update_from_csv("current_leaderboard.csv", animate=False)
        #    self.upnext_panel.update_from_csv("upnext.csv", animate=False)

    ###########################################################
    # Show final results window
    ###########################################################
    def show_final_results(self):
        dialog = FinalResultsDialog()
        dialog.exec_()

    ###########################################################
    # Exit button handler
    ###########################################################
    def on_exit_button_clicked(self):
        if self.engine_process is not None:
            self.engine_process.terminate()
            self.engine_process = None
        self.close()

    ###########################################################
    # Kill race engine on exit
    ###########################################################
    def closeEvent(self, event):
        if self.engine_process is not None:
            self.engine_process.terminate()
            self.engine_process = None
        event.accept()

###############################################################
# Run UI
###############################################################
def run_ui():
    app = QApplication(sys.argv)
    window = MainDashboard()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_ui()