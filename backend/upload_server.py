import os

from flask import Flask, jsonify, request

from backend.ocr.OpenAIServer import OpenAIServer

app = Flask(__name__)

rest_dir = os.path.dirname(__file__)

# todo: add this if possible __key_map__ = {}

@app.route("/api/start", methods=["GET"])
def start():
    id = request.args.get("id")
    return jsonify({"url": "http://localhost:8080/?id=" + id})

@app.route("/api/save", methods=["PUT"])
def save():
    json_data = request.get_json(force=True)
    # todo: store the data depending on the cases in the database
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if file:
        try:
            if file:
                    pass
                    # todo: Complete this
            return jsonify({"id": 1}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if file:
        data = file.read()
        server = OpenAIServer.new_server()
        server.extract_from_image(file)
        return jsonify({"id": 1}), 200
    return jsonify({"error": "Invalid file type"}), 400