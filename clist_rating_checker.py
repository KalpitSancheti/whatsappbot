import requests
from utils import send_whatsapp, get_ratings, set_ratings
import os

# CLIST API config
CLIST_URL = "https://clist.by/api/v4/json/coder/35625/?username=kalpitdon&api_key=18d91248076b10abca8b005576f16d18740b20ef"

def fetch_current_ratings():
    r = requests.get(CLIST_URL)
    return {acc['resource']: acc['rating'] for acc in r.json().get('accounts', [])}

def check_and_notify_ratings():
    current = fetch_current_ratings()
    old = get_ratings()
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
    set_ratings(current)
    return changes  # For logging or debugging
