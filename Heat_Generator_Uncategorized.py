"""Generate the heat schedule for the Awana Grand Prix event.

This utility randomizes all racers across the non-GroupB categories together,
then keeps GroupB in its own category block at the end of the schedule. The goal
is to ensure that each racer appears in a different lane across successive heats so
that the race remains fair and evenly distributed while preserving GroupB as a
separate category section.
"""

import csv
import random
from collections import defaultdict

###############################################################
# SCHEDULE GENERATION SETTINGS
# These values control where the source data is loaded from and where the output
# heat sheet is written.
###############################################################
INPUT_FILE = "Racer_List.csv"
OUTPUT_FILE = "heats.csv"
LANES_PER_HEAT = 4


def load_racers(filename):
    racers = []
    with open(filename, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            racers.append({
                "car_number": row["Car_Number"],
                "name": row["Name"],
                "category": row["Category"]
            })
    return racers


def build_sliding_window_heats(racers):
    """
    Build N heats for N racers.
    Each heat has up to 4 racers (wrapping around).
    Each racer appears exactly once per lane across all heats.
    """
    n = len(racers)
    if n == 0:
        return []

    heats = []

    for heat_index in range(n):
        heat = []

        # Sliding window across the shuffled global list.
        for j in range(min(LANES_PER_HEAT, n)):
            r = racers[(heat_index + j) % n]

            heat.append({
                "car_number": r["car_number"],
                "name": r["name"],
                "category": r["category"],
                "lane": j + 1   # lanes 1, 2, 3, 4
            })

        heats.append(heat)

    return heats


def write_heats_to_csv(all_heats):
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "heat_number", "car_number", "name", "lane"])

        heat_counter = 1

        for heat in all_heats:
            for entry in heat:
                writer.writerow([
                    entry["category"],
                    heat_counter,
                    entry["car_number"],
                    entry["name"],
                    entry["lane"]
                ])
            heat_counter += 1


def main():
    racers = load_racers(INPUT_FILE)
    if not racers:
        raise SystemExit(f"No racers found in {INPUT_FILE}")

    category_groups = defaultdict(list)
    for racer in racers:
        category_groups[racer["category"]].append(racer)

    non_group_b = []
    for category, racers_in_category in category_groups.items():
        if category == "GroupB":
            continue
        non_group_b.extend(racers_in_category)

    random.shuffle(non_group_b)
    all_heats = build_sliding_window_heats(non_group_b)

    group_b_racers = category_groups.get("GroupB", [])
    if group_b_racers:
        random.shuffle(group_b_racers)
        all_heats.extend(build_sliding_window_heats(group_b_racers))

    write_heats_to_csv(all_heats)

    print(f"Heat schedule written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()