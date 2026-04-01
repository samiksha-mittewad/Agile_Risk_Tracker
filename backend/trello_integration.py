import requests
from datetime import datetime

API_KEY = "66192359248f00cfad9fb92b73f606b8"
TOKEN = "ATTA4024ed0b451f002767d6bce4b41f0ac2daa1623c80a7d7371524c988b6041d0678AC326E"


def get_cards(board_id):
    url = f"https://api.trello.com/1/boards/{board_id}/cards"
    params = {"key": API_KEY, "token": TOKEN}

    res = requests.get(url, params=params)
    return res.json() if res.status_code == 200 else []


def get_progress(card):
    try:
        total = card["badges"]["checkItems"]
        done = card["badges"]["checkItemsChecked"]
        if total > 0:
            return int((done / total) * 100)
    except:
        pass
    return 50


def get_complexity(card):
    labels = [l["name"].lower() for l in card.get("labels", [])]
    if "high" in labels:
        return 2
    if "medium" in labels:
        return 1
    return 0


def process_cards(cards):
    processed = []

    for card in cards:

        # --- days_left ---
        try:
            if card.get("due"):
                due = datetime.strptime(card["due"][:10], "%Y-%m-%d")
                days_left = (due - datetime.now()).days
            else:
                days_left = 10
        except:
            days_left = 10

        # --- fallback ---
        days_left = days_left if days_left is not None else 10
        progress = get_progress(card)
        team_size = len(card.get("idMembers", [])) or 1
        complexity = get_complexity(card)

        budget = 50

        processed.append([
            progress,
            days_left,
            team_size,
            budget,
            complexity
        ])

    return processed