import datetime
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

class CalendarTool:
    name = "calendar"

    def invoke(self, text):
        print("[CalendarTool] invoke called", flush=True)
        try:
            args = json.loads(text)
            title = args.get("title", "Untitled Event")
            description = args.get("description", "")
            date = args.get("date")
            start_time = args.get("start_time")
            end_time = args.get("end_time")
            offset = '+05:30'
            if start_time and 'T' in start_time:
                dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                date = dt.strftime("%Y-%m-%d")
                start_time_fmt = dt.strftime("%H:%M")
            else:
                start_time_fmt = start_time
            if end_time and 'T' in end_time:
                dt_end = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                end_time_fmt = dt_end.strftime("%H:%M")
            else:
                end_time_fmt = end_time
            if not start_time_fmt and "time" in args:
                time_val = args["time"]
                try:
                    dt = datetime.datetime.fromisoformat(time_val.replace('Z', '+00:00'))
                    date = dt.strftime("%Y-%m-%d")
                    start_time_fmt = dt.strftime("%H:%M")
                except Exception:
                    start_time_fmt = time_val
            if start_time_fmt and not end_time_fmt:
                hour, minute = map(int, start_time_fmt.split(":"))
                start_dt_obj = datetime.datetime.strptime(date, "%Y-%m-%d").replace(hour=hour, minute=minute)
                end_dt_obj = start_dt_obj + datetime.timedelta(hours=1)
                end_time_fmt = end_dt_obj.strftime("%H:%M")
            if not (date and start_time_fmt and end_time_fmt):
                print("[CalendarTool] Missing date or time information.", flush=True)
                return "Missing date or time information."
            start_dt = f"{date}T{start_time_fmt}:00{offset}"
            end_dt = f"{date}T{end_time_fmt}:00{offset}"
            event = {
                'summary': title,
                'description': description,
                'start': {'dateTime': start_dt},
                'end': {'dateTime': end_dt},
            }
            calendar_id = 'kalpitjain3@gmail.com'
            print(f"[CalendarTool] calendarId: {calendar_id}", flush=True)
            print(f"[CalendarTool] Event JSON to be sent: {json.dumps(event, indent=2)}", flush=True)
            creds = service_account.Credentials.from_service_account_file(
                os.path.join(os.getcwd(), 'service_account.json'),
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            print(f"[CalendarTool] Service account email: {creds.service_account_email}", flush=True)
            service = build('calendar', 'v3', credentials=creds)
            print(f"[CalendarTool] Calendar ID: {calendar_id}", flush=True)
            print(f"[CalendarTool] Event to insert: {json.dumps(event, indent=2)}", flush=True)
            # Fetch events for the day (use UTC with Z)
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
            import pytz
            tz = pytz.timezone('Asia/Kolkata')
            new_start = tz.localize(datetime.datetime.strptime(f"{date} {start_time_fmt}", "%Y-%m-%d %H:%M"))
            new_end = tz.localize(datetime.datetime.strptime(f"{date} {end_time_fmt}", "%Y-%m-%d %H:%M"))
            for event_item in events:
                e_start = event_item['start'].get('dateTime', event_item['start'].get('date'))
                e_end = event_item['end'].get('dateTime', event_item['end'].get('date'))
                if 'T' in e_start:
                    e_start_dt = datetime.datetime.fromisoformat(e_start.replace('Z', '+00:00'))
                    if e_start_dt.tzinfo is None:
                        e_start_dt = tz.localize(e_start_dt)
                    else:
                        e_start_dt = e_start_dt.astimezone(tz)
                else:
                    e_start_dt = tz.localize(datetime.datetime.strptime(e_start, "%Y-%m-%d"))
                if 'T' in e_end:
                    e_end_dt = datetime.datetime.fromisoformat(e_end.replace('Z', '+00:00'))
                    if e_end_dt.tzinfo is None:
                        e_end_dt = tz.localize(e_end_dt)
                    else:
                        e_end_dt = e_end_dt.astimezone(tz)
                else:
                    e_end_dt = tz.localize(datetime.datetime.strptime(e_end, "%Y-%m-%d"))
                if not (new_end <= e_start_dt or new_start >= e_end_dt):
                    print("[CalendarTool] Slot conflict detected.", flush=True)
                    return f"Slot {start_time_fmt}-{end_time_fmt} on {date} is not free. Please choose another time."
            print(f"[CalendarTool] About to insert event: {json.dumps(event, indent=2)}", flush=True)
            event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
            print(f"[CalendarTool] Google API response: {json.dumps(event_result, indent=2)}", flush=True)
            return f"Event created: {title} from {start_time_fmt} to {end_time_fmt} on {date}"
        except Exception as e:
            print(f"[CalendarTool] Exception: {e}", flush=True)
            return f"Failed to add event: {e}"

calendar_tool = CalendarTool()
