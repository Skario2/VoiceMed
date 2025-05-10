from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Patient(Base):
    __tablename__ = 'patient'
    patient_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    insurance_card_id = Column(String(25), nullable=False, unique=True)
    date_of_birth = Column(Date, nullable=False)

class PatientInfo(Base):
    __tablename__ = 'patientinfo'
    info_id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patient.patient_id'))
    type = Column(String(100), nullable=False)
    content = Column(String(1000), nullable=False)
    date = Column(Date)
    priority = Column(Integer)
