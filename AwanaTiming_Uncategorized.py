###############################################################
# Awana Grand Prix Race Control System (Cleaned Version)
# -------------------------------------------------------------
# This version:
#   • Removes keyboard listener and redo logic
#   • Removes random finish sounds
#   • Keeps only essential race sounds (Menu, RaceStarted,
#       RaceFinished, GetReady)
#   • Auto‑advances based on heats_results.csv
#   • Waits indefinitely for all lanes to finish (no timeout)
#   • Validates lane numbers
#   • Loops forever when all heats are done
###############################################################

"""Awana Grand Prix timing engine.

This script is the race-control backend for the event. It reads the heat schedule,
waits for serial messages from the Arduino timing gate, validates and stores lane
results, updates live CSV files for the dashboard, and advances through each heat
until all heats have been completed.

The overall workflow is:
1. Load the scheduled heats from heats.csv.
2. Initialize the current race-state CSV files.
3. Open the serial connection to the Arduino timing gate.
4. Wait for the "Race Started" signal for the next heat.
5. Record each lane's finish time as the Arduino reports it.
6. Save the finished heat results and refresh the leaderboard/up-next files.
7. Continue until every heat is complete, then generate the final report.
"""

import csv
import os
import serial
from serial.tools import list_ports
import time
import sys
from collections import defaultdict
import pygame

pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")


def audio_path(filename):
    return os.path.join(AUDIO_DIR, filename)

###############################################################
# CONFIGURATION / SETTINGS
# These values are read once at startup and control how the race engine
# connects to hardware, which files it uses, and which sounds it plays.
###############################################################
# Serial settings: the Arduino should be connected to this COM port at this baud rate.
COMM_PORT = os.getenv("AWANA_COM_PORT", "COM4")
BAUD_RATE = int(os.getenv("AWANA_BAUD_RATE", "9600"))

# CSV file names used by the race engine to track the schedule, current results,
# completed heats, and the next race that should run.
HEATS_FILE = "heats.csv"
CSV_RESULTS_FILE = "heats_results.csv"
CURRENT_HEAT_FILE = "current_heat.csv"
CURRENT_LEADERBOARD_FILE = "current_leaderboard.csv"
UPNEXT_FILE = "upnext.csv"
FINAL_LEADERS_FILE = "final_leaders.csv"
EXCLUDED_OVERALL_CATEGORIES = {"GroupB"}

# Sound files used for race-state notifications to keep the event audio cues clear.
RACERESET_SOUND = audio_path("RaceReset.mp3")
RACEFINISHED_SOUND = audio_path("RaceFinished.mp3")
MENU_SOUND = audio_path("Menu.mp3")
RACESTARTED_SOUND = audio_path("RaceStarted.mp3")


###############################################################
# INITIALIZE RACE STATE
# Clears current CSVs and writes the first UpNext heat
###############################################################
def initialize_race_state(heats_by_number):
    # Clear current_heat.csv
    with open("current_heat.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Place", "car_number", "name", "lane",
            "time_ms", "category", "heat_number"
        ])

    # Clear current_leaderboard.csv
    with open("current_leaderboard.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Place", "category", "car_number",
            "name", " ", "Average Time (ms)","  "
        ])

    # Determine completed heats
    completed_heats = set()
    if os.path.exists(CSV_RESULTS_FILE):
        with open(CSV_RESULTS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                completed_heats.add(int(row["heat_number"]))

    next_heat = get_next_heat(heats_by_number, completed_heats=completed_heats)

    # Write upnext.csv
    with open("upnext.csv", "w", newline="") as f:
        if next_heat is None:
            return  # No heats left; leave the file blank

        writer = csv.writer(f)
        writer.writerow(["car_number", "name", "lane", "category", "heat_number"])

        heat_number = next_heat
        heat_data = heats_by_number[heat_number]

        for lane in sorted(heat_data.keys()):
            row = heat_data[lane]
            writer.writerow([
                row["car_number"],
                row["name"],
                row["lane"],
                row["category"],
                row["heat_number"]
            ])


###############################################################
# LOAD HEATS FROM heats.csv
###############################################################
def load_heats(filename):
    categories = defaultdict(lambda: defaultdict(dict))

    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row["category"]
            heat = int(row["heat_number"])
            lane = int(row["lane"])

            categories[category][heat][lane] = {
                "category": category,
                "heat_number": heat,
                "car_number": row["car_number"],
                "name": row["name"],
                "lane": lane,
                "time_ms": None
            }

    return categories


def load_heats_by_number(filename):
    heats_by_number = defaultdict(dict)

    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            heat_number = int(row["heat_number"])
            lane = int(row["lane"])

            heats_by_number[heat_number][lane] = {
                "category": row["category"],
                "heat_number": heat_number,
                "car_number": row["car_number"],
                "name": row["name"],
                "lane": lane,
                "time_ms": None,
            }

    return heats_by_number


def get_heat_roster_from_schedule(heat_number):
    """Returns the scheduled racers for a given heat directly from heats.csv."""
    if not os.path.exists(HEATS_FILE):
        return {}

    heat_roster = {}
    with open(HEATS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["heat_number"]) != heat_number:
                continue
            lane = int(row["lane"])
            heat_roster[lane] = {
                "category": row["category"],
                "heat_number": heat_number,
                "car_number": row["car_number"],
                "name": row["name"],
                "lane": lane,
                "time_ms": None,
            }

    return heat_roster


def get_ordered_heats(heats_by_number):
    return sorted(heats_by_number.keys())


def get_next_heat(heats_by_number, current_heat=None, completed_heats=None):
    ordered_heats = get_ordered_heats(heats_by_number)

    if not ordered_heats:
        return None

    if current_heat is not None:
        try:
            current_index = ordered_heats.index(current_heat)
        except ValueError:
            current_index = None

        if current_index is not None:
            if current_index + 1 < len(ordered_heats):
                return ordered_heats[current_index + 1]
            return None

    if completed_heats is not None:
        for heat_number in ordered_heats:
            if heat_number not in completed_heats:
                return heat_number
        return None

    return ordered_heats[0]


###############################################################
# GET LAST COMPLETED HEAT
###############################################################
def get_last_completed_heat():
    try:
        with open(CSV_RESULTS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            heats = [int(row["heat_number"]) for row in reader]
            return max(heats) if heats else 0
    except FileNotFoundError:
        return 0


###############################################################
# APPEND HEAT RESULTS TO heats_results.csv
###############################################################
def append_heat_results_csv(heat_data):
    if not heat_data:
        raise ValueError("No heat results were provided to append.")

    # The race format is fixed to 4 lanes; treat partial heats as invalid input.
    if len(heat_data) != 4:
        raise ValueError(
            f"Expected exactly 4 lane results for a heat, but received {len(heat_data)}."
        )

    file_exists = os.path.exists(CSV_RESULTS_FILE)

    with open(CSV_RESULTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "category", "heat_number", "car_number",
                "name", "lane", "time_ms"
            ])

        for lane in sorted(heat_data.keys()):
            row = heat_data[lane]
            writer.writerow([
                row["category"],
                row["heat_number"],
                row["car_number"],
                row["name"],
                row["lane"],
                row["time_ms"]
            ])

    print(f"Saved heat {list(heat_data.values())[0]['heat_number']} to {CSV_RESULTS_FILE}")


###############################################################
# WRITE CURRENT HEAT RESULTS TO current_heat.csv
###############################################################
def write_current_heat_csv(heat_data):
    with open("current_heat.csv", "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "Place", "car_number", "name", "lane",
            "time_ms", "category", "heat_number"
        ])

        # Fastest times first so place numbers match race results.
        sorted_rows = sorted(
            heat_data.values(),
            key=lambda r: r["time_ms"]
        )

        for idx, row in enumerate(sorted_rows, start=1):
            writer.writerow([
                idx,
                row["car_number"],
                row["name"],
                row["lane"],
                row["time_ms"],
                row["category"],
                row["heat_number"]
            ])


###############################################################
# COMPUTE OVERALL LEADERBOARD ACROSS ALL CATEGORIES
###############################################################
def compute_overall_leaderboard():
    results = defaultdict(list)
    names = {}
    categories = {}

    try:
        with open(CSV_RESULTS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["category"] in EXCLUDED_OVERALL_CATEGORIES:
                    continue
                car = row["car_number"]
                time_ms = float(row["time_ms"])
                results[car].append(time_ms)
                names[car] = row["name"]
                categories[car] = row["category"]
    except FileNotFoundError:
        return []

    averages = []
    for car, times in results.items():
        avg = sum(times) / len(times)
        averages.append((car, names[car], categories[car], avg))

    averages.sort(key=lambda x: x[3])
    return averages[:3]


###############################################################
# WRITE LEADERBOARD TO current_leaderboard.csv
###############################################################
def write_leaderboard_csv():
    leaders = compute_overall_leaderboard()

    with open("current_leaderboard.csv", "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "Place", "category", "car_number", "name", "lane", "time_ms"
        ])

        for idx, (car, name, category, avg) in enumerate(leaders, start=1):
            writer.writerow([
                idx,
                category,
                car,
                name,
                "",
                str(round(avg))
            ])


###############################################################
# WRITE LAST COMPLETED HEAT TO current_heat.csv
###############################################################
def write_last_heat_to_current(last_heat_number):
    """Builds the current heat display from the scheduled heat roster in heats.csv."""
    heat_roster = get_heat_roster_from_schedule(last_heat_number)
    if not heat_roster:
        return

    last_heat_data = []

    try:
        with open(CSV_RESULTS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row["heat_number"]) == last_heat_number:
                    last_heat_data.append(row)
    except FileNotFoundError:
        return

    if not last_heat_data:
        return

    # Re-key by lane so we can align results to the scheduled lane order first.
    result_by_lane = {int(row["lane"]): row for row in last_heat_data}
    ordered_rows = []
    for lane in sorted(heat_roster.keys()):
        row = result_by_lane.get(lane)
        if row is not None:
            ordered_rows.append(row)

    ordered_rows.sort(key=lambda x: int(x["time_ms"]))

    with open("current_heat.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Place", "car_number", "name", "lane",
            "time_ms", "category", "heat_number"
        ])

        for idx, row in enumerate(ordered_rows, start=1):
            writer.writerow([
                idx,
                row["car_number"],
                row["name"],
                row["lane"],
                row["time_ms"],
                row["category"],
                row["heat_number"]
            ])

    print(f"Updated current_heat.csv with results from Heat {last_heat_number}")


###############################################################
# GENERATE FINAL TOP 3 LEADERS ACROSS ALL CATEGORIES
###############################################################
def generate_final_leaders_csv(categories):
    """
    Creates a final CSV file with top 3 leaders in each category.
    File is saved as 'final_leaders.csv'
    """
    try:
        with open("final_leaders.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Place", "Category", "Car Number", "Name", "Average Time (ms)"])

            # Define category order
            category_order = ["Cubbies", "Sparks", "T&T", "Trek", "Journey"]
            
            for category in category_order:
                if category in categories:
                    leaders = [
                        (car, name, category_name, avg)
                        for car, name, category_name, avg in compute_overall_leaderboard()
                        if category_name == category
                    ][:3]
                    for place, (car, name, category_name, avg) in enumerate(leaders, start=1):
                        writer.writerow([
                            place,
                            category_name,
                            car,
                            name,
                            str(round(avg))
                        ])

        print(f"Final leaders saved to final_leaders.csv")
    except Exception as e:
        print(f"Error generating final leaders: {e}")


###############################################################
# SIMULATE A COMPLETED HEAT FOR UI TESTING / DEMO MODE
###############################################################
def simulate_heat_finish():
    """Replays the most recent completed heat in the UI without creating a new race result."""
    if not os.path.exists(CSV_RESULTS_FILE):
        print("No heats_results.csv found; nothing to replay.")
        return

    with open(CSV_RESULTS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No completed heat rows to replay.")
        return

    last_heat = max(int(row["heat_number"]) for row in rows)
    last_rows = [row for row in rows if int(row["heat_number"]) == last_heat]
    if not last_rows:
        return

    heat_roster = get_heat_roster_from_schedule(last_heat)
    saved_heat = {}
    for row in last_rows:
        lane_number = int(row["lane"])
        if lane_number not in heat_roster:
            continue
        saved_heat[lane_number] = {
            "category": row["category"],
            "heat_number": int(row["heat_number"]),
            "car_number": row["car_number"],
            "name": row["name"],
            "lane": lane_number,
            "time_ms": int(row["time_ms"]),
        }

    if not saved_heat and heat_roster:
        saved_heat = heat_roster.copy()

    write_current_heat_csv(saved_heat)
    write_leaderboard_csv()

    print(f"Replayed completed heat {last_heat} for UI animation.")


###############################################################
# WRITE NEXT HEAT TO upnext.csv
###############################################################
def write_upnext_csv(heats_by_number, current_heat):
    next_heat = get_next_heat(heats_by_number, current_heat)

    # Last heat → clear file
    if next_heat is None:
        with open("upnext.csv", "w", newline="") as f:
            pass
        return

    next_heat_data = heats_by_number[next_heat]

    with open("upnext.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["car_number", "name", "lane", "category", "heat_number"])

        # Keep lanes sorted for predictable display and marshal order at the line.
        for lane in sorted(next_heat_data.keys()):
            row = next_heat_data[lane]
            writer.writerow([
                row["car_number"],
                row["name"],
                row["lane"],
                row["category"],
                row["heat_number"]
            ])


###############################################################
# MAIN SERIAL MONITORING LOOP
###############################################################
def open_serial_connection(preferred_port, baud, timeout=0.1):
    """
    Opens a serial connection, trying the preferred port first and then
    falling back to the first available port when possible.
    """
    available_ports = [p.device for p in list_ports.comports()]

    try:
        return serial.Serial(preferred_port, baud, timeout=timeout)
    except serial.SerialException as exc:
        print(f"WARNING: Could not open preferred port {preferred_port}: {exc}")

    if not available_ports:
        raise RuntimeError(
            "No serial ports were detected. Check USB cable/driver and Arduino power."
        )

    for candidate in available_ports:
        if candidate == preferred_port:
            continue
        try:
            print(f"Trying fallback serial port: {candidate}")
            return serial.Serial(candidate, baud, timeout=timeout)
        except serial.SerialException:
            continue

    raise RuntimeError(
        "Unable to open any serial port. Available ports: "
        + ", ".join(available_ports)
        + ". Close other apps using the port (Arduino IDE Serial Monitor, etc.)."
    )


def monitor_serial(port, baud, timeout=0.1):
    ser = open_serial_connection(port, baud, timeout=timeout)
    print(f"Listening on {ser.port} at {baud} baud...")

    pygame.mixer.music.load(MENU_SOUND)
    pygame.mixer.music.play(loops=-1, fade_ms=2000)

    while True:
        print("\n=== Race System Reset — Loading Heats ===")

        categories = load_heats(HEATS_FILE)
        heats_by_number = load_heats_by_number(HEATS_FILE)
        initialize_race_state(heats_by_number)

        last_heat = get_last_completed_heat()
        print(f"Last completed heat: {last_heat}")

        all_heats = sorted(heats_by_number.keys())
        # Resume from disk state: only run heats beyond the highest persisted heat number.
        remaining_heats = [heat_number for heat_number in all_heats if heat_number > last_heat]

#What to do when all heats are done
        if not remaining_heats:
            print("All heats completed — generating final leaders report.")
            # Write last heat results to current_heat.csv
            write_last_heat_to_current(last_heat)
            # Update overall leaderboard across all racers while showing category
            write_leaderboard_csv()
            generate_final_leaders_csv(categories)
            print("All heats are done!")
            pygame.mixer.music.load(MENU_SOUND)
            pygame.mixer.music.play(loops=-1, fade_ms=2000)
            while True:
                time.sleep(1)

        # Process heats
        for current_heat in remaining_heats:
            heat_rows = heats_by_number[current_heat]
            lanes_expected = sorted(heat_rows.keys())
            
            print(f"\n--- Ready for Heat {current_heat} ---")
            pygame.mixer.music.load(MENU_SOUND)
            pygame.mixer.music.play(loops=-1, fade_ms=2000)

            lane_results = {}
            heat_active = False

            # Wait for Race Started
            while True:
                line = ser.readline().decode().strip()
                if line:
                    print("Arduino:", line)

                # Do not start recording times until the gate controller starts the race.
                if line == "Race Started":
                    print(f"--- Heat {current_heat} Started ---")
                    pygame.mixer.music.load(RACESTARTED_SOUND)
                    pygame.mixer.music.play()
                    time.sleep(2)
                    heat_active = True
                    break

                if line == "Race Reset":
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(RACERESET_SOUND)
                    pygame.mixer.music.play()
                    time.sleep(2)

            # Collect lane times
            while heat_active:
                line = ser.readline().decode().strip()
                if line:
                    print("Arduino:", line)

                if line.startswith("Lane"):
                    try:
                        # Expected serial format: "Lane <n>: <time_ms> ms"
                        parts = line.split()
                        lane = int(parts[0].replace("Lane", "").replace(":", ""))
                        time_ms = int(parts[2])

                        if lane not in lanes_expected:
                            print(f"WARNING: Lane {lane} not expected for this heat.")
                        else:
                            lane_results[lane] = time_ms
                            print(f"Recorded Lane {lane}: {time_ms} ms")

                    except:
                        print("Malformed lane time:", line)
                
                if len(lane_results) == len(lanes_expected):
                    print(f"--- Heat {current_heat} Complete ---")
                    pygame.mixer.music.load(RACEFINISHED_SOUND)
                    pygame.mixer.music.play()
                    time.sleep(5)
                    break

            # Build saved heat
            saved_heat = {}
            for lane in lanes_expected:
                lane_record = dict(heat_rows[lane])
                lane_record["time_ms"] = lane_results[lane]
                saved_heat[lane] = lane_record

            append_heat_results_csv(saved_heat)
            write_current_heat_csv(saved_heat)
            write_leaderboard_csv()
            write_upnext_csv(heats_by_number, current_heat)


###############################################################
# RUN SYSTEM
###############################################################
if __name__ == "__main__":
    monitor_serial(COMM_PORT, BAUD_RATE)