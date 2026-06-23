from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from twilio.rest import Client
from app.config import settings

router = APIRouter(prefix="/whatsapp-test", tags=["whatsapp-test"])


class WhatsappTestRequest(BaseModel):
    numbers: List[str]
    message: str


@router.post("/send")
def send_whatsapp(payload: WhatsappTestRequest):
    sid = settings.twilio_account_sid
    token = settings.twilio_auth_token
    from_whatsapp = settings.twilio_whatsapp_from

    if not sid or not token or not from_whatsapp:
        raise HTTPException(status_code=503, detail="Twilio credentials not configured in backend")

    client = Client(sid, token)

    results = []
    for number in payload.numbers:
        to_number = number
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        try:
            msg = client.messages.create(
                body=payload.message,
                from_=from_whatsapp,
                to=to_number,
            )
            results.append({"to": to_number, "sid": msg.sid})
        except Exception as exc:
            results.append({"to": to_number, "error": str(exc)})

    return {"message": "Requests sent", "results": results}
