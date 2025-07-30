from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai, os, pickle, datetime
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Google Calendar Setup
def get_calendar_service():
    creds = pickle.load(open("token.pkl", "rb"))
    return build("calendar", "v3", credentials=creds)

# OpenAI: Detect intent and extract info
def parse_message_with_ai(message, date_today):
    prompt = f"""
You are a smart calendar assistant. Today is {date_today}.
User message: "{message}"

Extract:
- intent: 'create' or 'fetch'
- title: What is the task/reminder
- date: ISO date (YYYY-MM-DD)
- time: Optional (like 10:00 or say 'auto')

Give JSON only.
"""

    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    json_part = res["choices"][0]["message"]["content"]
    return json.loads(json_part)

# Find free slot for user
def find_free_slot(service, date):
    start_of_day = f"{date}T08:00:00+05:30"
    end_of_day = f"{date}T20:00:00+05:30"

    events = service.events().list(calendarId='primary', timeMin=start_of_day, timeMax=end_of_day).execute()
    slots = [(datetime.datetime.fromisoformat(start_of_day), datetime.datetime.fromisoformat(end_of_day))]

    for event in events.get("items", []):
        start = datetime.datetime.fromisoformat(event['start']['dateTime'])
        end = datetime.datetime.fromisoformat(event['end']['dateTime'])

        new_slots = []
        for s, e in slots:
            if end <= s or start >= e:
                new_slots.append((s, e))
            else:
                if s < start:
                    new_slots.append((s, start))
                if end < e:
                    new_slots.append((end, e))
        slots = new_slots

    for s, e in slots:
        if (e - s).total_seconds() >= 1800:
            return s.strftime("%H:%M")
    return None

# Main webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip()
    response = MessagingResponse()
    msg = response.message()

    today = datetime.date.today().isoformat()
    try:
        parsed = parse_message_with_ai(incoming_msg, today)
        intent = parsed.get("intent")
        date = parsed.get("date", today)
        time = parsed.get("time")
        title = parsed.get("title", "Untitled Reminder")

        service = get_calendar_service()

        if intent == "fetch":
            events_result = service.events().list(
                calendarId='primary',
                timeMin=f"{date}T00:00:00Z",
                timeMax=f"{date}T23:59:59Z",
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            if not events:
                msg.body("No events on that day.")
            else:
                reply = f"Events on {date}:\n"
                for e in events:
                    start = e['start'].get('dateTime', e['start'].get('date'))
                    reply += f"- {e['summary']} at {start}\n"
                msg.body(reply)

        elif intent == "create":
            if time == "auto":
                time = find_free_slot(service, date)
                if not time:
                    msg.body("No free 30-minute slot available on that day.")
                    return str(response)

            start = f"{date}T{time}:00+05:30"
            end_dt = datetime.datetime.strptime(time, "%H:%M") + datetime.timedelta(minutes=30)
            end = f"{date}T{end_dt.strftime('%H:%M')}:00+05:30"

            event = {
                'summary': title,
                'start': {'dateTime': start, 'timeZone': 'Asia/Kolkata'},
                'end': {'dateTime': end, 'timeZone': 'Asia/Kolkata'},
            }

            service.events().insert(calendarId='primary', body=event).execute()
            msg.body(f"✅ Reminder '{title}' created on {date} at {time}")
        else:
            msg.body("Sorry, I couldn't understand what you meant.")
    except Exception as e:
        msg.body("❌ Error processing your request.")
        print(e)

    return str(response)
