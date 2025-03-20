import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

DATA_FILE = "groceries.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_next_id(data):
    if not data:
        return 1
    return max(entry["id"] for entry in data) + 1

@app.route('/groceries', methods=['GET'])
def get_all_groceries():
    data = load_data()
    return jsonify(data), 200

@app.route('/groceries', methods=['POST'])
def add_grocery():
    data = load_data()
    req = request.get_json()

    # In case the user doesn't pass "unit", we can default to "units" or "grams"
    new_entry = {
        "id": get_next_id(data),
        "item": req["item"],
        "quantity": req["quantity"],
        # NEW: add "unit" field (default to "units" if not given)
        "unit": req.get("unit", "units")
    }
    data.append(new_entry)
    save_data(data)

    return jsonify({"message": "Grocery added"}), 201

@app.route('/groceries/<int:grocery_id>', methods=['PUT'])
def edit_grocery(grocery_id):
    data = load_data()
    req = request.get_json()

    for entry in data:
        if entry["id"] == grocery_id:
            entry["item"] = req.get("item", entry["item"])
            entry["quantity"] = req.get("quantity", entry["quantity"])
            # NEW: allow updating "unit"
            if "unit" in req:
                entry["unit"] = req["unit"]
            save_data(data)
            return jsonify({"message": "Grocery updated"}), 200

    return jsonify({"error": "Item not found"}), 404

@app.route('/groceries/<int:grocery_id>', methods=['DELETE'])
def remove_grocery(grocery_id):
    data = load_data()
    updated_data = [g for g in data if g["id"] != grocery_id]

    if len(updated_data) == len(data):
        return jsonify({"error": "Item not found"}), 404

    save_data(updated_data)
    return jsonify({"message": "Grocery removed"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
