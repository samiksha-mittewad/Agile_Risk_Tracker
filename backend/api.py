from pathlib import Path
import sqlite3

import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from trello_integration import get_cards, process_cards


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "risk.db"

app = Flask(__name__, static_folder=str(BASE_DIR / "public"), static_url_path="")
CORS(app)
model = joblib.load(BASE_DIR / "risk_model.pkl")


def create_api_history_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS api_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            progress INTEGER,
            days_left INTEGER,
            team_size INTEGER,
            budget INTEGER,
            complexity INTEGER,
            prediction INTEGER NOT NULL,
            label TEXT NOT NULL,
            confidence REAL NOT NULL,
            board_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_history(source, inputs, prediction, label, confidence, board_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO api_history
        (source, progress, days_left, team_size, budget, complexity, prediction, label, confidence, board_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        source,
        inputs.get("progress"),
        inputs.get("days_left"),
        inputs.get("team_size"),
        inputs.get("budget"),
        inputs.get("complexity"),
        prediction,
        label,
        confidence,
        board_id,
    ))
    conn.commit()
    conn.close()


def get_history(limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, source, progress, days_left, team_size, budget, complexity,
               prediction, label, confidence, board_id, timestamp
        FROM api_history
        ORDER BY timestamp DESC, id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows


def summarize_history(rows):
    counts = {"Low": 0, "Medium": 0, "High": 0}
    confidence_total = 0

    for row in rows:
        counts[row["label"]] = counts.get(row["label"], 0) + 1
        confidence_total += row["confidence"]

    total = len(rows)
    return {
        "total": total,
        "counts": counts,
        "average_confidence": round(confidence_total / total, 2) if total else 0,
        "latest": rows[0] if rows else None,
    }


def explain_risk(inputs, label):
    reasons = []

    if inputs["progress"] < 40:
        reasons.append("progress is still low")
    if inputs["days_left"] < 0:
        reasons.append("the project is overdue")
    elif inputs["days_left"] <= 5:
        reasons.append("the deadline is close")
    if inputs["team_size"] <= 3:
        reasons.append("the team is small")
    if inputs["budget"] >= 80:
        reasons.append("budget usage is high")
    if inputs["complexity"] == 2:
        reasons.append("task complexity is high")

    if reasons:
        return f"This is {label.lower()} risk because {', '.join(reasons[:3])}."

    if label == "Low":
        return "This is low risk because progress, timeline, team size, and budget look balanced."
    if label == "Medium":
        return "This is medium risk because the project has some warning signs and should be monitored."

    return "This is high risk because the current project signals suggest a strong chance of delay."


create_api_history_table()


# ---------------- HOME ROUTE ----------------
@app.route("/")
def home():
    index_path = BASE_DIR / "public" / "index.html"
    if index_path.exists():
        return send_from_directory(app.static_folder, "index.html")

    return jsonify({
        "message": "Agile Risk Tracker API is running",
        "endpoints": {
            "/predict": "POST -> risk prediction",
            "/trello": "POST -> trello task analysis",
            "/history": "GET -> prediction history and analytics",
        },
    })


@app.route("/health")
def health():
    return jsonify({
        "message": "Agile Risk Tracker API is running",
        "endpoints": {
            "/predict": "POST -> risk prediction",
            "/trello": "POST -> trello task analysis",
            "/history": "GET -> prediction history and analytics",
        },
    })


@app.route("/history")
def history():
    limit = request.args.get("limit", default=50, type=int)
    limit = min(max(limit, 1), 200)
    rows = get_history(limit)

    return jsonify({
        "history": rows,
        "summary": summarize_history(rows),
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
        "urgency": p / d_safe,
        "efficiency": p / t,
        "budget_pressure": b / p_safe,
        "time_pressure": d / p_safe,
        "team_load": c / t,
        "overdue": int(d < 0),
        "low_progress": int(p < 40),
        "small_team": int(t <= 3),
    }])


# ---------------- PREDICT ----------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True)

        inputs = {
            "progress": int(data["progress"]),
            "days_left": int(data["days_left"]),
            "team_size": int(data["team_size"]),
            "budget": int(data["budget"]),
            "complexity": int(data["complexity"]),
        }

        sample = build_features(
            inputs["progress"],
            inputs["days_left"],
            inputs["team_size"],
            inputs["budget"],
            inputs["complexity"],
        )

        pred = model.predict(sample)[0]
        prob = model.predict_proba(sample)[0]
        confidence = round(max(prob) * 100, 2)

        labels = ["Low", "Medium", "High"]
        label = labels[pred]
        explanation = explain_risk(inputs, label)
        save_history("manual", inputs, int(pred), label, confidence)

        return jsonify({
            "prediction": int(pred),
            "label": label,
            "confidence": confidence,
            "explanation": explanation,
            "message": "Prediction successful",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- TRELLO ----------------
@app.route("/trello", methods=["POST"])
def trello():
    try:
        board_id = request.get_json(force=True)["board_id"]

        cards = get_cards(board_id)
        tasks = process_cards(cards)

        output = []
        labels = ["Low", "Medium", "High"]

        for task in tasks:
            p, d, ts, b, c = task

            sample = build_features(p, d, ts, b, c)

            pred = model.predict(sample)[0]
            prob = model.predict_proba(sample)[0]
            confidence = round(max(prob) * 100, 2)
            label = labels[pred]
            inputs = {
                "progress": p,
                "days_left": d,
                "team_size": ts,
                "budget": b,
                "complexity": c,
            }
            explanation = explain_risk(inputs, label)

            save_history("trello", inputs, int(pred), label, confidence, board_id)

            output.append({
                "prediction": int(pred),
                "label": label,
                "confidence": confidence,
                "explanation": explanation,
                "inputs": inputs,
            })

        return jsonify({"tasks": output})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
