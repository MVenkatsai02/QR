from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    emp_code = Column(String, unique=True, nullable=False)

    attendance = relationship("Attendance", back_populates="employee")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    check_type = Column(String)  # IN or OUT
    timestamp = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="attendance")

class QRToken(Base):
    __tablename__ = "qr_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    valid_date = Column(String, nullable=False)  # YYYY-MM-DD
