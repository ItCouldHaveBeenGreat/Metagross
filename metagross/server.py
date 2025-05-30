from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)


@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200


@app.route("/guess", methods=["POST"])
def guess():
    if request.is_json:
        data = request.get_json()
        print("Received JSON:", json.dumps(data))
        # Process the JSON data here
        response_data = {"received": data, "message": "JSON processed successfully"}
        return jsonify(response_data), 200
    else:
        return jsonify({"error": "Request must be JSON"}), 400

    # First, we need to take the state log and parse it into an incomplete game state

    # Second, we need to run simulations on the incomplete game state. Complete game states
    # will be produced from the incomplete by adding filler data and making guesses.
    # TODO: Each simulation should emit a log of the events that happened. The logs should be
    #       collected and visualized into a branching probability tree for debugging!

    # Finally, return the options available annotated by their win probability


if __name__ == "__main__":
    app.run(debug=True)
