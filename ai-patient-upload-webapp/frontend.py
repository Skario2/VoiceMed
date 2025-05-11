from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='static')

@app.route('/frontend', defaults={'path': ''})
@app.route('/frontend/<path:path>')
def serve_frontend(path):
    if path.startswith("static/"):
        return send_from_directory('static', path[7:])  # strip "static/"
    return send_from_directory('.', 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True, port=3000)