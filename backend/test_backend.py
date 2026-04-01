import pandas as pd
import joblib
import time

from trello_integration import process_cards

# ---------------- LOAD MODEL ----------------
model = joblib.load("risk_model.pkl")


# ---------------- CORE: FEATURE BUILDER ----------------
def build_features(p, d, t, b, c):

    # -------- SAFETY --------
    p = p if p is not None else 50
    d = d if d is not None else 10
    t = t if t is not None else 3
    t = max(t, 1)

    d_safe = d if d != 0 else 1
    p_safe = p if p != 0 else 1

    # -------- FEATURES --------
    return pd.DataFrame([{
        "progress": p,
        "days_left": d,
        "team_size": t,
        "budget_used": b,
        "task_complexity": c,
        "urgency": p / d_safe,
        "efficiency": p / t,
        "budget_pressure": b / p_safe,
        "time_pressure": d / p_safe,
        "team_load": c / t,
        "overdue": int(d < 0),
        "low_progress": int(p < 40),
        "small_team": int(t <= 3)
    }])


# ---------------- TEST 1: BASIC ----------------
def test_basic():
    sample = build_features(50, 10, 5, 70, 1)
    pred = model.predict(sample)[0]
    print("Basic →", pred)


# ---------------- TEST 2: VARIETY ----------------
def test_variety():

    cases = [
        ("Safe", 50, 10, 5, 70, 1),
        ("Critical", 10, 1, 2, 95, 2),
        ("Overdue", 20, -2, 3, 80, 2),
        ("Perfect", 90, 25, 8, 30, 0)
    ]

    for name, p, d, t, b, c in cases:
        sample = build_features(p, d, t, b, c)
        pred = model.predict(sample)[0]
        print(f"{name} → {pred}")


# ---------------- TEST 3: WEIRD INPUTS ----------------
def test_weird_inputs():

    cases = [
        ("Nulls", None, None, None, 50, 1),
        ("Extreme", 999, -999, 100, 200, 5),
        ("ZeroCase", 0, 0, 1, 50, 1),
    ]

    for name, p, d, t, b, c in cases:
        sample = build_features(p, d, t, b, c)
        pred = model.predict(sample)[0]
        print(f"{name} → {pred}")


# ---------------- TEST 4: TRELLO SIMULATION ----------------
def test_trello():

    fake_cards = [{
        "due": None,
        "idMembers": [],
        "labels": [],
        "badges": {"checkItems": 0, "checkItemsChecked": 0}
    }]

    tasks = process_cards(fake_cards)

    for i, t in enumerate(tasks):
        p, d, t_size, b, c = t
        sample = build_features(p, d, t_size, b, c)
        pred = model.predict(sample)[0]
        print(f"Trello Task {i+1} → {pred}")


# ---------------- TEST 5: CONSISTENCY ----------------
def test_consistency():
    print("Consistency Test:")
    for _ in range(5):
        test_basic()


# ---------------- TEST 6: PERFORMANCE ----------------
def test_performance():

    start = time.time()

    for _ in range(100):
        sample = build_features(50, 10, 5, 70, 1)
        model.predict(sample)

    print("Time for 100 predictions:", round(time.time() - start, 4), "seconds")


# ---------------- RUN ALL ----------------
if __name__ == "__main__":

    print("\n--- BASIC ---")
    test_basic()

    print("\n--- VARIETY ---")
    test_variety()

    print("\n--- WEIRD INPUTS ---")
    test_weird_inputs()

    print("\n--- TRELLO TEST ---")
    test_trello()

    print("\n--- CONSISTENCY ---")
    test_consistency()

    print("\n--- PERFORMANCE ---")
    test_performance()