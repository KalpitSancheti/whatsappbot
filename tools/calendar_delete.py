import datetime
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re

class CalendarDeleteTool:
    name = "calendar_delete"

    def parse_time(self, time_str):
        # Accepts '20:00', '8 pm', '8:00 pm', etc. Returns 24-hour 'HH:MM' string or None.
        time_str = time_str.strip().lower()
        match = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", time_str)
        if not match:
            return None
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        ampm = match.group(3)
        if ampm == 'pm' and hour != 12:
            hour += 12
        if ampm == 'am' and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    def invoke(self, text):
        try:
            args = json.loads(text)
            title = args.get("title")
            date = args.get("date")
            time_str = args.get("time")
            calendar_id = 'kalpitjain3@gmail.com'
            creds = service_account.Credentials.from_service_account_file(
                os.path.join(os.getcwd(), 'service_account.json'),
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            service = build('calendar', 'v3', credentials=creds)
            if not date:
                return "Please provide a date to delete an event."
            # Fetch events for the day
            start_of_day = datetime.datetime.strptime(date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = datetime.datetime.strptime(date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=0)
            time_min = start_of_day.astimezone(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
            time_max = end_of_day.astimezone(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            # If time is provided, delete any event at that time
            if time_str:
                target_time = self.parse_time(time_str)
                if not target_time:
                    return f"Could not parse time '{time_str}'."
                target_dt = datetime.datetime.strptime(f"{date} {target_time}", "%Y-%m-%d %H:%M")
                for event in events:
                    e_start = event['start'].get('dateTime', event['start'].get('date'))
                    e_end = event['end'].get('dateTime', event['end'].get('date'))
                    if 'T' in e_start:
                        e_start_dt = datetime.datetime.fromisoformat(e_start.replace('Z', '+00:00'))
                    else:
                        e_start_dt = datetime.datetime.strptime(e_start, "%Y-%m-%d")
                    if 'T' in e_end:
                        e_end_dt = datetime.datetime.fromisoformat(e_end.replace('Z', '+00:00'))
                    else:
                        e_end_dt = datetime.datetime.strptime(e_end, "%Y-%m-%d")
                    if e_start_dt <= target_dt < e_end_dt:
                        service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
                        return f"Deleted event '{event.get('summary', 'No Title')}' at {target_time} on {date}."
                return f"No event found at {target_time} on {date}."
            # Otherwise, delete by title
            if title:
                for event in events:
                    if event.get('summary', '').lower() == title.lower():
                        service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
                        return f"Deleted event '{title}' on {date}."
                return f"No event titled '{title}' found on {date}."
            return "Please provide a title or time to delete an event."
        except Exception as e:
            return f"Failed to delete event: {e}"

calendar_delete_tool = CalendarDeleteTool()
