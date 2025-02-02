from datetime import datetime
from flask import Flask, request, jsonify
import googlemaps
from flask_cors import CORS # type: ignore
import firebase_admin
from firebase_admin import credentials, firestore, auth, db
import os
from dotenv import load_dotenv # type: ignore

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize Google Maps client with your API key
gmaps = googlemaps.Client(key="AIzaSyCrfmZ1LLM5_lYTsnUTX8qmjOQfMe0dS4A")  # Replace with your actual API key

cred = credentials.Certificate("nirbhaya-90922-firebase-adminsdk-fbsvc-43d31cff0e.json")  # Make sure the filename matches!

# Initialize the app with the credentials and database URL
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://nirbhaya-90922-default-rtdb.firebaseio.com/'
})

ref = db.reference('test')  # Reference to the 'test' node in your Realtime Database

# Write data to Firebase Realtime Database
ref.set({
    'message': 'Hello Firebase'
})

@app.route('/get_safe_route', methods=['GET'])
def get_safe_route():
    # Get origin and destination from the query parameters
    origin = request.args.get('origin')
    destination = request.args.get('destination')

    # Ensure both parameters are provided
    if not origin or not destination:
        return jsonify({"error": "Both 'origin' and 'destination' are required."}), 400

    # Fetch directions using Google Maps API
    try:
        directions = gmaps.directions(origin, destination, mode="walking")
        return jsonify(directions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_routes", methods=["GET"])
def get_routes():
    routes_ref = db.reference("safe_routes")
    routes = routes_ref.get()

    return jsonify(routes), 200

@app.route("/get_user/<uid>", methods=["GET"])
def get_user(uid):
    user_ref = db.reference(f"users/{uid}")
    user_data = user_ref.get()

    if user_data:
        return jsonify(user_data), 200
    else:
        return jsonify({"error": "User not found"}), 404

# Signup API
@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.json
        email = data["email"]
        password = data["password"]

        # Create user in Firebase
        user = auth.create_user(email=email, password=password)

        # Store user details in Realtime Database
        user_ref = db.reference(f"users/{user.uid}")
        user_ref.set({
            "email": email,
            "name": data.get("name", ""),
            "other_info": data.get("other_info", "")
        })
        
        return jsonify({"message": "User created successfully", "uid": user.uid}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Login API
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data["email"]
        password = data["password"]
        # Firebase Authentication handles login and password validation
        user = auth.get_user_by_email(email)
        if user:
            # You could validate the password if using a custom system, but Firebase Auth does this automatically
            return jsonify({"message": "Login successful", "uid": user.uid}), 200
        else:
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Route to report unsafe areas
@app.route('/report_unsafe_area', methods=['POST'])
def report_unsafe_area():
    try:
        data = request.json
        location = data['location']
        user_id = data.get('user_id', 'anonymous')  # Optional: Track user who reported

        # Manually create a timestamp using datetime
        timestamp = datetime.utcnow().isoformat()  # Use UTC timestamp

        # Store the report in Firebase Realtime Database
        report_ref = db.reference('unsafe_areas').push()
        report_ref.set({
            'location': location,
            'user_id': user_id,
            'timestamp': timestamp  # Use manual timestamp
        })
        
        return jsonify({"status": "success", "report_id": report_ref.key})  # Use .key for Realtime Database ID
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to fetch reported unsafe areas
@app.route('/get_unsafe_areas', methods=['GET'])
def get_unsafe_areas():
    try:
        # Fetch all reported unsafe areas from Firebase Realtime Database
        unsafe_areas = []
        reports_ref = db.reference('unsafe_areas').get()  # Using Realtime Database reference

        # Check if data exists
        if reports_ref:
            for key, value in reports_ref.items():  # Iterate through items in the unsafe_areas
                unsafe_areas.append(value)
        
        return jsonify(unsafe_areas) if unsafe_areas else jsonify({"message": "No reports found"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/save_route", methods=["POST"])
def save_route():
    try:
        data = request.json
        route_ref = db.reference("safe_routes").push()  # Auto-generate a unique key
        route_ref.set(data)

        return jsonify({"message": "Route saved successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Test if Firebase Realtime Database connection is working
def test_firebase_connection():
    try:
        ref = db.reference('test')
        ref.set({'test_key': 'test_value'})
        print("Connection and write success!")
    except Exception as e:
        print(f"Error: {str(e)}")

test_firebase_connection()

if __name__ == "__main__":
    app.run(debug=True)


