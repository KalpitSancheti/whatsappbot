import requests
import json
from utils import send_whatsapp
import os

# CLIST API config
CLIST_URL = "https://clist.by/api/v4/json/coder/35625/?username=kalpitdon&api_key=18d91248076b10abca8b005576f16d18740b20ef"
RATING_FILE = "last_ratings.json"

def fetch_current_ratings():
    r = requests.get(CLIST_URL)
    return {acc['resource']: acc['rating'] for acc in r.json().get('accounts', [])}

def check_and_notify_ratings():
    current = fetch_current_ratings()
    try:
        with open(RATING_FILE, 'r') as f:
            old = json.load(f)
    except Exception:
        old = {}
    changes = []
    for platform, new_rating in current.items():
        old_rating = old.get(platform)
        if old_rating is None:
            changes.append(f"{platform}: {new_rating} (new)")
        elif old_rating != new_rating:
            diff = new_rating - old_rating
            if diff > 0:
                changes.append(f"{platform}: {old_rating} → {new_rating} ⬆️ (+{diff})")
            else:
                changes.append(f"{platform}: {old_rating} → {new_rating} ⬇️ ({diff})")
    if changes:
        msg = "📈 Rating Update!\n\n" + "\n".join(changes)
        send_whatsapp(msg)
    with open(RATING_FILE, 'w') as f:
        json.dump(current, f)
    return changes  # For logging or debugging
