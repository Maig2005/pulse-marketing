from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database import SessionLocal, engine
from models import Base, Event, Campaign

# ── Create tables ──────────────────────────────────────────────────────────────

app = FastAPI(title="Pulse Marketing API")
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "Pulse API Live"}

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB dependency ──────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ══════════════════════════════════════════════════════════════════════════════
# EMAIL CONFIG  ← fill these in once, everything works automatically
# ══════════════════════════════════════════════════════════════════════════════
import os

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("mainakg2005@gmail.com")
SMTP_PASSWORD = os.getenv("yyyb nnei hsnt zazi")
SENDER_NAME = "Pulse Marketing"

# ── In-memory OTP store  { email: { "otp": "1234", "expires": timestamp } } ──
_otp_store: dict = {}
OTP_TTL = 300   # seconds (5 minutes)


# ── Pydantic schemas ───────────────────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _send_otp_email(to_email: str, otp: str, purpose: str = "verification"):
    """Send a styled OTP email via Gmail SMTP."""

    subject = f"Your Pulse {purpose} code: {otp}"

    html = f"""
    <div style="background:#0b0d12;padding:40px 20px;font-family:'Segoe UI',sans-serif;">
      <div style="max-width:420px;margin:0 auto;background:#11141b;border:1px solid #1f2430;
                  border-radius:16px;padding:36px 32px;">

        <!-- Logo -->
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:28px;">
          <div style="width:32px;height:32px;border-radius:8px;background:#10b981;
                      display:flex;align-items:center;justify-content:center;">
            <span style="font-weight:800;font-size:14px;color:#04130c;">P</span>
          </div>
          <span style="font-weight:600;font-size:16px;color:#e6e9ef;">Pulse</span>
          <span style="font-size:11px;padding:2px 8px;border-radius:6px;
                       background:#161a23;border:1px solid #1f2430;color:#8a93a6;">
            Marketing
          </span>
        </div>

        <h2 style="color:#e6e9ef;font-size:20px;font-weight:600;
                   letter-spacing:-0.02em;margin:0 0 8px;">
          Your {purpose} code
        </h2>
        <p style="color:#8a93a6;font-size:13px;margin:0 0 28px;line-height:1.6;">
          Use the code below to complete your {purpose}. 
          It expires in <strong style="color:#e6e9ef;">5 minutes</strong>.
        </p>

        <!-- OTP Box -->
        <div style="background:#161a23;border:1px solid #1f2430;border-radius:12px;
                    padding:24px;text-align:center;margin-bottom:24px;">
          <div style="font-family:'Courier New',monospace;font-size:36px;font-weight:700;
                      letter-spacing:0.18em;color:#10b981;">
            {otp}
          </div>
        </div>

        <p style="color:#8a93a6;font-size:12px;line-height:1.6;margin:0;">
          If you didn't request this, you can safely ignore this email.<br/>
          Never share this code with anyone.
        </p>

        <div style="margin-top:28px;padding-top:20px;border-top:1px solid #1f2430;">
          <p style="color:#4b5563;font-size:11px;margin:0;">
            Pulse Marketing Platform · Sent automatically
          </p>
        </div>
      </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())


# ══════════════════════════════════════════════════════════════════════════════
# OTP ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/send-otp")
def send_otp(payload: OTPRequest):
    """Generate a 6-digit OTP, store it, and email it to the user."""
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")

    otp = str(random.randint(100000, 999999))
    _otp_store[email] = {"otp": otp, "expires": time.time() + OTP_TTL}

    try:
        _send_otp_email(email, otp)
    except Exception as e:
        # Surface the error clearly so you can fix SMTP config
        raise HTTPException(
            status_code=500,
            detail=f"Email delivery failed: {str(e)}. Check SMTP_USER / SMTP_PASSWORD in main.py."
        )

    return {"status": "sent", "message": f"OTP sent to {email}"}


@app.post("/verify-otp")
def verify_otp(payload: OTPVerify):
    """Validate the OTP submitted by the user."""
    email = payload.email.strip().lower()
    record = _otp_store.get(email)

    if not record:
        raise HTTPException(status_code=400, detail="No OTP found for this email. Please request a new one.")

    if time.time() > record["expires"]:
        del _otp_store[email]
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

    if payload.otp.strip() != record["otp"]:
        raise HTTPException(status_code=400, detail="Incorrect OTP. Please try again.")

    # Valid — remove from store so it can't be reused
    del _otp_store[email]
    return {"status": "verified"}


# ══════════════════════════════════════════════════════════════════════════════
# TRACKING
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
# DECISION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/decision/{session_id}")
def get_decision(session_id: str, db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.session_id == session_id).all()
    total  = len(events)
    clicks = sum(1 for e in events if e.event_type == "click")
    cta    = sum(1 for e in events if e.event_type == "cta_click")

    if cta > 0:
        return {"action": "no_action", "message": ""}

    if clicks >= 5:
        offers = [
            "🎉 You've been active! Get 20% off your next campaign boost.",
            "🚀 Exclusive deal: Double your ad reach for free this week.",
            "💡 Upgrade to Pro and unlock AI-powered budget suggestions.",
        ]
        return {"action": "show_offer", "message": random.choice(offers)}

    if total >= 2:
        return {"action": "show_chatbot", "message": ""}

    return {"action": "no_action", "message": ""}


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    all_events = db.query(Event).all()
    return {
        "total_events": len(all_events),
        "clicks":       sum(1 for e in all_events if e.event_type == "click"),
        "page_views":   sum(1 for e in all_events if e.event_type == "page_view"),
        "cta_clicks":   sum(1 for e in all_events if e.event_type == "cta_click"),
        "sessions":     len(set(e.session_id for e in all_events if e.session_id)),
    }


# ══════════════════════════════════════════════════════════════════════════════
# CAMPAIGNS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(Campaign).all()


@app.post("/campaign", status_code=201)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    campaign = Campaign(name=payload.name, budget=payload.budget,
                        status="active", clicks=0, conversions=0)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@app.put("/campaign/{campaign_id}")
def update_campaign(campaign_id: int, payload: CampaignUpdate,
                    db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if payload.name is not None:
        campaign.name = payload.name
    if payload.budget is not None:
        campaign.budget = payload.budget
    db.commit()
    db.refresh(campaign)
    return campaign


@app.delete("/campaign/{campaign_id}")
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    db.delete(campaign)
    db.commit()
    return {"status": "deleted", "id": campaign_id}


# ══════════════════════════════════════════════════════════════════════════════
# AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/campaign-insights")
def campaign_insights(db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).all()
    insights  = []

    if not campaigns:
        insights.append("No campaigns yet. Create your first campaign to start tracking performance.")
        return {"insights": insights}

    total_budget      = sum(c.budget for c in campaigns)
    total_clicks      = sum(c.clicks for c in campaigns)
    total_conversions = sum(c.conversions for c in campaigns)

    best = max(campaigns, key=lambda c: c.clicks)
    if best.clicks > 0:
        insights.append(
            f"🏆 <b>{best.name}</b> is your top performer with {best.clicks} clicks. "
            "Consider increasing its budget allocation.")

    low = [c for c in campaigns if c.clicks < 5]
    if low:
        insights.append(
            f"⚠️ Low engagement on: <b>{', '.join(c.name for c in low)}</b>. "
            "Review targeting or creatives.")

    if total_clicks > 0:
        cr = (total_conversions / total_clicks) * 100
        if cr < 2:
            insights.append(
                f"📉 Conversion rate <b>{cr:.1f}%</b> is below the 2% benchmark. "
                "A/B test landing pages.")
        else:
            insights.append(
                f"✅ Conversion rate is healthy at <b>{cr:.1f}%</b>. Scale top channels.")

    insights.append(
        f"💰 Total active budget: <b>₹{total_budget:,.0f}</b> across {len(campaigns)} campaign(s).")

    return {"insights": insights}


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)