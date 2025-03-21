import os
import requests
from fastapi import APIRouter, Request, Query, BackgroundTasks
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
META_API_URL = f"https://graph.facebook.com/v16.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "Verification failed"}, 403

@router.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    form_data = await request.json()
    for change in form_data.get("entry", [{}])[0].get("changes", []):
        message_data = change.get("value", {}).get("messages", [{}])[0]
        sender_number = message_data.get("from", "").strip()
        message_text = message_data.get("text", {}).get("body", "").strip()
        if sender_number == WHATSAPP_PHONE_NUMBER_ID or not sender_number:
            continue
        background_tasks.add_task(process_message, sender_number, message_text)
    return {"status": "success"}

def process_message(sender_number, message_text):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        # Here you would integrate with your agent – for example, call the EC2 agent HTTP endpoint
        response_text = f"Processed message: {message_text}"  # placeholder logic
        chunk_size = 1500
        chunks = [response_text[i : i + chunk_size] for i in range(0, len(response_text), chunk_size)]
        for chunk in chunks:
            payload = {
                "messaging_product": "whatsapp",
                "to": sender_number,
                "text": {"body": chunk.strip()}
            }
            requests.post(META_API_URL, headers=headers, json=payload)
    except Exception as e:
        error_payload = {
            "messaging_product": "whatsapp",
            "to": sender_number,
            "text": {"body": f"❌ Error: {str(e)}"}
        }
        requests.post(META_API_URL, headers=headers, json=error_payload)
