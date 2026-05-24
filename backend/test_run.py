print("STARTING...")

from fastapi import FastAPI
print("FastAPI imported")

from database import SessionLocal, Base, engine
print("Database imported")

from models import Event, Campaign
print("Models imported")

app = FastAPI()

print("App created")

@app.get("/")
def test():
    return {"status": "working"}

print("END OF FILE")