import requests
import datetime
from utils import send_whatsapp
import os

# CLIST API config
CLIST_API_KEY = os.environ.get("CLIST_API_KEY", "18d91248076b10abca8b005576f16d18740b20ef")
CLIST_USERNAME = os.environ.get("CLIST_USERNAME", "kalpitdon")
CLIST_URL = f"https://clist.by/api/v4/contest/?username={CLIST_USERNAME}&api_key={CLIST_API_KEY}"

PLATFORMS = [
    'codeforces.com', 'atcoder.jp', 'leetcode.com', 'codechef.com', 'csacademy.com',
    'topcoder.com', 'kickstart', 'hackerearth.com', 'hackerrank.com', 'icpc.global'
]

def fetch_contests(start_gte, start_lt):
    params = {
        'start__gte': start_gte,
        'start__lt': start_lt,
        'order_by': 'start',
        'resource__name__in': ','.join(PLATFORMS),
        'limit': 100
    }
    headers = {
        'Authorization': 'ApiKey kalpitdon:18d91248076b10abca8b005576f16d18740b20ef'
    }
    r = requests.get(CLIST_URL, params=params, headers=headers)
    return r.json().get('objects', [])

def send_morning_digest():
    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + datetime.timedelta(days=1)
    contests = fetch_contests(
        today_start.isoformat() + 'Z',
        today_end.isoformat() + 'Z'
    )
    if not contests:
        msg = "☀️ Good morning! No programming contests today."
    else:
        msg = "☀️ Good morning! Here are today's contests:\n\n"
        for c in contests:
            start = c['start'].replace('T', ' ')[:-6]
            msg += f"• {c['event']} ({c['resource']['name']})\n  Starts: {start} UTC\n  Duration: {c['duration']//3600}h{(c['duration']//60)%60}m\n  Link: {c['href']}\n\n"
    send_whatsapp(msg.strip())

def send_upcoming_alerts():
    now = datetime.datetime.utcnow()
    window_start = now + datetime.timedelta(minutes=26)
    window_end = now + datetime.timedelta(minutes=34)
    contests = fetch_contests(
        window_start.isoformat() + 'Z',
        window_end.isoformat() + 'Z'
    )
    for c in contests:
        start = c['start'].replace('T', ' ')[:-6]
        msg = (
            f"⏰ Contest Alert!\n\n"
            f"{c['event']} ({c['resource']['name']})\n"
            f"Starts at: {start} UTC\n"
            f"Duration: {c['duration']//3600}h{(c['duration']//60)%60}m\n"
            f"Link: {c['href']}"
        )
        send_whatsapp(msg)
