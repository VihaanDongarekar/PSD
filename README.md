# PSD


## 🏏 Volunteer Assignment Generator

### 📋 Overview

This script automates the process of assigning volunteer tasks for the **PSD 2025 Cricket Tournament**.
It reads player data from a CSV file and evenly distributes volunteer roles across tournament days and locations, based on predefined rules and player divisions.

### ⚙️ What It Does

* Reads player data (columns: **Mgmt**, **Name**, and **Div**) from a CSV file.
* Excludes players marked as “Yes” in the `Mgmt` column.
* Assigns volunteer tasks:

  * **Ground Manager** (AM/PM slots)
  * **Food Delivery**
  * **Scoring**
* Tasks are allocated **evenly** across players so that total volunteer hours are balanced.
* Ensures **no player is double-booked** on the same day.
* Assigns players to preferred locations by division:

  * **U10/U12** → Stanford & Patelco
  * **U14** → Sycamore
  * **U16** → Davis & FSP
* Generates a formatted Excel file:
  `Volunteer_Schedule_Generated.xlsx`
  containing a tab named **Volunteer Schedule**.

### 🗓 Tournament Details

* Dates: **Nov 27 – Nov 30**
* Locations: **Stanford, Patelco, Sycamore, Davis, FSP**
* Each task’s hours (per day, per location):

  | Task           | Hours | Notes                                                                   |
  | -------------- | ----- | ----------------------------------------------------------------------- |
  | Ground Manager | 5 hrs | 2 per day for Stanford/Patelco/Sycamore (AM & PM), 1 each for Davis/FSP |
  | Food Delivery  | 3 hrs | 1 per day per location                                                  |
  | Scoring        | 4 hrs | 1 per day per location                                                  |

### 🧩 Requirements

Install Python (v3.8 or later) and the following dependencies:

```bash
pip install pandas openpyxl
```

### ▶️ How to Run

1. Place your input CSV file in the same directory as the script.
2. Update the script’s `input_path` variable if your file name differs.
3. Run:

   ```bash
   python3 volunteer-assignment.py
   ```
4. The generated Excel file will appear in the same folder.

### 📁 Output

**Volunteer_Schedule_Generated.xlsx**

* Sheet: `Volunteer Schedule`

  * Includes columns for: Date, Location, Task, Player Assigned, and Hours.

### 💡 Example

| Date   | Location | Task                | Volunteer  | Hours |
| ------ | -------- | ------------------- | ---------- | ----- |
| Nov 27 | Stanford | Ground Manager (AM) | John Doe   | 5     |
| Nov 27 | Patelco  | Scoring             | Jane Smith | 4     |

---

Would you like me to include a **section describing how to modify the script** (e.g., to change tournament days or locations easily)? That would make it even easier for someone else to reuse later.
