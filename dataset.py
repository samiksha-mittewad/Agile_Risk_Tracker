import pandas as pd
import random

data = []

for _ in range(3000):

    # --- simulate real-world missing data ---
    progress = random.choice([random.randint(0, 100), None])
    days_left = random.choice([random.randint(-5, 30), None])  # include overdue
    team_size = random.choice([random.randint(1, 10), None])
    budget_used = random.randint(20, 100)
    task_complexity = random.choice([0, 1, 2])

    # --- fallback handling ---
    progress = progress if progress is not None else 50
    days_left = days_left if days_left is not None else 10
    team_size = team_size if team_size is not None else 3

    risk_score = 0

    # --- base logic ---
    if progress < 30:
        risk_score += 2
    elif progress < 60:
        risk_score += 1

    if days_left < 5:
        risk_score += 2
    elif days_left < 10:
        risk_score += 1

    if budget_used > 85:
        risk_score += 2
    elif budget_used > 70:
        risk_score += 1

    if team_size <= 3:
        risk_score += 2

    risk_score += task_complexity

    # --- real-world patterns ---
    if progress < 30 and days_left < 5:
        risk_score += 3

    if days_left < 0:  # overdue
        risk_score += 3

    if team_size <= 2 and task_complexity == 2:
        risk_score += 2

    # --- category ---
    if risk_score >= 8:
        risk = 2
    elif risk_score >= 4:
        risk = 1
    else:
        risk = 0

    # --- controlled noise ---
    if random.random() < 0.1:
        risk = max(0, min(2, risk + random.choice([0, 1])))

    data.append([
        progress, days_left, team_size,
        budget_used, task_complexity, risk
    ])

df = pd.DataFrame(data, columns=[
    "progress", "days_left", "team_size",
    "budget_used", "task_complexity", "risk"
])

df.to_csv("project_risk_dataset.csv", index=False)

print("Dataset ready")
print(df["risk"].value_counts())