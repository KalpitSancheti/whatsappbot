import os
from twilio.rest import Client
from pymongo import MongoClient
from dotenv import load_dotenv

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

# MongoDB utility
load_dotenv()
MONGODB_URI = os.environ.get("MONGODB_URI")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "whatsappbot")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "ratings")

_mongo_client = None

def get_mongo_collection():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGODB_URI)
    db = _mongo_client[MONGO_DB_NAME]
    return db[MONGO_COLLECTION]

def get_ratings():
    col = get_mongo_collection()
    doc = col.find_one({"_id": "ratings"})
    return doc["data"] if doc and "data" in doc else {}

def set_ratings(ratings_dict):
    col = get_mongo_collection()
    col.update_one({"_id": "ratings"}, {"$set": {"data": ratings_dict}}, upsert=True)
