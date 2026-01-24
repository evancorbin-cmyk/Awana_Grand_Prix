# Copilot Instructions for Awana Grand Prix Codebase

## Overview
This codebase is designed for managing the Awana Grand Prix race control system. It includes functionalities for loading heats, monitoring race progress, and recording results. The main script is `AwanaTiming_Clean.py`, which orchestrates the race logic and communicates with an Arduino for real-time updates.

## Architecture
- **Main Components**:
  - `AwanaTiming_Clean.py`: The primary script that handles race logic, including loading heats, monitoring serial input, and writing results to CSV files.
  - CSV Files: Used for storing heats, results, and current race state. Key files include:
    - `heats.csv`: Contains the configuration for heats.
    - `heats_results.csv`: Stores results of completed heats.
    - `current_heat.csv`: Holds the current heat's data.
    - `upnext.csv`: Lists the next heat to be run.

- **Data Flow**:
  - The system reads from `heats.csv` to load race configurations.
  - Results are recorded in `heats_results.csv` after each heat.
  - The system communicates with an Arduino via serial to receive lane times.

## Developer Workflows
- **Running the System**:
  - Ensure the Arduino is connected to the specified COM port.
  - Run `AwanaTiming_Clean.py` to start the race monitoring process.

- **Testing**:
  - Tests can be added to validate the functionality of individual components, especially the CSV handling and race logic.

- **Debugging**:
  - Use print statements to log the state of the system at various points, especially when reading from the serial port.

## Project-Specific Conventions
- **File Naming**: Use lowercase with underscores for file names (e.g., `AwanaTiming_Clean.py`).
- **CSV Structure**: Ensure that CSV files adhere to the expected structure as defined in the code, particularly the headers.

## Integration Points
- **Arduino Communication**: The system expects specific messages from the Arduino (e.g., "Race Started", "Lane X: Y ms"). Ensure the Arduino is programmed to send these messages correctly.

## External Dependencies
- **Python Libraries**: The project uses the following libraries:
  - `pygame`: For sound management.
  - `serial`: For serial communication with the Arduino.

## Conclusion
This document serves as a guide for AI coding agents to understand the Awana Grand Prix codebase. For further details, refer to the code comments and the README.md file.