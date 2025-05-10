import base64
import hashlib
import hmac
import os
import secrets
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

__SECRET_KEY__ = bytes(secrets.token_hex(32), 'utf-8')
__c = 0


'''
What we want is 
{
hash: {patient:id, state: (authenticated | voice_done | uploading), last_uploaded: {id, status, structured_data}}...
}
'''

connected_patients = {}
lock = threading.Lock()

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
    print(1)
    birthdate = request.args.get("birthdate")
    print(2)
    insurance_id = request.args.get("insurance_id")
    print(3)
    engine = create_engine(DATABASE_URL, echo=True)
    print(4)
    Base.metadata.create_all(engine)
    print(5)
    new_session = sessionmaker(bind=engine)
    print(6)
    session = new_session()
    print(7)
    patients = (session.query(Patient).filter(Patient.name == name).filter(Patient.date_of_birth == birthdate)
     .filter(Patient.insurance_card_id == insurance_id).all())
    print(8)
    assert len(patients) == 1
    hash_digest = hmac.new(__SECRET_KEY__, f"{__c:03}".encode(), hashlib.sha256).digest()
    print(9)
    patient_id = base64.urlsafe_b64encode(hash_digest).decode().rstrip("=")
    print(10)
    lock.acquire()
    print(11)
    connected_patients[patient_id] = {"patient": patients[0].patient_id, "state": "authenticated", "last_uploaded_id": -1}
    print(12)
    lock.release()
    print(patient_id)
    return {'id': patient_id}, 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)