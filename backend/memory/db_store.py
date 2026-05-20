import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    preferred_language = Column(String) # e.g. English, Hindi, Tamil
    past_history = Column(String)

class Doctor(Base):
    __tablename__ = 'doctors'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    specialty = Column(String)

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer)
    doctor_id = Column(Integer)
    date = Column(String) # For simplicity: YYYY-MM-DD
    time = Column(String) # For simplicity: HH:MM
    status = Column(String) # booked, cancelled, rescheduled

DB_URL = "sqlite:///./appointments.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Seed some data if empty
    db = SessionLocal()
    if not db.query(Doctor).first():
        db.add(Doctor(name="Dr. Sharma", specialty="Cardiologist"))
        db.add(Doctor(name="Dr. Gupta", specialty="Dermatologist"))
        db.commit()
    if not db.query(Patient).first():
        db.add(Patient(name="Rahul", preferred_language="Hindi", past_history="Asthma"))
        db.commit()
    db.close()
