from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)


@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200


@app.route('/guess', methods=['POST'])
def guess():
    if request.is_json:
        data = request.get_json()
        print("Received JSON:", json.dumps(data))
        # Process the JSON data here
        response_data = {
            "received": data,
            "message": "JSON processed successfully"
        }
        return jsonify(response_data), 200
    else:
        return jsonify({"error": "Request must be JSON"}), 400


if __name__ == '__main__':
    app.run(debug=True)
