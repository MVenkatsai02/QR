from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os

from db import Base, engine, SessionLocal
import models
from models import Employee, Attendance, QRToken
from qr_utils import generate_daily_qr

# Init DB
Base.metadata.create_all(bind=engine)

app = FastAPI(title="QR Attendance Demo")

# Static + Templates
app.mount("/qrcodes", StaticFiles(directory="qrcodes"), name="qrcodes")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if not db.query(QRToken).filter(QRToken.valid_date == today).first():
        token, today, img_path = generate_daily_qr()
        db.add(QRToken(token=token, valid_date=today))
        db.commit()
    db.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    qr_file = f"qrcodes/qr_{today}.png"

    employees = db.query(Employee).all()
    logs = db.query(Attendance).all()

    status_map = {}
    for emp in employees:
        emp_logs = [log for log in logs if log.employee_id == emp.id]
        status_map[emp.id] = {
            "in": next((log.timestamp.strftime("%H:%M") for log in emp_logs if log.check_type == "IN"), "-"),
            "out": next((log.timestamp.strftime("%H:%M") for log in emp_logs if log.check_type == "OUT"), "-"),
        }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "qr_file": qr_file if os.path.exists(qr_file) else None,
        "employees": employees,
        "status_map": status_map
    })

@app.post("/attendance/checkin/{emp_id}")
def checkin(emp_id: int, token: str, db: Session = Depends(get_db)):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    qr = db.query(QRToken).filter(QRToken.valid_date == today).first()
    if not qr or qr.token != token:
        raise HTTPException(status_code=400, detail="Invalid or expired QR")
    record = Attendance(employee_id=emp_id, check_type="IN")
    db.add(record)
    db.commit()
    return {"message": "Check-in recorded"}

@app.post("/attendance/checkout/{emp_id}")
def checkout(emp_id: int, token: str, db: Session = Depends(get_db)):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    qr = db.query(QRToken).filter(QRToken.valid_date == today).first()
    if not qr or qr.token != token:
        raise HTTPException(status_code=400, detail="Invalid or expired QR")
    record = Attendance(employee_id=emp_id, check_type="OUT")
    db.add(record)
    db.commit()
    return {"message": "Check-out recorded"}
