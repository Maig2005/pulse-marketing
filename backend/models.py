from sqlalchemy import Column, Integer, String, Float
from database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)
    page = Column(String)
    timestamp = Column(String)
    session_id = Column(String)


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    budget = Column(Float)
    status = Column(String, default="Active")
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String)
    address = Column(String)
    gender = Column(String)