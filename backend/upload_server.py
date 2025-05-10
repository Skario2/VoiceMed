import os
from datetime import datetime

from flask import Flask, jsonify, request

from backend.ocr.OpenAIServer import OpenAIServer

app = Flask(__name__)

rest_dir = os.path.dirname(__file__)

# todo: add this if possible __key_map__ = {}

def save_to_db(type: str, priority: int, content: str, date: datetime) -> None:
    pass

@app.route("/api/start", methods=["GET"])
def start():
    id = request.args.get("id")
    return jsonify({"url": "http://localhost:8080/?id=" + id})

@app.route("/api/save", methods=["PUT"])
def save():
    json_data = request.get_json(force=True)
    database_format = {"type": json_data["type"], "proirity": json_data["proirity"],
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
