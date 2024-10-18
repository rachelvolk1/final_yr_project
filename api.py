from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from models.models import db, User, Dataset

api = Blueprint('api', __name__)

# API Endpoint to get all users
@api.route('/users', methods=['GET'])
def get_users():
    user_id = request.args.get('user_id')  # Get user_id from query parameters

    if user_id:
        user = User.query.get(user_id)  # Fetch user by ID
        if user:
            return jsonify(user.to_dict()), 200
        else:
            return jsonify({"error": "User not found."}), 404
    else:
        users = User.query.all()  # Fetch all users
        return jsonify([user.to_dict() for user in users]), 200

# API Endpoint to create a new user
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from models.models import db, User, Dataset
from datetime import datetime

api = Blueprint('api', __name__)

# API Endpoint to create a new user
@api.route('/users', methods=['POST'])
def add_new_user():
    data = request.json  # Get the JSON data from the request

    # Check if 'password' is provided
    password = data.get('password')
    if not password:
        return jsonify({"error": "Password is required."}), 400

    # Check if required fields are provided
    required_fields = ['first_name', 'last_name', 'email', 'dob', 'nrc', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required."}), 400

    # Check if email is unique
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists."}), 400

    # Parse the date of birth and ensure it's in the correct format
    try:
        dob = datetime.strptime(data['dob'], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Date of birth must be in YYYY-MM-DD format."}), 400

    # Create a new user instance
    new_user = User(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data.get('email'),
        password_hash=generate_password_hash(password),  # Storing hashed passwords
        dob=dob,
        nrc=data.get('nrc'),
        role=data.get('role'),
        user_status=data.get('user_status', 'active')
    )

    # Add the new user to the session and commit
    db.session.add(new_user)
    db.session.commit()

    # Return the created user's details
    return jsonify(new_user.to_dict()), 201


# API Endpoint to delete a user
@api.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)  # Fetch user by ID

    if user:
        db.session.delete(user)  # Delete the user from the session
        db.session.commit()  # Commit the transaction
        return jsonify({"message": "User deleted successfully."}), 200
    else:
        return jsonify({"error": "User not found."}), 404


# API Endpoint to get all datasets
@api.route('/datasets', methods=['GET'])
def get_datasets():
    datasets = Dataset.query.all()
    return jsonify([dataset.to_dict() for dataset in datasets]), 200

# Error handling
@api.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@api.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500
