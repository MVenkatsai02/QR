from db import Base, engine, SessionLocal
from models import Employee, QRToken
from qr_utils import generate_daily_qr
from datetime import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Add employees if none exist
if db.query(Employee).count() == 0:
    employees = [
        Employee(name="Alice", emp_code="EMP001"),
        Employee(name="Bob", emp_code="EMP002"),
        Employee(name="Charlie", emp_code="EMP003"),
        Employee(name="Diana", emp_code="EMP004"),
        Employee(name="Eve", emp_code="EMP005"),
    ]
    db.add_all(employees)
    db.commit()
    print("✅ Employees seeded")

# Generate today's QR
token, today, img_path = generate_daily_qr()
if not db.query(QRToken).filter(QRToken.valid_date == today).first():
    db.add(QRToken(token=token, valid_date=today))
    db.commit()
    print(f"✅ QR generated for {today}, saved at {img_path}")
