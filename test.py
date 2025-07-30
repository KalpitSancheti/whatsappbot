from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACC_FILE = 'service_account.json'
CAL_ID = 'kalpitjain3@gmail.com'  # your calendar

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACC_FILE, scopes=SCOPES)
svc = build('calendar', 'v3', credentials=creds)

# Test insert
event = {
    'summary': 'Test SA Event',
    'start': {'dateTime': '2025-08-01T10:00:00+05:30'},
    'end':   {'dateTime': '2025-08-01T11:00:00+05:30'},
}
created = svc.events().insert(calendarId=CAL_ID, body=event).execute()
print("Created:", created.get('id'))
