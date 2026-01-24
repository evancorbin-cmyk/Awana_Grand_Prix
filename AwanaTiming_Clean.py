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

import csv
import os
import serial
import time
import sys
from collections import defaultdict
import pygame

pygame.mixer.init()

###############################################################
# USER SETTINGS
###############################################################
COMM_PORT = "COM4"
BAUD_RATE = 9600

HEATS_FILE = "heats.csv"
CSV_RESULTS_FILE = "heats_results.csv"

# Sounds to keep
RACERESET_SOUND = "GetReady.mp3"
RACEFINISHED_SOUND = "RaceFinished.mp3"
MENU_SOUND = "Menu.mp3"
RACESTARTED_SOUND = "RaceStarted.mp3"


###############################################################
# INITIALIZE RACE STATE
# Clears current CSVs and writes the first UpNext heat
###############################################################
def initialize_race_state(categories):
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
            "name", "Average Time (ms)"
        ])

    # Determine completed heats
    completed_heats = set()
    if os.path.exists(CSV_RESULTS_FILE):
        with open(CSV_RESULTS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                completed_heats.add(int(row["heat_number"]))

    # Build global ordered heat list
    global_heats = []
    for cat, heats in categories.items():
        for h in sorted(heats.keys()):
            global_heats.append((cat, h))

    global_heats.sort(key=lambda x: x[1])

    # Find first uncompleted heat
    next_heat = None
    for cat, h in global_heats:
        if h not in completed_heats:
            next_heat = (cat, h)
            break

    # Write upnext.csv
    with open("upnext.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["car_number", "name", "lane", "category", "heat_number"])

        if next_heat is None:
            return  # No heats left

        cat, h = next_heat
        heat_data = categories[cat][h]

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
# COMPUTE LEADERBOARD FOR A CATEGORY
###############################################################
def compute_leaderboard(category):
    results = defaultdict(list)
    names = {}

    try:
        with open(CSV_RESULTS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["category"] == category:
                    car = row["car_number"]
                    time_ms = float(row["time_ms"])
                    results[car].append(time_ms)
                    names[car] = row["name"]
    except FileNotFoundError:
        return []

    averages = []
    for car, times in results.items():
        avg = sum(times) / len(times)
        averages.append((car, names[car], avg))

    averages.sort(key=lambda x: x[2])
    return averages[:3]


###############################################################
# WRITE LEADERBOARD TO current_leaderboard.csv
###############################################################
def write_leaderboard_csv(category):
    leaders = compute_leaderboard(category)

    with open("current_leaderboard.csv", "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "Place", "car_number", "name",
            "avg_time_ms", "category"
        ])

        for idx, (car, name, avg) in enumerate(leaders, start=1):
            writer.writerow([
                idx,
                car,
                name,
                str(round(avg)),
                category
            ])


###############################################################
# WRITE NEXT HEAT TO upnext.csv
###############################################################
def write_upnext_csv(categories, current_category, current_heat):
    global_heats = []
    for cat, heats in categories.items():
        for h in sorted(heats.keys()):
            global_heats.append((cat, h))

    global_heats.sort(key=lambda x: x[1])

    try:
        idx = global_heats.index((current_category, current_heat))
    except ValueError:
        return

    # Last heat → clear file
    if idx + 1 >= len(global_heats):
        with open("upnext.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["car_number", "name", "lane", "category", "heat_number"])
        return

    next_cat, next_heat = global_heats[idx + 1]
    next_heat_data = categories[next_cat][next_heat]

    with open("upnext.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["car_number", "name", "lane", "category", "heat_number"])

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
def monitor_serial(port, baud, timeout=0.1):
    ser = serial.Serial(port, baud, timeout=timeout)
    print(f"Listening on {port} at {baud} baud...")

    pygame.mixer.music.load(MENU_SOUND)
    pygame.mixer.music.play(loops=-1, fade_ms=2000)

    while True:
        print("\n=== Race System Reset — Loading Heats ===")

        categories = load_heats(HEATS_FILE)
        category_list = list(categories.keys())
        initialize_race_state(categories)

        last_heat = get_last_completed_heat()
        print(f"Last completed heat: {last_heat}")

        all_heats = []
        for cat in category_list:
            for h in categories[cat].keys():
                all_heats.append((cat, h))

        all_heats.sort(key=lambda x: x[1])
        remaining_heats = [(cat, h) for (cat, h) in all_heats if h > last_heat]

        if not remaining_heats:
            print("All heats completed — restarting system.")
            time.sleep(2)
            continue  # Loop forever

        # Process heats
        for current_category, current_heat in remaining_heats:
            heats = categories[current_category]
            lanes_expected = sorted(heats[current_heat].keys())

            print(f"\n--- Ready for Heat {current_heat} ({current_category}) ---")
            pygame.mixer.music.load(MENU_SOUND)
            pygame.mixer.music.play(loops=-1, fade_ms=2000)

            lane_results = {}
            heat_active = False

            # Wait for Race Started
            while True:
                line = ser.readline().decode().strip()
                if line:
                    print("Arduino:", line)

                if line == "Race Started":
                    print(f"--- Heat {current_heat} Started ---")
                    pygame.mixer.music.load(RACESTARTED_SOUND)
                    pygame.mixer.music.play()
                    time.sleep(2)
                    heat_active = True
                    break

                if line == "Race Reset":
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
                lane_record = dict(heats[current_heat][lane])
                lane_record["time_ms"] = lane_results[lane]
                saved_heat[lane] = lane_record

            append_heat_results_csv(saved_heat)
            write_current_heat_csv(saved_heat)
            write_leaderboard_csv(current_category)
            write_upnext_csv(categories, current_category, current_heat)


###############################################################
# RUN SYSTEM
###############################################################
if __name__ == "__main__":
    monitor_serial(COMM_PORT, BAUD_RATE)