import streamlit as st
import joblib
import pandas as pd
import altair as alt
import database
import auth
from trello_integration import get_cards, process_cards


database.create_table()
auth.create_users_table()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "fetch_clicked" not in st.session_state:
    st.session_state["fetch_clicked"] = False

st.set_page_config(page_title="Agile Risk Tracker", layout="wide")


if not st.session_state["logged_in"]:

    menu = ["Login", "Register"]
    choice = st.sidebar.radio(" Account", menu)

    if choice == "Register":
        st.title("Create Account")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        cp = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if p != cp:
                st.error("Passwords don't match")
            else:
                if auth.add_user(u, p):
                    st.success("Account created")
                else:
                    st.error("User already exists")

    else:
        st.title("Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if auth.login_user(u, p):
                st.session_state["logged_in"] = True
                st.session_state["user"] = u
                st.rerun()
            else:
                st.error("Invalid login")

    st.stop()

#  LOGOUT 
st.sidebar.success(f" {st.session_state['user']}")
if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

#  MODEL 
model = joblib.load("risk_model.pkl")

#  FEATURE BUILDER 
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

#  UI
st.title(" Agile Risk Tracker")
st.caption("AI-powered Sprint Risk Intelligence")

#  SIDEBAR INPUT 
st.sidebar.header(" Project Inputs")

progress = st.sidebar.slider("Progress (%)", 0, 100, 50)
days_left = st.sidebar.slider("Days Left", -5, 30, 10)
team_size = st.sidebar.slider("Team Size", 1, 10, 5)
budget = st.sidebar.slider("Budget Used (%)", 20, 100, 50)
complexity = st.sidebar.selectbox("Complexity", ["Low", "Medium", "High"])

complexity_map = {"Low": 0, "Medium": 1, "High": 2}
c_val = complexity_map[complexity]

# - LAYOUT 
col1, col2 = st.columns([1, 2])

# ANALYSIS 
with col1:
    st.subheader(" Risk Analysis")

    if st.button("Analyze Risk"):

        sample = build_features(progress, days_left, team_size, budget, c_val)

        pred = model.predict(sample)[0]
        prob = model.predict_proba(sample)[0]
        confidence = round(max(prob) * 100, 2)

        database.add_data((progress, days_left, team_size, budget, c_val, pred))

        risk_labels = {
            0: " LOW RISK",
            1: " MEDIUM RISK",
            2: " HIGH RISK"
        }

        st.markdown(f"### {risk_labels[pred]}")
        st.metric("Confidence", f"{confidence}%")

        if pred == 2:
            st.error(" High chance of delay")
        elif pred == 1:
            st.warning(" Needs attention")
        else:
            st.success(" On track")

        reasons = []
        if progress < 40:
            reasons.append("Low progress")
        if days_left < 5:
            reasons.append("Deadline near")
        if team_size <= 3:
            reasons.append("Small team")

        if reasons:
            st.markdown(" **Why?**")
            for r in reasons:
                st.write(f"• {r}")

        st.markdown(" **Action:**")
        if pred == 2:
            st.write(" Add resources or extend deadline")
        elif pred == 1:
            st.write(" Monitor closely")
        else:
            st.write(" Continue as planned")

# ---------------- ANALYTICS ----------------
with col2:
    st.subheader(" Analytics")

    data = database.view_data()

    if data:
        df = pd.DataFrame(data, columns=[
            "Progress", "Days Left", "Team Size",
            "Budget", "Complexity", "Risk", "Timestamp"
        ])

        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df["Risk Label"] = df["Risk"].map({0: "Low", 1: "Medium", 2: "High"})

        chart = alt.Chart(df).mark_line(point=True).encode(
            x="Timestamp:T",
            y="Risk",
            color="Risk Label"
        )

        st.altair_chart(chart, use_container_width=True)
        st.dataframe(df)

# TRELLO
st.divider()
st.subheader("Trello Integration")

board_input = st.text_input("Enter Board ID or URL")

if "trello.com" in board_input:
    board_id = board_input.split("/b/")[1].split("/")[0]
else:
    board_id = board_input

if st.button("Fetch Trello Data"):
    st.session_state.fetch_clicked = True

#  RUN ONLY ONCE (NO DUPLICATION)
if st.session_state.fetch_clicked:

    cards = get_cards(board_id)

    if not cards:
        st.error(" API error or invalid board")
    else:
        tasks = process_cards(cards)

        st.success(f"{len(tasks)} tasks loaded")

        risk_labels = {
            0: "LOW RISK",
            1: "MEDIUM RISK",
            2: " HIGH RISK"
        }

        for i, t in enumerate(tasks):

            with st.container():

                p, d, t_size, b, c = t

                sample = build_features(p, d, t_size, b, c)

                pred = model.predict(sample)[0]
                prob = model.predict_proba(sample)[0]
                confidence = round(max(prob) * 100, 2)

                st.markdown(f"##  Task {i+1}")
                st.markdown(f"### {risk_labels[pred]}")
                st.metric(f"Confidence (Task {i+1})", f"{confidence}%")

                if confidence < 60:
                    st.warning(" Low confidence → data may be incomplete")

                reasons = []
                if p < 40:
                    reasons.append("Low progress")
                if d < 5:
                    reasons.append("Deadline is near")
                if t_size <= 3:
                    reasons.append("Small team")
                if d < 0:
                    reasons.append("Task is overdue")

                if reasons:
                    st.markdown(" **Why this risk?**")
                    for r in reasons:
                        st.write(f"• {r}")

                if pred == 2:
                    st.error("High chance of delay")
                elif pred == 1:
                    st.warning(" Needs attention")
                else:
                    st.success(" Task on track")

                st.markdown(" **Suggested Action:**")

                if pred == 2:
                    st.write(" Add more team members or extend deadline")
                elif pred == 1:
                    st.write(" Monitor closely")
                else:
                    st.write(" Continue as planned")

                if p == 50 and d == 10:
                    st.error(" Insufficient data → unreliable prediction")

                st.markdown("---")