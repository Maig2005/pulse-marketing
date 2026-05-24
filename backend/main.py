from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import random
import time
import os
import requests

from database import SessionLocal, engine
from models import Base, Event, Campaign

# ── App Init ─────────────────────────────────────────────
app = FastAPI(title="Pulse Marketing API")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("✅ DB LOADED SUCCESSFULLY")

@app.get("/")
def root():
    return {"status": "Pulse API Live"}

# ── CORS ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB ─────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── EMAIL CONFIG (RESEND) ─────────────────────────────
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

if not RESEND_API_KEY:
    print("❌ RESEND API KEY NOT LOADED")
else:
    print("✅ RESEND API LOADED")

# ── OTP STORE ─────────────────────────────────────────
_otp_store = {}
OTP_TTL = 300  # 5 minutes

# ── SCHEMAS ───────────────────────────────────────────
class TrackPayload(BaseModel):
    event_type: str
    timestamp: str
    page: str
    session_id: str

class CampaignCreate(BaseModel):
    name: str
    budget: float

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    budget: Optional[float] = None

class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str

# ─────────────────────────────────────────────────────
# EMAIL FUNCTION (RESEND)
# ─────────────────────────────────────────────────────
def _send_otp_email(to_email: str, otp: str):
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": "Pulse <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Pulse OTP Verification",
            "html": f"<h2>Your OTP is: {otp}</h2>"
        }
    )

    if response.status_code != 200:
        print("❌ EMAIL ERROR:", response.text)
        raise Exception(response.text)

    print("✅ EMAIL SENT")

# ─────────────────────────────────────────────────────
# OTP SEND
# ─────────────────────────────────────────────────────
@app.post("/send-otp")
def send_otp(payload: OTPRequest):
    email = payload.email.strip().lower()

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    otp = str(random.randint(100000, 999999))

    _otp_store[email] = {
        "otp": otp,
        "expires": time.time() + OTP_TTL
    }

    print("📦 OTP STORED:", email, otp)

    try:
        _send_otp_email(email, otp)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email delivery failed: {str(e)}"
        )

    return {"status": "sent"}

# ─────────────────────────────────────────────────────
# OTP VERIFY
# ─────────────────────────────────────────────────────
@app.post("/verify-otp")
def verify_otp(payload: OTPVerify):
    email = payload.email.strip().lower()
    record = _otp_store.get(email)

    print("🔍 VERIFYING:", email)
    print("📦 STORED:", record)
    print("✏️ ENTERED:", payload.otp)

    if not record:
        raise HTTPException(status_code=400, detail="No OTP found")

    if time.time() > record["expires"]:
        del _otp_store[email]
        raise HTTPException(status_code=400, detail="OTP expired")

    if payload.otp.strip() != record["otp"]:
        raise HTTPException(status_code=400, detail="Incorrect OTP")

    del _otp_store[email]

    return {"status": "verified"}

# ─────────────────────────────────────────────────────
# TRACKING
# ─────────────────────────────────────────────────────
@app.post("/track")
def track_event(payload: TrackPayload, db: Session = Depends(get_db)):
    event = Event(
        event_type=payload.event_type,
        page=payload.page,
        timestamp=str(payload.timestamp),
        session_id=payload.session_id,
    )
    db.add(event)
    db.commit()
    return {"status": "ok"}

# ─────────────────────────────────────────────────────
# DECISION ENGINE
# ─────────────────────────────────────────────────────
@app.get("/decision/{session_id}")
def get_decision(session_id: str):
    return {
        "action": "show_offer",
        "message": "Grab this exclusive deal just for you!"
    }

# ─────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────
@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    return {
        "total_events": len(events),
        "clicks": sum(1 for e in events if e.event_type == "click"),
        "page_views": sum(1 for e in events if e.event_type == "page_view"),
    }

# ─────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)