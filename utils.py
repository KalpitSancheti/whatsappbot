import os
from twilio.rest import Client

# Twilio config (set these as environment variables in deployment)
TWILIO_SID = os.environ.get("TWILIO_SID", "your_twilio_sid")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN", "your_twilio_token")
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'
TO_WHATSAPP = os.environ.get("TO_WHATSAPP", "whatsapp:+919873358502")  # Set your WhatsApp number or manage a list

client = Client(TWILIO_SID, TWILIO_TOKEN)

def send_whatsapp(msg, to=TO_WHATSAPP):
    client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        body=msg,
        to=to
    )
