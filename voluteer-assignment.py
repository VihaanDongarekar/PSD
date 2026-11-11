import pandas as pd
from datetime import datetime, timedelta

# === Load your CSV ===
print("=== Loading input data from CSV ===")
players_df = pd.read_csv("inputData/PSD2026-input.csv")

# Normalize columns
print("=== # Normalizing columns in the input data===")
players_df.rename(columns={"Player Name": "Name"}, inplace=True)
players_df['Mgmt'] = players_df['Mgmt'].astype(str).str.strip().str.title()
players_df['Name'] = players_df['Name'].astype(str).str.strip()
players_df['Div'] = players_df['Div'].astype(str).str.strip().str.upper()
div_remap = {"U10": "U9", "U12": "U11", "U14": "U13", "U16": "U15"}
players_df['Div'] = players_df['Div'].replace(div_remap)

# Team column: normalize values like "team 1", "TEAM1", "1" -> "Team1"
TEAM_COLUMN = "Team"   # change this if the CSV header is different
TEAMS = ["Team1", "Team2"]
players_df['Team'] = (
    players_df[TEAM_COLUMN].astype(str).str.strip().str.lower()
    .str.replace(" ", "", regex=False).str.replace("team", "", regex=False)
    .map(lambda t: f"Team{t}" if t in ("1", "2") else "Unknown")
)
unknown_team = players_df[players_df['Team'] == "Unknown"]
if not unknown_team.empty:
    print(f"WARNING: {len(unknown_team)} player(s) have no valid Team value: "
          f"{', '.join(unknown_team['Name'])}")

# Exclude management players
print("=== # Exclude management players===")
volunteers = players_df[players_df['Mgmt'] != 'Yes'].copy().reset_index(drop=True)
volunteers['AssignedHours'] = 0.0
volunteers['Assignments'] = [[] for _ in range(len(volunteers))]

# Tournament setup
start_date = datetime(2026, 11, 26)
dates = [(start_date + timedelta(days=i)).date() for i in range(4)]
locations = ["Stanford", "Patelco-E", "Patelco-W", "Sycamore2", "Sycamore3", "FSP", "QR"]
fd_locations = ["Patelco", "Sycamore", "FSP", "QR"]

# Task and location setup
ground_manager_count = {"Stanford": 2, "Patelco-E": 2, "Patelco-W": 2, "Sycamore2": 2, "Sycamore3": 2, "FSP": 1, "QR": 1}
food_delivery_count = {"Patelco": 2, "Sycamore": 2, "FSP": 1, "QR": 1 }
scorer_count = {"Stanford": 2, "Patelco-E": 1, "Patelco-W": 1, "Sycamore2": 1, "Sycamore3": 1, "FSP": 1, "QR": 1}
division_pref = {
    "Stanford": ["U9"],
    "Patelco-E": ["U11"],
    "Patelco-W": ["U11"],
    "Sycamore2": ["U13"],
    "Sycamore3": ["U13"],
    "FSP": ["U15"],
    "Tarika": ["U15"],
    "QR": ["U15"],
}

print("=== # Task and location setup done===")
# Generate all task instances
task_instances = []
for date in dates:
    for loc in locations:
        gm_count = ground_manager_count[loc]
        scr_count = scorer_count[loc]
        if gm_count == 2:
            task_instances.extend([
                {"Date": date, "Location": loc, "Task": "Ground Manager", "Instance": "AM", "Hours": 5},
                {"Date": date, "Location": loc, "Task": "Ground Manager", "Instance": "PM", "Hours": 5},
            ])
        elif gm_count == 4:
            task_instances.extend([
                {"Date": date, "Location": loc, "Task": "Ground Manager1", "Instance": "AM", "Hours": 5},
                {"Date": date, "Location": loc, "Task": "Ground Manager1", "Instance": "PM", "Hours": 5},
                {"Date": date, "Location": loc, "Task": "Ground Manager2", "Instance": "AM", "Hours": 5},
                {"Date": date, "Location": loc, "Task": "Ground Manager2", "Instance": "PM", "Hours": 5},
            ])
        else :
            task_instances.append({"Date": date, "Location": loc, "Task": "Ground Manager", "Instance": "Day", "Hours": 5})


        if scr_count == 2:
            task_instances.extend([{"Date": date, "Location": loc, "Task": "Scoring", "Instance": "Day", "Hours": 4},
                                    {"Date": date, "Location": loc, "Task": "Scoring", "Instance": "Day", "Hours": 4},
            ])
        else :
            task_instances.append({"Date": date, "Location": loc, "Task": "Scoring", "Instance": "Day", "Hours": 4})

        #task_instances.extend([
        #    {"Date": date, "Location": loc, "Task": "Food Delivery", "Instance": "Day", "Hours": 3},
        #    {"Date": date, "Location": loc, "Task": "Scoring", "Instance": "Day", "Hours": 4},
        #])
    for fd_locs in fd_locations:
        fd_count = food_delivery_count[fd_locs]
        if fd_count == 2:
            task_instances.extend([
                {"Date": date, "Location": fd_locs, "Task": "Food Delivery", "Instance": "Day", "Hours": 4},
                {"Date": date, "Location": fd_locs, "Task": "Food Delivery", "Instance": "Day", "Hours": 4},
            ])
        else :
            task_instances.append({"Date": date, "Location": fd_locs, "Task": "Food Delivery", "Instance": "Day", "Hours": 4})


# Assign a required team to each Scoring slot so that, every day, each division
# gets one scorer from Team1 and one from Team2 (alternating across its slots).
# e.g. Stanford slot1 -> Team1, slot2 -> Team2; Patelco-E -> Team1, Patelco-W -> Team2
scoring_slot_counter = {}
for t in task_instances:
    t["RequiredTeam"] = None
    if t["Task"] == "Scoring":
        div = division_pref.get(t["Location"], ["ALL"])[0]
        key = (t["Date"], div)
        n = scoring_slot_counter.get(key, 0)
        t["RequiredTeam"] = TEAMS[n % len(TEAMS)]
        scoring_slot_counter[key] = n + 1

tasks_df = pd.DataFrame(task_instances).sort_values(by='Hours', ascending=False, kind='stable').reset_index(drop=True)

print("=== # Generated all task instances===")
# Helper to check availability
def is_available(vol_name, date):
    row = volunteers.loc[volunteers['Name'] == vol_name]
    if row.empty:
        return False
    assignments = row['Assignments'].iloc[0]
    return all(a['Date'] != date for a in assignments)

# Allocate volunteers
print("=== # Stating to allocate volunteers ===")
assignments = []
for _, row in tasks_df.iterrows():
    date, loc, task, inst, hrs = row['Date'], row['Location'], row['Task'], row['Instance'], row['Hours']
    req_team = row['RequiredTeam']
    candidates = volunteers.copy()
    candidates = candidates[candidates['Name'].apply(lambda n: is_available(n, date))]

    prefs = division_pref.get(loc, [])
    in_div = candidates['Div'].isin(prefs) if prefs else pd.Series(False, index=candidates.index)

    # Candidate pools in priority order
    if req_team:
        in_team = candidates['Team'] == req_team
        pools = [
            (candidates[in_div & in_team], ""),
            (candidates[in_team], f"{req_team} scorer from outside preferred division"),
            (candidates[in_div], f"No {req_team} volunteer available - used other team"),
            (candidates, f"No {req_team} volunteer available - used other team"),
        ]
    else:
        pools = [(candidates[in_div], ""), (candidates, "")]

    chosen, note = None, ""
    for pool, pool_note in pools:
        if not pool.empty:
            chosen, note = pool.sort_values('AssignedHours', kind='stable').iloc[0], pool_note
            break

    if chosen is not None:
        vname, vdiv, vteam = chosen['Name'], chosen['Div'], chosen['Team']
        idx = volunteers[volunteers['Name'] == vname].index[0]
        volunteers.at[idx, 'AssignedHours'] += hrs
        # Following lines had issues and was giving error.
    #    volunteers.at[idx, 'Assignments'].iloc[0].append(
    #        {"Date": date, "Location": loc, "Task": task, "Instance": inst, "Hours": hrs})
        volunteers.at[idx, 'Assignments'].append({"Date": date, "Location": loc, "Task": task, "Instance": inst, "Hours": hrs})

        assignments.append({
            "Date": date, "Location": loc, "Task": task, "Instance": inst, "Hours": hrs,
            "RequiredTeam": req_team, "VolunteerName": vname, "VolunteerDiv": vdiv,
            "VolunteerTeam": vteam, "Note": note
        })
    else:
        assignments.append({
            "Date": date, "Location": loc, "Task": task, "Instance": inst, "Hours": hrs,
            "RequiredTeam": req_team, "VolunteerName": None, "VolunteerDiv": None,
            "VolunteerTeam": None, "Note": "UNASSIGNED"
        })

print("=== # Allocating volunteers done===")
# Save to Excel
assignments_df = pd.DataFrame(assignments)
with pd.ExcelWriter("output/2026_Volunteer_Schedule_Generated.xlsx") as writer:
    assignments_df.to_excel(writer, index=False, sheet_name="Volunteer Schedule")
    volunteers[['Name', 'Div', 'Team', 'Mgmt', 'AssignedHours']].sort_values(by='AssignedHours', ascending=False).to_excel(
        writer, index=False, sheet_name="Volunteer Summary"
    )

print("✅ 2026 Volunteer_Schedule_Generated.xlsx has been created successfully!")
