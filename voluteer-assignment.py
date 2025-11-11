import pandas as pd
from datetime import datetime, timedelta

# === Load your CSV ===
print("=== Loading input data from CSV ===")
players_df = pd.read_csv("inputData/PSD2025-Volunteer allocations - SRCA-Players.csv")

# Normalize columns
print("=== # Normalizing columns in the input data===")
players_df.rename(columns={"Player Name": "Name"}, inplace=True)
players_df['Mgmt'] = players_df['Mgmt'].astype(str).str.strip().str.title()
players_df['Name'] = players_df['Name'].astype(str).str.strip()
players_df['Div'] = players_df['Div'].astype(str).str.strip().str.upper()

# Exclude management players
print("=== # Exclude management players===")
volunteers = players_df[players_df['Mgmt'] != 'Yes'].copy().reset_index(drop=True)
volunteers['AssignedHours'] = 0.0
volunteers['Assignments'] = [[] for _ in range(len(volunteers))]

# Tournament setup
start_date = datetime(2025, 11, 27)
dates = [(start_date + timedelta(days=i)).date() for i in range(4)]
locations = ["Stanford", "Patelco", "Sycamore", "Davis", "FSP", "Rancho"]
fd_locations = [ "Patelco", "Sycamore", "Rancho", "FSP"]

# Task and location setup
ground_manager_count = {"Stanford": 2, "Patelco": 2, "Sycamore": 4, "Davis": 1, "FSP": 1, "Rancho": 2}
food_delivery_count  = {"Patelco" : 2, "Sycamore": 2, "Rancho": 2, "FSP": 1}
scorer_count = {"Stanford": 1, "Patelco": 2, "Sycamore": 2, "Davis": 1, "FSP": 1, "Rancho": 1}
division_pref = {
    "Sycamore": ["U14"],
#    "Sycamore3": ["U14"],
    "Stanford": ["U10", "U12"],
    "Patelco": ["U10", "U12"],
    "Davis": ["U16"],
    "FSP": ["U16"],
    "Rancho": ["U12"],
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
                {"Date": date, "Location": fd_locs, "Task": "Food Delivery", "Instance": "Day", "Hours": 3},
                {"Date": date, "Location": fd_locs, "Task": "Food Delivery", "Instance": "Day", "Hours": 3},
            ])
        else :
            task_instances.append({"Date": date, "Location": fd_locs, "Task": "Food Delivery", "Instance": "Day", "Hours": 3})


tasks_df = pd.DataFrame(task_instances).sort_values(by='Hours', ascending=False).reset_index(drop=True)

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
    candidates = volunteers.copy()
    candidates = candidates[candidates['Name'].apply(lambda n: is_available(n, date))]

    prefs = division_pref.get(loc, [])
    pref_candidates = candidates[candidates['Div'].isin(prefs)] if prefs else pd.DataFrame(columns=candidates.columns)

    chosen = None
    if not pref_candidates.empty:
        chosen = pref_candidates.sort_values('AssignedHours').iloc[0]
    elif not candidates.empty:
        chosen = candidates.sort_values('AssignedHours').iloc[0]

    if chosen is not None:
        vname, vdiv = chosen['Name'], chosen['Div']
        idx = volunteers[volunteers['Name'] == vname].index[0]
        volunteers.at[idx, 'AssignedHours'] += hrs
        # Following lines had issues and was giving error.
    #    volunteers.at[idx, 'Assignments'].iloc[0].append(
    #        {"Date": date, "Location": loc, "Task": task, "Instance": inst, "Hours": hrs})
        volunteers.at[idx, 'Assignments'].append({"Date": date, "Location": loc, "Task": task, "Instance": inst, "Hours": hrs})

        assignments.append({
            "Date": date, "Location": loc, "Task": task, "Instance": inst, "Hours": hrs,
            "VolunteerName": vname, "VolunteerDiv": vdiv, "Note": ""
        })
    else:
        assignments.append({
            "Date": date, "Location": loc, "Task": task, "Instance": inst, "Hours": hrs,
            "VolunteerName": None, "VolunteerDiv": None, "Note": "UNASSIGNED"
        })

print("=== # Allocating volunteers done===")
# Save to Excel
assignments_df = pd.DataFrame(assignments)
with pd.ExcelWriter("output/Volunteer_Schedule_Generated.xlsx") as writer:
    assignments_df.to_excel(writer, index=False, sheet_name="Volunteer Schedule")
    volunteers[['Name', 'Div', 'Mgmt', 'AssignedHours']].sort_values(by='AssignedHours', ascending=False).to_excel(
        writer, index=False, sheet_name="Volunteer Summary"
    )

print("✅ Volunteer_Schedule_Generated.xlsx has been created successfully!")
