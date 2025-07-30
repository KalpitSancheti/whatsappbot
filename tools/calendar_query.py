import datetime
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz

class CalendarQueryTool:
    name = "calendar_query"

    def invoke(self, text):
        try:
            # Accept both plain string and JSON with 'date' or 'day'
            tz = pytz.timezone('Asia/Kolkata')
            date_str = None
            text = text.strip()
            # Try to parse as JSON
            try:
                args = json.loads(text)
                if isinstance(args, dict):
                    date_str = args.get('date') or args.get('day')
                elif isinstance(args, str):
                    date_str = args
            except Exception:
                date_str = text
            if not date_str or date_str.lower() in ["", "today"]:
                day = datetime.datetime.now(tz)
            elif date_str.lower() == "tomorrow":
                day = datetime.datetime.now(tz) + datetime.timedelta(days=1)
            else:
                try:
                    day = tz.localize(datetime.datetime.strptime(date_str, "%Y-%m-%d"))
                except Exception:
                    return "Invalid date format. Use YYYY-MM-DD, 'today', or 'tomorrow'."
            start_of_day = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = day.replace(hour=23, minute=59, second=59, microsecond=0)
            creds = service_account.Credentials.from_service_account_file(
                os.path.join(os.getcwd(), 'service_account.json'),
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            service = build('calendar', 'v3', credentials=creds)
            calendar_id = 'kalpitjain3@gmail.com'
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
            event_summaries = []
            busy_times = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                summary = event.get('summary', 'No Title')
                event_summaries.append(f"{summary}: {start} to {end}")
                if 'dateTime' in event['start'] and 'dateTime' in event['end']:
                    b_start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    b_end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                    if b_start_dt.tzinfo is None:
                        b_start_dt = tz.localize(b_start_dt)
                    else:
                        b_start_dt = b_start_dt.astimezone(tz)
                    if b_end_dt.tzinfo is None:
                        b_end_dt = tz.localize(b_end_dt)
                    else:
                        b_end_dt = b_end_dt.astimezone(tz)
                    busy_times.append((b_start_dt, b_end_dt, summary))
            free_slots = []
            slot_status = {}
            work_start = start_of_day.replace(hour=8, minute=0)
            work_end = start_of_day.replace(hour=22, minute=0)
            current = work_start
            offset = '+05:30'
            while current < work_end:
                next_hour = current + datetime.timedelta(hours=1)
                slot_busy = False
                busy_event = None
                for b_start_dt, b_end_dt, summary in busy_times:
                    if not (next_hour <= b_start_dt or current >= b_end_dt):
                        slot_busy = True
                        busy_event = summary
                        break
                slot_label = f"{current.strftime('%H:%M')}"
                if slot_busy:
                    slot_status[slot_label] = f"busy: {busy_event}"
                else:
                    slot_status[slot_label] = "free"
                    free_slots.append(f"{current.strftime('%H:%M')} - {next_hour.strftime('%H:%M')}")
                current = next_hour
            output = {
                "date": day.strftime("%Y-%m-%d"),
                "events": event_summaries,
                "free_slots": free_slots,
                "slot_status": slot_status
            }
            print(f"[CalendarQueryTool] Queried events for {output['date']}:", flush=True)
            print(json.dumps(output, indent=2), flush=True)
            return json.dumps(output, indent=2)
        except Exception as e:
            print(f"[CalendarQueryTool] Exception: {e}", flush=True)
            return f"Failed to fetch events: {e}"

calendar_query_tool = CalendarQueryTool()
