# Awana Grand Prix Race Control System

A comprehensive race timing and leaderboard management system for the Awana Grand Prix event. This system automates race monitoring, result recording, and real-time leaderboard updates using Arduino integration and a PyQt5-based graphical interface.

## Overview

The Awana Grand Prix Race Control System is designed to manage multiple racing categories (Cubbies, Sparks, T&T, Trek, Journey, and GroupB) with automated heat scheduling, real-time lane timing via Arduino, and dynamic leaderboard displays.

## Features

- **Real-time Race Monitoring**: Receives lane timing data from Arduino via serial communication
- **Multi-Category Support**: Manages 6 different racing categories with separate leaderboards
- **Dynamic Heat Scheduling**: Automatically sequences heats and tracks completion
- **Live Leaderboard**: Updates category leaderboards after each heat
- **Final Results Report**: Generates final_leaders.csv with top 3 racers per category
- **Animated UI**: PyQt5-based dashboard with animated tables, category GIFs, and sound effects
- **Data Persistence**: All results stored in CSV format for archival and analysis

## Quick Start

### Requirements

- Python 3.7+
- PyQt5
- PyGame
- PySerial
- Arduino with timing gate hardware

### Installation

1. Clone or download the project files
2. Install Python dependencies:
   ```bash
   pip install PyQt5 pygame pyserial
   ```
3. Ensure Arduino is connected to the specified COM port (default: COM4)
4. **Verify COM Port and Baud Rate**:
   - Check which COM port your Arduino is using (Device Manager in Windows)
   - Open `AwanaTiming_Clean.py` and update these settings:
     ```python
     COMM_PORT = "COM4"      # Change to your Arduino's COM port
     BAUD_RATE = 9600        # Change if your Arduino uses different baud rate
     ```
5. Place required GIF files in the project directory

### Setup Before Each Race

**IMPORTANT**: Before running the race, follow these steps in order:

1. **Create/Update Racer List** - Create or edit a file named exactly `Racer List.csv`:
   - **IMPORTANT**: File name MUST be exactly `Racer List.csv` (with space and capital letters) or the program won't find it
   - Columns: `Car_Number`, `Name`, `Category` (in this order)
   - One racer per row
   - Example:
     ```
     Car_Number,Name,Category
     101,Donald Duck,Cubbies
     102,Donald Trump,Cubbies
     201,Mickey Mouse,Sparks
     ```
   - Save the file

2. **Generate Heat Schedule** - Run the Heat Generator:
   ```bash
   python "Heat Generator.py"
   ```
   This will create the `heats.csv` file with the race schedule

3. **Start the Race Dashboard** - Run the UI:
   ```bash
   python RaceUI.py
   ```
   The dashboard will automatically launch the timing system

### Running the System

1. **During the Race**:
   - The dashboard displays the current heat, leaderboard, and next heat
   - Monitor animated category GIFs during races
   - Races proceed automatically through all heats
   - Click "Show Final Results" to view the final leaderboard
   - Click "Exit" to close the application

2. **If a Heat Needs to be Redone**:
   - **Exit the UI** - Click the Exit button to close the application
   - **Edit heats_results.csv** - Delete the last heat's results (remove all rows for that heat)
   - **Save the file** - Close and save heats_results.csv
   - **Re-run the UI** - Execute `python RaceUI.py` again
   - The system will resume from the corrected point

2. **Using the Dashboard**:
   - Monitor the current heat, leaderboard, and next heat information
   - View animated category GIFs during races
   - Click "Show Final Results" to view the final leaderboard
   - Click "Exit" to close the application

## Project Structure

```
├── AwanaTiming_Clean.py          # Main race timing engine
├── RaceUI.py                      # PyQt5 dashboard interface
├── AwanaTimingGateArduino.ino     # Arduino sketch for timing gates
├── heats.csv                      # Race configuration (categories, heat assignments)
├── heats_results.csv              # All completed race results
├── current_heat.csv               # Current heat results
├── current_leaderboard.csv        # Current category leaderboard
├── final_leaders.csv              # Final top 3 per category (generated at race end)
├── upnext.csv                     # Next heat to run
└── [category_gifs]                # Animated GIFs for each category
```

## CSV File Formats

### heats.csv
Defines all heats and lane assignments:
```
category,heat_number,car_number,name,lane
```

### heats_results.csv
Records all completed race results:
```
category,heat_number,car_number,name,lane,time_ms
```

### current_leaderboard.csv
Tracks average times per racer in current category:
```
Place,Category,car_number,name,Average Time (ms)
```

### final_leaders.csv
Generated at race completion, shows top 3 per category:
```
Place,Category,Car Number,Name,Average Time (ms)
```

## Arduino Integration

The system communicates with an Arduino device via serial (COM4, 9600 baud) expecting messages in the format:
- `Race Started` - Initiates heat timing
- `Lane X: Y ms` - Records lane X finish time in milliseconds
- `Race Reset` - Resets current heat

## Features in Detail

### Real-time Leaderboard Updates
After each heat, the system automatically:
1. Records all lane times
2. Calculates average times across all completed heats for each racer
3. Updates current_leaderboard.csv with top 3 racers
4. Displays results with animated table rows

### Final Results Generation
When all heats complete:
1. Generates final_leaders.csv with rankings across all heats
2. Groups results by category in order: Cubbies, Sparks, T&T, Trek, Journey, GroupB
3. Displays final results in a dedicated window with category GIFs
4. Plays menu music on loop

### Sound Effects
- Menu.mp3 - Background during heat selection
- RaceStarted.mp3 - Played when heat begins
- RaceFinished.mp3 - Played when heat completes
- RaceReset.mp3 - Played when race resets
- swoosh.wav - Table row animation sound effect

## Configuration

Key settings in `AwanaTiming_Clean.py`:
```python
COMM_PORT = "COM4"          # Arduino serial port
BAUD_RATE = 9600            # Serial communication speed
HEATS_FILE = "heats.csv"    # Input heats configuration
CSV_RESULTS_FILE = "heats_results.csv"  # Output results file
```

## Troubleshooting

- **Serial Connection Error**: Verify Arduino is connected and COM port matches COMM_PORT setting
- **Missing GIFs**: Ensure all category GIF files are in the project directory
- **Window Geometry Error**: May occur on small screens; system will auto-adjust table sizes

## Developer Notes

- The timing engine loops continuously, restarting when all heats complete
- CSV files are read/written with proper DictReader/writer for robustness
- UI updates occur every second via QTimer
- Animations play with 600ms intervals per row
- All times are in milliseconds for precision

## License

See LICENSE file for details

## Support

For issues or questions, refer to the code comments and the .github/copilot-instructions.md file for architecture details.
