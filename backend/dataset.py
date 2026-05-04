import pandas as pd
import random

data = []

for _ in range(3000):

    scenario = random.choice([
        "agile_dev",
        "bug_fix",
        "research",
        "deployment"
    ])

    # SCENARIO LOGIC

    if scenario == "agile_dev":
        progress = random.randint(30, 80)
        days_left = random.randint(5, 20)
        team_size = random.randint(3, 7)
        budget = random.randint(40, 80)
        complexity = random.choice([1, 2])

    elif scenario == "bug_fix":
        progress = random.randint(0, 40)
        days_left = random.randint(0, 5)
        team_size = random.randint(1, 3)
        budget = random.randint(70, 100)
        complexity = 2

    elif scenario == "research":
        progress = random.randint(20, 60)
        days_left = random.randint(10, 30)
        team_size = random.randint(2, 5)
        budget = random.randint(30, 70)
        complexity = random.choice([0, 1])

    elif scenario == "deployment":
        progress = random.randint(40, 70)
        days_left = random.randint(1, 10)
        team_size = random.randint(2, 4)
        budget = random.randint(60, 90)
        complexity = 2

    #  EDGE CASES 

    if random.random() < 0.1:
        days_left = -random.randint(1, 3)  # overdue

    if random.random() < 0.1:
        progress = 0

    if random.random() < 0.1:
        team_size = 1

    # RISK LOGIC 

    risk_score = 0

    if progress < 30:
        risk_score += 2

    if days_left < 5:
        risk_score += 2

    if budget > 85:
        risk_score += 2

    if team_size <= 2:
        risk_score += 2

    risk_score += complexity

    if days_left < 0:
        risk_score += 3

    #  FINAL CLASS 

    if risk_score >= 8:
        risk = 2
    elif risk_score >= 4:
        risk = 1
    else:
        risk = 0

    data.append([
        progress, days_left, team_size,
        budget, complexity, risk
    ])

df = pd.DataFrame(data, columns=[
    "progress", "days_left", "team_size",
    "budget_used", "task_complexity", "risk"
])

df.to_csv("project_risk_dataset.csv", index=False)

print("Realistic dataset created")
print(df["risk"].value_counts())