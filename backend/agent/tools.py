from memory.db_store import SessionLocal, Appointment, Doctor
from datetime import datetime

def check_availability(doctor_specialty: str, date: str, time: str) -> str:
    """Checks if a doctor is available at a given date and time. Date should be YYYY-MM-DD and time HH:MM"""
    db = SessionLocal()
    doctor = db.query(Doctor).filter(Doctor.specialty.ilike(f"%{doctor_specialty}%")).first()
    if not doctor:
        db.close()
        return "No doctor found with that specialty."
    
    doc_name = doctor.name
    doc_id = doctor.id
    
    # Check if time is in the past
    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        if dt < datetime.now():
            db.close()
            return "Cannot book an appointment in the past."
    except Exception:
        pass
        
    appt = db.query(Appointment).filter(
        Appointment.doctor_id == doc_id, 
        Appointment.date == date, 
        Appointment.time == time,
        Appointment.status == "booked"
    ).first()
    
    db.close()
    
    if appt:
        return "Doctor is already booked at that time. Available alternative slots are 10:00, 14:00, and 16:30."
    return f"Doctor {doc_name} is available at {date} {time}."

def book_appointment(patient_id: int, doctor_specialty: str, date: str, time: str) -> str:
    db = SessionLocal()
    doctor = db.query(Doctor).filter(Doctor.specialty.ilike(f"%{doctor_specialty}%")).first()
    if not doctor:
        db.close()
        return "No doctor found with that specialty."
        
    doc_name = doctor.name
    doc_id = doctor.id
        
    # Prevent double booking
    appt = db.query(Appointment).filter(
        Appointment.doctor_id == doc_id, 
        Appointment.date == date, 
        Appointment.time == time,
        Appointment.status == "booked"
    ).first()
    if appt:
        db.close()
        return "Conflict: Slot already booked. Available alternative slots are 10:00, 14:00, and 16:30."
        
    new_appt = Appointment(patient_id=patient_id, doctor_id=doc_id, date=date, time=time, status="booked")
    db.add(new_appt)
    db.commit()
    db.close()
    return f"Appointment booked successfully with {doc_name} on {date} at {time}."

def cancel_appointment(patient_id: int, date: str, time: str) -> str:
    db = SessionLocal()
    appt = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.date == date,
        Appointment.time == time,
        Appointment.status == "booked"
    ).first()
    if appt:
        appt.status = "cancelled"
        db.commit()
        db.close()
        return "Appointment cancelled successfully."
    db.close()
    return "No booked appointment found for that date and time."

def reschedule_appointment(patient_id: int, old_date: str, old_time: str, new_date: str, new_time: str) -> str:
    db = SessionLocal()
    appt = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.date == old_date,
        Appointment.time == old_time,
        Appointment.status == "booked"
    ).first()
    if not appt:
        db.close()
        return "Original appointment not found."
        
    # Check new availability
    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == appt.doctor_id,
        Appointment.date == new_date,
        Appointment.time == new_time,
        Appointment.status == "booked"
    ).first()
    
    if conflict:
        db.close()
        return "Conflict: New slot already booked. Available alternative slots are 10:00, 14:00, and 16:30."
        
    appt.date = new_date
    appt.time = new_time
    db.commit()
    db.close()
    return f"Appointment successfully rescheduled to {new_date} at {new_time}."

TOOLS_LIST = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Checks if a doctor is available at a given date and time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_specialty": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "time": {"type": "string", "description": "HH:MM"}
                },
                "required": ["doctor_specialty", "date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Books an appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_specialty": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "time": {"type": "string", "description": "HH:MM"}
                },
                "required": ["doctor_specialty", "date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancels an appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "time": {"type": "string", "description": "HH:MM"}
                },
                "required": ["date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": "Reschedules an appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_date": {"type": "string"},
                    "old_time": {"type": "string"},
                    "new_date": {"type": "string"},
                    "new_time": {"type": "string"}
                },
                "required": ["old_date", "old_time", "new_date", "new_time"]
            }
        }
    }
]

def execute_tool(name: str, args: dict, patient_id: int) -> str:
    if name == "check_availability":
        return check_availability(args["doctor_specialty"], args["date"], args["time"])
    elif name == "book_appointment":
        return book_appointment(patient_id, args["doctor_specialty"], args["date"], args["time"])
    elif name == "cancel_appointment":
        return cancel_appointment(patient_id, args["date"], args["time"])
    elif name == "reschedule_appointment":
        return reschedule_appointment(patient_id, args["old_date"], args["old_time"], args["new_date"], args["new_time"])
    return "Unknown tool"
