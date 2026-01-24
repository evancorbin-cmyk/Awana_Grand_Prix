import csv
from collections import defaultdict

INPUT_FILE = "Racer List.csv"
OUTPUT_FILE = "heats.csv"


def load_racers(filename):
    racers_by_category = defaultdict(list)
    with open(filename, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            racers_by_category[row["Category"]].append({
                "car_number": row["Car_Number"],
                "name": row["Name"]
            })
    return racers_by_category


def build_sliding_window_heats(racers):
    """
    Build N heats for N racers.
    Each heat has 4 racers (wrapping around).
    Each racer appears exactly once per lane across all heats.
    """
    n = len(racers)
    heats = []

    for heat_index in range(n):
        heat = []

        # Sliding window of 4 racers
        for j in range(4):
            r = racers[(heat_index + j) % n]

            heat.append({
                "car_number": r["car_number"],
                "name": r["name"],
                "lane": j + 1   # lanes 1, 2, 3, 4
            })

        heats.append(heat)

    return heats


def write_heats_to_csv(all_heats):
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "heat_number", "car_number", "name", "lane"])

        heat_counter = 1   # <-- moved OUTSIDE the category loop

        for category, heats in all_heats.items():
            for heat in heats:
                for entry in heat:
                    writer.writerow([
                        category,
                        heat_counter,
                        entry["car_number"],
                        entry["name"],
                        entry["lane"]
                    ])
                heat_counter += 1
import json

def write_heats_to_json(all_heats, filename="heats.json"):
    data = {"categories": []}

    heat_counter = 1

    for category, heats in all_heats.items():
        cat_entry = {"name": category, "heats": []}

        for heat in heats:
            heat_entry = {
                "heat_number": heat_counter,
                "racers": heat
            }
            cat_entry["heats"].append(heat_entry)
            heat_counter += 1

        data["categories"].append(cat_entry)

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def main():
    racers_by_category = load_racers(INPUT_FILE)
    all_heats = {}

    for category, racers in racers_by_category.items():
        racers_sorted = sorted(racers, key=lambda r: int(r["car_number"]))
        heats = build_sliding_window_heats(racers_sorted)
        all_heats[category] = heats

    write_heats_to_csv(all_heats)
    write_heats_to_json(all_heats, "heats.json")

    print(f"Heat schedule written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()