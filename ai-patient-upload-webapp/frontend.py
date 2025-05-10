from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='static')

@app.route('/frontend')
def serve_frontend():
    return send_from_directory('static', 'static/index.html')

if __name__ == '__main__':
    app.run(debug=True, port=3000)