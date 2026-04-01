import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# ---------------- LOAD ----------------
df = pd.read_csv("project_risk_dataset.csv")

# ---------------- CLEANING ----------------

# Replace invalid values BEFORE feature engineering
df["progress"] = df["progress"].fillna(50)
df["days_left"] = df["days_left"].fillna(10)
df["team_size"] = df["team_size"].fillna(3)

# Prevent division issues
df["days_left_safe"] = df["days_left"].replace(0, 1)
df["progress_safe"] = df["progress"].replace(0, 1)

# ---------------- FEATURE ENGINEERING ----------------

df["urgency"] = df["progress"] / (df["days_left_safe"])
df["efficiency"] = df["progress"] / df["team_size"]
df["budget_pressure"] = df["budget_used"] / df["progress_safe"]

df["time_pressure"] = df["days_left"] / df["progress_safe"]
df["team_load"] = df["task_complexity"] / df["team_size"]

# Flags
df["overdue"] = (df["days_left"] < 0).astype(int)
df["low_progress"] = (df["progress"] < 40).astype(int)
df["small_team"] = (df["team_size"] <= 3).astype(int)

# ---------------- REMOVE TEMP COLS ----------------
df.drop(["days_left_safe", "progress_safe"], axis=1, inplace=True)

# ---------------- FINAL CLEAN ----------------

# Replace inf / -inf
df.replace([np.inf, -np.inf], np.nan, inplace=True)

# Fill any remaining NaN
df.fillna(0, inplace=True)

# ---------------- SPLIT ----------------

X = df.drop("risk", axis=1)
y = df["risk"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ---------------- MODEL ----------------

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight={0:1, 1:1, 2:3},
    random_state=42
)

model.fit(X_train, y_train)

# ---------------- EVALUATION ----------------

y_pred = model.predict(X_test)

print("\n🚀 Accuracy:", round(accuracy_score(y_test, y_pred), 4))
print("\n📊 Classification Report:\n", classification_report(y_test, y_pred))
print("\n🧩 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

# ---------------- CROSS VALIDATION ----------------

cv_scores = cross_val_score(model, X, y, cv=5)

print("\n📈 CV Scores:", cv_scores)
print("🔥 Avg CV:", round(np.mean(cv_scores), 4))

# ---------------- FEATURE IMPORTANCE ----------------

importance = model.feature_importances_
features = X.columns

print("\n🔍 Feature Importance:")
for f, i in zip(features, importance):
    print(f"{f}: {round(i, 3)}")

# ---------------- SAVE ----------------

joblib.dump(model, "risk_model.pkl")
print("\n✅ Model saved successfully")