from flask import Flask, request, jsonify
import joblib
import pandas as pd
from trello_integration import get_cards, process_cards

app = Flask(__name__)
model = joblib.load("risk_model.pkl")

# ---------------- HOME ROUTE ----------------
@app.route("/")
def home():
    return jsonify({
        "message": " Agile Risk Tracker API is running",
        "endpoints": {
            "/predict": "POST → risk prediction",
            "/trello": "POST → trello task analysis"
        }
    })

# ---------------- FEATURE BUILDER ----------------
def build_features(p, d, t, b, c):

    p = p if p is not None else 50
    d = d if d is not None else 10
    t = max(t if t else 3, 1)

    d_safe = d if d != 0 else 1
    p_safe = p if p != 0 else 1

    return pd.DataFrame([{
        "progress": p,
        "days_left": d,
        "team_size": t,
        "budget_used": b,
        "task_complexity": c,
        "urgency": p/d_safe,
        "efficiency": p/t,
        "budget_pressure": b/p_safe,
        "time_pressure": d/p_safe,
        "team_load": c/t,
        "overdue": int(d < 0),
        "low_progress": int(p < 40),
        "small_team": int(t <= 3)
    }])

# ---------------- PREDICT ----------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json

        sample = build_features(
            int(data["progress"]),
            int(data["days_left"]),
            int(data["team_size"]),
            int(data["budget"]),
            int(data["complexity"])
        )

        pred = model.predict(sample)[0]
        prob = model.predict_proba(sample)[0]
        confidence = round(max(prob) * 100, 2)

        labels = ["Low", "Medium", "High"]

        return jsonify({
            "prediction": int(pred),
            "label": labels[pred],
            "confidence": confidence,
            "message": "Prediction successful"
        })

    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- TRELLO ----------------
@app.route("/trello", methods=["POST"])
def trello():
    try:
        board_id = request.json["board_id"]

        cards = get_cards(board_id)
        tasks = process_cards(cards)

        output = []
        labels = ["Low", "Medium", "High"]

        for t in tasks:
            p, d, ts, b, c = t

            sample = build_features(p, d, ts, b, c)

            pred = model.predict(sample)[0]
            prob = model.predict_proba(sample)[0]

            output.append({
                "prediction": int(pred),
                "label": labels[pred],
                "confidence": round(max(prob) * 100, 2)
            })

        return jsonify({"tasks": output})

    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)