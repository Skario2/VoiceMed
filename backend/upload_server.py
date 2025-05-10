import os
from datetime import datetime
import threading

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.patients.config import DATABASE_URL

from backend.ocr.OpenAIServer import OpenAIServer
from db.patients.models import Base, PatientInfo, Patient

app = Flask(__name__)

rest_dir = os.path.dirname(__file__)

'''
What we want is 
{
hash: {state: (authenticated | voice_done | uploading), uploaded_id: id}
}
'''

connected_patients = {}

def save_to_db(patient_id: int, type: str, priority: int, content: str, date: datetime) -> None:
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    new_session = sessionmaker(bind=engine)
    session = new_session()
    session.add(PatientInfo(patient_id=patient_id, type=type, content=content, date=date, priority=priority))
    session.commit()

@app.route("/api/start", methods=["GET"])
def start():
    id = request.args.get("id")
    return jsonify({"url": "http://localhost:8080/?id=" + id})

@app.route("/api/info", methods=["PUT"])
def save_info():
    json_data = request.get_json(force=True)
    database_format = {"type": json_data["type"], "priority": json_data["priority"],
                       "content": json_data["content"], "date": json_data["date"]}
    try:
        save_to_db(**database_format)
        return jsonify({"message": "Saved data in the database"}), 200
    except Exception:
        return jsonify({"error": "Cannot save the data in the database"}), 400

@app.route("/api/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if file:
        try:
            image_bytes = file.read()
            openai_server = OpenAIServer.new_server()
            output = openai_server.extract_from_image(image_bytes)
            if output['status'] == 'good':
                # todo: inform agent that it's good
                return jsonify({"status": "good"}), 200
            if output['status'] == 'bad':
                # todo: inform agent that it's bad
                return jsonify({"status": "bad"}), 400
            if output['status'] == 'unclear':
                # todo: inform agent that it's bad
                return jsonify({"status": "unclear"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/id", methods=["GET"])
def get_id():
    name = request.args.get("name")
    birthdate = request.args.get("birthdate")
    insurance_id = request.args.get("insurance_id")
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    new_session = sessionmaker(bind=engine)
    session = new_session()
    patients = (session.query(Patient).filter(Patient.name == name).filter(Patient.date_of_birth == birthdate)
     .filter(Patient.insurance_card_id == insurance_id).all())
    assert len(patients) == 1

    return {"id": patients[0].patient_id}, 200
