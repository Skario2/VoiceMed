from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from models import Patient, PatientInfo, Base


def create_dummy_data(new_session):
    patients = [
        Patient(name="Alice Johnson", insurance_card_id="IC123456", date_of_birth=date(1990, 5, 1)),
        Patient(name="Bob Smith", insurance_card_id="IC654321", date_of_birth=date(1985, 8, 15)),
        Patient(name="Charlie Davis", insurance_card_id="IC987654", date_of_birth=date(1992, 3, 22)),
    ]
    new_session.add_all(patients)
    new_session.commit()

    patient_infos = [
        PatientInfo(patient_id=patients[0].patient_id, type="Allergy", info="Peanuts"),
        PatientInfo(patient_id=patients[0].patient_id, type="Medication", info="Aspirin"),
        PatientInfo(patient_id=patients[1].patient_id, type="Diagnosis", info="Diabetes"),
        PatientInfo(patient_id=patients[2].patient_id, type="Surgery", info="Appendectomy in 2015"),
    ]
    new_session.add_all(patient_infos)
    new_session.commit()


# Setup database and session
engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Create dummy data
create_dummy_data(session)
