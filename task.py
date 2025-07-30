
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes=["https://www.googleapis.com/auth/calendar"])
creds = flow.run_local_server(port=0)

# Save token
import pickle
with open("token.pkl", "wb") as f:
    pickle.dump(creds, f)
