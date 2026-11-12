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
# Stanford (U9) has only one team -> one scorer per day
scorer_count = {"Stanford": 1, "Patelco-E": 1, "Patelco-W": 1, "Sycamore2": 1, "Sycamore3": 1, "FSP": 1, "QR": 1}
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

# Zone preference for Ground Manager and Food Delivery
# (Scoring keeps the exact division mapping above)
zone_pref = {
    "Stanford":  ["U9", "U11"],
    "Patelco-E": ["U9", "U11"],
    "Patelco-W": ["U9", "U11"],
    "Patelco":   ["U9", "U11"],
    "Sycamore2": ["U13"],
    "Sycamore3": ["U13"],
    "Sycamore":  ["U13"],
    "FSP":       ["U15"],
    "QR":        ["U15"],
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
# gets one scorer from each of its teams (cycling through the teams that division has).
# e.g. Patelco-E -> Team1, Patelco-W -> Team2; Stanford (U9, Team1 only) -> Team1
div_teams = {
    div: [t for t in TEAMS if t in set(grp['Team'])]
    for div, grp in volunteers.groupby('Div')
}
print(f"=== Teams per division: {div_teams} ===")
scoring_slot_counter = {}
for t in task_instances:
    t["RequiredTeam"] = None
    if t["Task"] == "Scoring":
        div = division_pref.get(t["Location"], ["ALL"])[0]
        teams = div_teams.get(div) or TEAMS
        key = (t["Date"], div)
        n = scoring_slot_counter.get(key, 0)
        t["RequiredTeam"] = teams[n % len(teams)]
        scoring_slot_counter[key] = n + 1

# Allocate Scoring first (most constrained: specific division + team), then the rest by hours
tasks_df = pd.DataFrame(task_instances)
tasks_df['IsScoring'] = tasks_df['Task'] == 'Scoring'
tasks_df = (tasks_df.sort_values(by=['IsScoring', 'Hours'], ascending=[False, False], kind='stable')
            .drop(columns='IsScoring').reset_index(drop=True))

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

    prefs = division_pref.get(loc, []) if task == "Scoring" else zone_pref.get(loc, [])
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
        pools = [(candidates[in_div], ""), (candidates, "Assigned outside preferred division")]

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

# === Second pass: Misc-StandBy ===
# After the main assignments, give volunteers with fewer than STANDBY_MAX_HOURS hours
# a Misc-StandBy task: one per food-delivery location per day (4 per day).
STANDBY_HOURS = 3
STANDBY_MAX_HOURS = 8   # only volunteers with fewer than this many hours are eligible
print(f"=== # Allocating Misc-StandBy to volunteers with < {STANDBY_MAX_HOURS} hrs ===")
for date in dates:
    for loc in fd_locations:
        candidates = volunteers[volunteers['Name'].apply(lambda n: is_available(n, date))]
        eligible = candidates[candidates['AssignedHours'] < STANDBY_MAX_HOURS]
        in_zone = eligible['Div'].isin(zone_pref.get(loc, []))
        pools = [
            (eligible[in_zone], ""),
            (eligible, "Assigned outside preferred division"),
        ]  # if nobody under the limit is free, the slot stays UNASSIGNED
        chosen, note = None, ""
        for pool, pool_note in pools:
            if not pool.empty:
                chosen, note = pool.sort_values('AssignedHours', kind='stable').iloc[0], pool_note
                break

        if chosen is not None:
            idx = volunteers[volunteers['Name'] == chosen['Name']].index[0]
            volunteers.at[idx, 'AssignedHours'] += STANDBY_HOURS
            volunteers.at[idx, 'Assignments'].append({"Date": date, "Location": loc, "Task": "Misc-StandBy",
                                                      "Instance": "Day", "Hours": STANDBY_HOURS})
            assignments.append({
                "Date": date, "Location": loc, "Task": "Misc-StandBy", "Instance": "Day", "Hours": STANDBY_HOURS,
                "RequiredTeam": None, "VolunteerName": chosen['Name'], "VolunteerDiv": chosen['Div'],
                "VolunteerTeam": chosen['Team'], "Note": note
            })
        else:
            assignments.append({
                "Date": date, "Location": loc, "Task": "Misc-StandBy", "Instance": "Day", "Hours": STANDBY_HOURS,
                "RequiredTeam": None, "VolunteerName": None, "VolunteerDiv": None,
                "VolunteerTeam": None, "Note": f"UNASSIGNED - no volunteer under {STANDBY_MAX_HOURS} hrs available"
            })
print("=== # Misc-StandBy allocation done ===")
# Save to Excel
assignments_df = pd.DataFrame(assignments)
with pd.ExcelWriter("output/2026_Volunteer_Schedule_Generated.xlsx") as writer:
    # Team and Hours columns are used internally but not shown on the schedule sheet
    assignments_df.drop(columns=['Hours', 'RequiredTeam', 'VolunteerTeam']).to_excel(
        writer, index=False, sheet_name="Volunteer Schedule")
    volunteers[['Name', 'Div', 'Team', 'Mgmt', 'AssignedHours']].sort_values(by='AssignedHours', ascending=False).to_excel(
        writer, index=False, sheet_name="Volunteer Summary"
    )

print("✅ 2026 Volunteer_Schedule_Generated.xlsx has been created successfully!")
