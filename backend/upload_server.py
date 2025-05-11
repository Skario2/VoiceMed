import base64
import hashlib
import hmac
import os
import random
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


def save_to_db(patient_id: int, type: str, priority: int, content: str, date: datetime | str) -> None:
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    new_session = sessionmaker(bind=engine)
    session = new_session()
    session.add(PatientInfo(patient_id=patient_id, type=type, content=content, date=date, priority=priority))
    session.commit()


@app.route("/api/info", methods=["PUT"])
def save_info():
    database_format = request.get_json(force=True)
    try:
        for db_format in database_format:
            save_to_db(**db_format)
        return jsonify({"message": "Saved data in the database"}), 200
    except Exception:
        return jsonify({"error": "Cannot save the data in the database"}), 400


@app.route("/api/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    patient_id = request.args.get("patient_id")
    lock.acquire()
    if patient_id not in connected_patients:
        lock.release()
        return jsonify({"status": "bad"}), 400
    connected_patients[patient_id]["lock"].acquire()
    lock.release()

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if file:
        try:
            image_bytes = file.read()
            openai_server = OpenAIServer.new_server()
            output = openai_server.extract_from_image(image_bytes)
            connected_patients[patient_id]["last_uploaded"] = {
                "id": 0 if len(connected_patients[patient_id]["last_uploaded"]) == 0 else
                connected_patients[patient_id]["last_uploaded"]["id"] + 1,
                "status": output["status"],
                "content": output["content"]
            }
            connected_patients[patient_id]["lock"].release()
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            connected_patients[patient_id]["lock"].release()
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid file type"}), 400


@app.route("/api/id", methods=["GET"])
def get_id():
    name = request.args.get("name")
    birthdate = request.args.get("birthday")
    insurance_id = request.args.get("insurance_id")
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    new_session = sessionmaker(bind=engine)
    session = new_session()
    patients = (session.query(Patient).filter(Patient.name == name).filter(Patient.date_of_birth == birthdate)
                .filter(Patient.insurance_card_id == insurance_id).all())
    assert len(patients) <= 1
    is_new = len(patients) == 0
    if is_new:
        with new_session() as session:
            session.add(Patient(name=name, date_of_birth=datetime.strptime(birthdate, '%Y-%m-%d').date(),
                                insurance_card_id=insurance_id))
            session.commit()
    session = new_session()
    patients = (session.query(Patient).filter(Patient.name == name).filter(Patient.date_of_birth == birthdate)
                .filter(Patient.insurance_card_id == insurance_id).all())
    hash_digest = hmac.new(__SECRET_KEY__, f"{__c:03}".encode(), hashlib.sha256).digest()
    patient_id = base64.urlsafe_b64encode(hash_digest).decode().rstrip("=")
    lock.acquire()
    connected_patients[patient_id] = {"patient": patients[0].patient_id,
                                      "state": "authenticated",
                                      "last_uploaded": {},
                                      "lock": threading.Lock()}
    lock.release()
    return {'id': patient_id, 'is_new': is_new}, 200


@app.route("/api/info", methods=["POST", "PUT"])
def put_info():
    patient_id = request.args.get("patient_id")
    if patient_id is None:
        return jsonify({"error": "Missing patient_id"}), 400

    if patient_id not in connected_patients:
        return jsonify({"error": "Unknown patient_id"}), 404
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    new_session = sessionmaker(bind=engine)
    data_structure = request.get_json(force=True)
    lock.acquire()
    try:
        connected_patients[patient_id]["lock"].acquire()
        connected_patients[patient_id]["state"] = "voice_done"
    except Exception:
        connected_patients[patient_id]["lock"].release()
        return jsonify({"error": "Cannot save the data in the database"}), 400
    finally:
        lock.release()
    patient_actual_id = connected_patients[patient_id]["patient"]
    connected_patients[patient_id]["lock"].release()
    for info in data_structure:
        with new_session() as session:
            print(3)
            session.add(PatientInfo(patient_id=patient_actual_id, **info))
            print(4)
            session.commit()
    return jsonify({"status": "ok"}), 200

@app.route("/api/start-upload", methods=["PUT"])
def start_upload():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return jsonify({"error": "Missing patient_id"}), 400
    if patient_id not in connected_patients:
        return jsonify({"error": "Unknown patient_id"}), 404
    lock.acquire()
    try:
        connected_patients[patient_id]["state"] = "uploading"
        upload_link = f"http://localhost:3000/frontend/{patient_id}"
        connected_patients[patient_id]["last_uploaded"]["link"] = upload_link
    finally:
        lock.release()
    return jsonify({"link": upload_link}), 200

@app.route("/api/upload-stats", methods=["GET"])
def upload_stats():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return jsonify({"error": "Missing patient_id"}), 400

    lock.acquire()
    if patient_id not in connected_patients:
        lock.release()
        return jsonify({"error": "Unknown patient_id"}), 404

    try:
        status = connected_patients[patient_id]["last_uploaded"]["status"]
    finally:
        lock.release()
    return jsonify({"status": status}), 200


@app.route("/api/content", methods=["PUT"])
def upload_content():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return jsonify({"error": "Missing patient_id"}), 400

    lock.acquire()
    if patient_id not in connected_patients:
        lock.release()
        return jsonify({"error": "Unknown patient_id"}), 404
    lock.release()
    try:
        connected_patients[patient_id]["last_uploaded"]["structured_data"] = request.get_json(force=True)
        status = connected_patients[patient_id]["last_uploaded"]["status"]
    finally:
        lock.release()
    return jsonify({"status": status}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
