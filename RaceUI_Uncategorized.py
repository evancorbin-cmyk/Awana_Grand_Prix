"""Qt dashboard for monitoring Awana Grand Prix results in real time.

This file builds the display used at race time. It reads the live CSV files created
by the timing engine and renders the heat results, leaderboard, and next heat in a
full-screen dashboard. The UI also starts the timing engine in the background and
shows a final results dialog when the event is complete.
"""
# Select the project virtual environment for local Python execution.
# This dashboard is intended to display live race data while the timing engine updates CSV files.
#Select .venv311(3.11.9) for Python environment
from ast import If
import os
import sys
import subprocess
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QScrollArea,
    QMessageBox
)
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QMovie
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QSoundEffect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def asset_path(folder, filename):
    candidate = os.path.join(BASE_DIR, folder, filename)
    if os.path.exists(candidate):
        return candidate
    return os.path.join(BASE_DIR, filename)

###############################################################
# GLOBAL UI SETTINGS
# These values define dashboard sizing, fonts, layout spacing, and table widths.
# They are centralized here so the dashboard can be tuned without hunting through
# multiple widgets and classes.
###############################################################
DEFAULT_COLUMN_WIDTH = 180
TABLE_COLUMN_WIDTHS = {
    "heat_results": {
        "Place": 110,
        "Category": 250,
        "heat_number": 180,
        "car_number": 170,
        "name": 360,
        "lane": 150,
        "time": 190,
    },
    "leaderboard": {
        "Place": 110,
        "Category": 210,
        "car_number": 170,
        "name": 360,
        "Avg Time": 190,
        "avg_time": 190,
    },
    "up_next": {
        "car_number": 200,
        "name": 360,
        "lane": 230,
        "category": 350,
        "heat_number": 180,
    },
    "final_results": {
        "Place": 110,
        "Category": 210,
        "heat_number": 130,
        "car_number": 300,
        "name": 360,
        "lane": 110,
        "time": 220,
        "time_ms": 220,
        "avg_time": 350,
        "Average Time (ms)": 350,
        "Average Time": 350,
    },
}

TABLE_DIMENSIONS = {
    "heat_results": {
        "table_width": 1600,
        "table_height": 300,
        "panel_height": 370,
        "row_height": 45,
    },
    "leaderboard": {
        "table_width": 1600,
        "table_height": 250,
        "panel_height": 320,
        "row_height": 45,
    },
    "up_next": {
        "table_width": 1600,
        "table_height": 300,
        "panel_height": 370,
        "row_height": 45,
    },
    "final_results": {
        "dialog_width": 1600,
        "dialog_height": 900,
        "table_width": 1600,
        "table_height": 270,
        "row_height": 64,
    },
}

TEXT_SIZES = {
    "panel_title": 44,
    "panel_table": 30,
    "panel_header": 36,
    "animated_row": 33,
    "final_title": 64,
    "final_table": 33,
    "final_header": 36,
    "error_label": 36,
    "button": 18,
}

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


def build_table_stylesheet(cell_font_size, header_font_size):
    return f"""
        QTableWidget {{
            background-color: black !important;
            color: yellow;
            font-size: {cell_font_size}px;
            font-family: 'Comic Sans MS';
            font-weight: bold;
        }}
        QHeaderView::section {{
            background-color: black !important;
            color: yellow;
            font-size: {header_font_size}px;
            font-family: 'Comic Sans MS';
            font-weight: bold;
            padding: 4px;
        }}
    """


def build_button_stylesheet(font_size):
    return f"""
        QPushButton {{
            background-color: #222;
            color: yellow;
            font-size: {font_size}px;
            font-family: 'Comic Sans MS';
            font-weight: bold;
            border: 2px solid yellow;
            padding: 6px;
        }}
        QPushButton:hover {{
            background-color: #444;
        }}
    """


def normalize_header_name(name):
    return name.strip().lower().replace(" ", "_").replace("#", "number")


def apply_column_widths(table, headers, width_map=None):
    header = table.horizontalHeader()
    if not headers:
        return

    if not width_map:
        header.setSectionResizeMode(QHeaderView.Stretch)
        return

    normalized_map = {
        normalize_header_name(key): value for key, value in width_map.items()
    }

    aliases = {
        "average_time_(ms)": "avg_time",
        "average_time": "avg_time",
        "average_time_ms": "avg_time",
        "time_(ms)": "time",
        "time_ms": "time",
    }

    for index, header_name in enumerate(headers):
        lookup_name = normalize_header_name(header_name)
        width = normalized_map.get(lookup_name)
        if width is None:
            alias_name = aliases.get(lookup_name)
            if alias_name is not None:
                width = normalized_map.get(alias_name)
        if width is None:
            width = DEFAULT_COLUMN_WIDTH

        header.setSectionResizeMode(index, QHeaderView.Fixed)
        table.setColumnWidth(index, width)

###############################################################
# FINAL RESULTS DIALOG
###############################################################
class FinalResultsDialog(QDialog):
    def __init__(self):
        super().__init__()
        final_sizes = TABLE_DIMENSIONS["final_results"]
        self.setWindowTitle("Final Results")
        self.setGeometry(100, 100, final_sizes["dialog_width"], final_sizes["dialog_height"])
        self.showMaximized()

        # Background
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(QPixmap(asset_path("images", "checker_bg.png"))))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("<b>Final Leaders</b>")
        title_label.setStyleSheet(
            f"font-size: {TEXT_SIZES['final_title']}px; color: yellow; font-family: 'Comic Sans MS'; font-weight: bold; background-color: black; padding: 10px;"
        )
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
            error_label.setStyleSheet(
                f"font-size: {TEXT_SIZES['error_label']}px; color: red; font-family: 'Comic Sans MS';"
            )
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
                table.setFixedWidth(final_sizes["table_width"])
                table.setFixedHeight(final_sizes["table_height"])
                table.verticalHeader().setVisible(False)
                table.verticalHeader().setDefaultSectionSize(final_sizes["row_height"])
                table.horizontalHeader().setDefaultAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                table.setStyleSheet(
                    build_table_stylesheet(
                        TEXT_SIZES["final_table"],
                        TEXT_SIZES["final_header"],
                    )
                )

                # Populate table
                pretty_headers = [h if h in ["Place", "Car #"] else h.replace("_", " ").title().replace("Ms)", "ms)") for h in headers]
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(pretty_headers)
                apply_column_widths(table, headers, TABLE_COLUMN_WIDTHS["final_results"])
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
                    gif_label.setFixedWidth(220)
                    gif_label.setFixedHeight(138)
                    gif_label.setScaledContents(True)
                    
                    # Create movie and get its dimensions
                    movie = QMovie(asset_path("images", category_gifs[category]))
                    movie.setCacheMode(QMovie.CacheAll)
                    movie.setSpeed(100)
                    
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
        close_btn.setStyleSheet(build_button_stylesheet(TEXT_SIZES["button"]))
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def resizeEvent(self, event):
        bg = QPixmap(asset_path("images", "checker_bg.png"))
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

    def __init__(
        self,
        title,
        bg_image,
        fixed_height=340,
        column_widths=None,
        table_width=1600,
        table_height=200,
        row_height=70,
        title_font_size=None,
        table_font_size=None,
        header_font_size=None,
        animated_row_font_size=None,
        cell_alignment=Qt.AlignHCenter | Qt.AlignVCenter,
        header_alignment=Qt.AlignHCenter | Qt.AlignVCenter,
    ):
        super().__init__()
        self.column_widths = column_widths or {}
        self.animated_row_font_size = animated_row_font_size or TEXT_SIZES["animated_row"]
        self.cell_alignment = cell_alignment
        self.header_alignment = header_alignment

        title_font_size = title_font_size or TEXT_SIZES["panel_title"]
        table_font_size = table_font_size or TEXT_SIZES["panel_table"]
        header_font_size = header_font_size or TEXT_SIZES["panel_header"]

        # Background
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(QPixmap(asset_path("images", bg_image))))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter)

        # Title
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setStyleSheet(
            f"font-size: {title_font_size}px; color: yellow; font-family: 'Comic Sans MS';"
        )
        layout.addWidget(title_label, alignment=Qt.AlignLeft)

        # Table
        self.table = QTableWidget()
        self.table.setFixedWidth(table_width)
        self.table.setFixedHeight(table_height)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(row_height)
        self.table.horizontalHeader().setDefaultAlignment(self.header_alignment)
        self.table.setStyleSheet(build_table_stylesheet(table_font_size, header_font_size))

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
        self.swoosh.setSource(QUrl.fromLocalFile(asset_path("audio", "swoosh.wav")))
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
        container_layout.setSpacing(0)

        for c, value in enumerate(row_data):
            lbl = QLabel(value)
            lbl.setStyleSheet(
                f"color: yellow; font-size: {self.animated_row_font_size}px; font-family: 'Comic Sans MS';"
            )
            lbl.setAlignment(self.cell_alignment)
            # Match each animated label to the real table column width
            lbl.setFixedWidth(self.table.columnWidth(c))
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
            "time_ms": "Time",
            "category": "Category",
            "heat_number": "Heat #",        
            "avg_time_ms": "Avg Time"
        }
        pretty_headers = [header_map.get(h, h) for h in headers]

        # Reset table
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(pretty_headers)
        self.table.horizontalHeader().setDefaultAlignment(self.header_alignment)
        apply_column_widths(self.table, headers, self.column_widths)
        self.table.setRowCount(0)

        if not animate:
            # Quiet fill
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(self.cell_alignment)
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

        # Animated checker background behind the entire dashboard.
        self.background_label = QLabel(self)
        self.background_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.background_label.setStyleSheet("background: transparent;")
        self.background_label.lower()
        self.background_movie = QMovie(asset_path("images", "checker_bg_waving.gif"))
        self.background_movie.setCacheMode(QMovie.CacheAll)
        self.background_movie.setSpeed(100)
        self.background_label.setMovie(self.background_movie)
        self.background_movie.start()

        # Track last heat number to detect new heats
        self.last_heat_number = None

        # Track race engine process
        #self.engine_process = None

        #main_layout = QVBoxLayout()
        main_layout = QHBoxLayout()
        tables_layout = QVBoxLayout()
        top_row = QHBoxLayout()

        # Three stacked panels
        heat_sizes = TABLE_DIMENSIONS["heat_results"]
        leader_sizes = TABLE_DIMENSIONS["leaderboard"]
        upnext_sizes = TABLE_DIMENSIONS["up_next"]

        self.heat_panel = DataPanel(
            "_______________________Heat Results________________________",
            "heat_bg.png",
            fixed_height=heat_sizes["panel_height"],
            column_widths=TABLE_COLUMN_WIDTHS["heat_results"],
            table_width=heat_sizes["table_width"],
            table_height=heat_sizes["table_height"],
            row_height=heat_sizes["row_height"],
        )
        self.setStyleSheet("background-color: black;")

        self.leader_panel = DataPanel(
            "_____________________Current Leaderboard____________________",
            "leaderboard_bg.png",
            fixed_height=leader_sizes["panel_height"],
            column_widths=TABLE_COLUMN_WIDTHS["leaderboard"],
            table_width=leader_sizes["table_width"],
            table_height=leader_sizes["table_height"],
            row_height=leader_sizes["row_height"],
        )
        self.upnext_panel = DataPanel(
            "__________________________Up Next_________________________",
            "upnext_bg.png",
            fixed_height=upnext_sizes["panel_height"],
            column_widths=TABLE_COLUMN_WIDTHS["up_next"],
            table_width=upnext_sizes["table_width"],
            table_height=upnext_sizes["table_height"],
            row_height=upnext_sizes["row_height"],
            cell_alignment=Qt.AlignHCenter | Qt.AlignVCenter,
            header_alignment=Qt.AlignHCenter | Qt.AlignVCenter,
        )

        tables_layout.addWidget(self.heat_panel)
        tables_layout.addWidget(self.leader_panel)
        tables_layout.addWidget(self.upnext_panel)

        top_row.addLayout(tables_layout)

        main_layout.addLayout(top_row)


        # Buttons at bottom
        buttons_layout = QVBoxLayout()
        buttons_layout.addStretch(1)    

        #btn_run = QPushButton("Run Timing Program")
        #btn_run.setFixedSize(180, 40)
        #btn_run.clicked.connect(self.run_timing_program)

        btn_current = QPushButton("Current")
        btn_current.setFixedSize(80, 40)
        btn_current.clicked.connect(self.run_current_animations)
        btn_current.setStyleSheet(build_button_stylesheet(TEXT_SIZES["button"]))

        btn_results = QPushButton("Results")
        btn_results.setFixedSize(80, 40)
        btn_results.clicked.connect(self.show_final_results)
        btn_results.setStyleSheet(build_button_stylesheet(TEXT_SIZES["button"]))

        btn_exit = QPushButton("Exit")
        btn_exit.setFixedSize(80, 40)
        btn_exit.clicked.connect(self.on_exit_button_clicked)
        btn_exit.setStyleSheet(build_button_stylesheet(TEXT_SIZES["button"]))


        #buttons_layout.addWidget(btn_run)
        buttons_layout.addWidget(btn_current)
        buttons_layout.addWidget(btn_results)
        buttons_layout.addWidget(btn_exit)
        buttons_layout.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

        # Auto-refresh every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_panels)
        self.timer.start(1000)

        # Start maximized
        self.showMaximized()
        self.background_label.setGeometry(self.rect())
        self.background_movie.setScaledSize(self.size())

    def run_current_animations(self):
        try:
            import AwanaTiming_Uncategorized
            if hasattr(AwanaTiming_Uncategorized, "simulate_heat_finish"):
                AwanaTiming_Uncategorized.simulate_heat_finish()
        except Exception as exc:
            print(f"Current simulation failed: {exc}")

        heat_data = load_csv("current_heat.csv")
        upnext_data = load_csv("upnext.csv")
        if not heat_data or len(heat_data) < 2:
            return

        self.heat_panel.update_from_csv("current_heat.csv", animate=True)
        self.leader_panel.update_from_csv("current_leaderboard.csv", animate=True)
        if upnext_data and len(upnext_data) > 1:
            self.upnext_panel.update_from_csv("upnext.csv", animate=True)
        else:
            self.upnext_panel.table.setRowCount(0)
            self.upnext_panel.table.setColumnCount(0)

        self.last_heat_number = None

    def resizeEvent(self, event):
        if hasattr(self, "background_label"):
            self.background_label.setGeometry(self.rect())
        if hasattr(self, "background_movie"):
            self.background_movie.setScaledSize(self.size())

        super().resizeEvent(event)

    ###########################################################
    # Initialize race state (method to be called externally)
    ###########################################################
    def initialize_race_state(self):
        import csv, os

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # 1. Clear current_heat.csv
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        with open("current_heat.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Place", "car_number", "name", "lane",
                "time_ms", "category", "heat_number"
            ])

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # 2. Clear current_leaderboard.csv
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        with open("current_leaderboard.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Place","Category", "car_number", "name", "Avg Time"])

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # 3. Determine next heat based on heats_results.csv
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        completed_heats = set()

        if os.path.exists("heats_results.csv"):
            with open("heats_results.csv", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    completed_heats.add(int(row["heat_number"]))

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # 4. Build global heat list
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
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

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # 5. Find first uncompleted heat
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        next_heat = None
        for cat, h in global_heats:
            if h not in completed_heats:
                next_heat = (cat, h)
                break

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # 6. Write upnext.csv
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
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
            self.engine_process = subprocess.Popen([sys.executable, "AwanaTiming_Uncategorized.py"])

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)

    ###########################################################
    # Determine last completed and next categories
    ############################################################
    def get_last_and_next_categories(self):
        """
        Returns (last_completed_category, next_category)
        based on heats_results.csv and heats.csv.
        """

        import csv, os

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # Load heats.csv into a dict: heats[(heat_number)] = category
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        heat_to_category = {}
        if os.path.exists("heats.csv"):
            with open("heats.csv", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    heat_num = int(row["heat_number"])
                    heat_to_category[heat_num] = row["category"]

        if not heat_to_category:
            return None, None

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # Load completed heats from heats_results.csv
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        completed_heats = set()
        if os.path.exists("heats_results.csv"):
            with open("heats_results.csv", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    completed_heats.add(int(row["heat_number"]))

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # Determine last completed heat
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        last_completed_heat = max(completed_heats) if completed_heats else None
        last_category = heat_to_category.get(last_completed_heat)

        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        # Determine next heat
        # ________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
        all_heats_sorted = sorted(heat_to_category.keys())
        next_heat = None
        for h in all_heats_sorted:
            if h not in completed_heats:
                next_heat = h
                break

        next_category = heat_to_category.get(next_heat)

        return last_category, next_category

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
            # Start animation chain
            self.heat_panel.update_from_csv("current_heat.csv", animate=True)
            self.leader_panel.update_from_csv("current_leaderboard.csv", animate=True)
            if upnext_data and len(upnext_data) > 1:
                self.upnext_panel.update_from_csv("upnext.csv", animate=True)
            else:
                self.upnext_panel.table.setRowCount(0)
                self.upnext_panel.table.setColumnCount(0)

        #    self.leader_panel.table.setRowCount(0)
        #    self.upnext_panel.table.setRowCount(0)
        #else:
            # Quiet refresh
        #    self.heat_panel.update_from_csv("current_heat.csv", animate=False)
        #    self.leader_panel.update_from_csv("current_leaderboard.csv", animate=False)
        #    self.upnext_panel.update_from_csv("upnext.csv", animate=False)

    ###########################################################
    # Generate current final results before opening the dialog
    ###########################################################
    def generate_final_results_csv(self):
        category_order = ["Cubbies", "Sparks", "T&T", "Trek", "Journey", "GroupB"]
        categories = {}

        if os.path.exists("heats.csv"):
            with open("heats.csv", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category = row["category"]
                    categories.setdefault(category, [])
                    categories[category].append(row)

        final_rows = [["Place", "Category", "Car Number", "Name", "Average Time (ms)"]]

        for category in category_order:
            if category not in categories:
                continue

            results_by_car = {}
            names = {}

            if os.path.exists("heats_results.csv"):
                with open("heats_results.csv", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("category") == category:
                            car = row["car_number"]
                            names[car] = row["name"]
                            results_by_car.setdefault(car, []).append(float(row["time_ms"]))

            leaders = []
            for car, times in results_by_car.items():
                avg = sum(times) / len(times)
                leaders.append((car, names.get(car, ""), avg))

            leaders.sort(key=lambda x: x[2])
            for place, (car, name, avg) in enumerate(leaders[:3], start=1):
                final_rows.append([place, category, car, name, str(round(avg))])

        with open("final_leaders.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(final_rows)

    ###########################################################
    # Show final results window
    ###########################################################
    def show_final_results(self):
        self.generate_final_results_csv()
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