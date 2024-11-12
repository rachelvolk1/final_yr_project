# Standard library imports
import os
import time
from datetime import datetime

# Third-party imports
import pymysql
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Local application imports
from config import Config
from models.models import db, User, Dataset, Instance, ErrorLog, Model, Notification, Preprocessing, Process, TestResult, TrainingProcess
from models.decision_tree import train_decision_tree_model
from models.random_forest import train_random_forest_model
from models.svm import train_svm_model

# Configure PyMySQL to be used as MySQLdb
pymysql.install_as_MySQLdb()

# Initialize the app
app = Flask(__name__)

# Apply the configurations from config.py
app.config.from_object(Config)

# Set up database configurations (optional if already in config.py)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://dbmasteruser:mypassword@ls-07e0ef4f1e34959472eab621b30ef9cad6b83a49.c3ueawe2gzde.ap-south-1.rds.amazonaws.com/dbmaster'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = r'C:\Users\USER\Desktop\proj\uploads'

# Initialize db and Flask-Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Create all tables (if necessary)
with app.app_context():
    db.create_all()

# Function to get all users
def get_all_users():
    return User.query.all()

# Function to get a user by ID
def get_user_by_id(user_id):
    return User.query.get(user_id)

# Function to delete a user by ID
def delete_user_by_id(user_id):
    user = get_user_by_id(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    else:
        raise ValueError("User not found")

# API Endpoint to get all users
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

# API Endpoint to create a new user
@app.route('/api/users', methods=['POST'])
def add_new_user():
    data = request.json
    new_user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),  # Storing hashed passwords
        dob=data.get('dob'),
        nrc=data.get('nrc'),
        role=data.get('role'),
        user_status=data.get('user_status', 'active')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201

# API Endpoint to get all datasets
@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    datasets = Dataset.query.all()
    return jsonify([dataset.to_dict() for dataset in datasets])

# Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}

# Define expected columns
EXPECTED_COLUMNS = [
    "TPIN", "Location", "TAX Type", "Transaction ID", 
    "Period From", "Period To", "Payment Method", 
    "Payment Amount", "Payment Date"
]

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'csv', 'xlsx'}


# Function to save the uploaded file
def save_file(file):
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filename, filepath


# Function to create a dataset entry
def create_dataset(filename, filepath):
    dataset = Dataset(
        dataset_name=filename,
        file_path=filepath,
        upload_date=datetime.utcnow(),
        dataset_status='uploaded'
    )
    db.session.add(dataset)
    db.session.commit()  # Commit here to get the dataset_id
    return dataset.dataset_id  # Ensure it's dataset_id not id


# Function to create an instance (Placeholder function assuming it uses dataset_id)
def create_instance(dataset_id):
    instance = Instance(
        dataset_id=dataset_id,
        instance_name=f'Instance for dataset {dataset_id}',  # Update name as needed
        instance_status='created'
    )
    db.session.add(instance)
    db.session.commit()
    return instance.instance_id



# Function to load and validate dataframe (Placeholder function)
def load_dataframe(filepath):
    # Implementation for loading and validating the DataFrame
    pass

# Function to validate the DataFrame against expected columns
def validate_columns(df):
    return all(col in df.columns for col in EXPECTED_COLUMNS)


# Mock Functions

# Function to get all users (mocked)
def get_all_users():
    return users

# Function to get a user by ID (mocked)
def get_user_by_id(user_id):
    return next((user for user in users if user['id'] == user_id), None)

# Function to delete a user by ID (mocked)
def delete_user_by_id(user_id):
    global users
    users = [user for user in users if user['id'] != user_id]

# Function to get a user by their ID
def get_user_by_id(user_id):
    return User.query.get(user_id)  # Ensure you're getting a User model, not a dict


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query the database to find the user by their email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and the password is correct
        if user and check_password_hash(user.password_hash, password):
            # Store user information in the session
            session['user_id'] = user.user_id
            session['username'] = user.first_name  # This can be customized to store more info
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to the dashboard if login is successful
        else:
            flash('Invalid email or password!', 'danger')  # Show an error if login fails

    return render_template('login.html')  # Render the login page for GET requests


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        dob = request.form['date_of_birth']
        nrc = request.form['nrc']
        position = request.form['position']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return render_template('register.html')

        # Create new user and hash the password
        hashed_password = generate_password_hash(password)
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hashed_password,
            dob=datetime.strptime(dob, '%Y-%m-%d'),  # Assuming dob is stored as a Date
            nrc=nrc,
            role=position,
            created_on=datetime.utcnow()
        )

        # Add the user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error occurred during registration: ' + str(e), 'danger')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Implement logic to handle forgot password functionality (e.g., sending a reset link via email)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

# Display upload page
@app.route('/upload', methods=['GET', 'POST'])
def upload_form():
    if request.method == 'GET':
        return render_template('upload.html')
    elif request.method == 'POST':
        return upload_file()

def upload_file():
    if 'fileUpload' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400

    file = request.files['fileUpload']
    if not file or not file.filename:
        return jsonify({'error': 'No file selected.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file type.'}), 400

    try:
        filename, filepath = save_file(file)
        dataset_id = create_dataset(filename, filepath)

        # Create instance for dataset and load DataFrame for validation
        instance_id = create_instance(dataset_id)
        load_dataframe(filepath)

        return jsonify({'dataset_id': dataset_id, 'instance_id': instance_id, 'filename': filename}), 200
    except SQLAlchemyError as e:
        db.session.rollback()  # Ensure rollback on database error
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Route to display the preview page
@app.route('/preview/<int:instance_id>/<filename>', methods=['GET'])
def preview_file(instance_id, filename):
    return render_template('preview.html', instance_id=instance_id, filename=filename)

# API endpoint to provide file data for AJAX
@app.route('/api/preview/<int:dataset_id>/<string:filename>', methods=['GET'])
def api_preview(dataset_id, filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(filepath):
        try:
            # Load the dataset depending on the file type
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filepath)
            else:
                return jsonify({"error": "Unsupported file type"}), 400

            # Convert the DataFrame to JSON for DataTables or other use
            data_json = df.to_dict(orient='records')

            return jsonify(data_json), 200
        except Exception as e:
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    else:
        return jsonify({"error": "File not found"}), 404


@app.route('/load-data', methods=['GET'])
def load_data():
    try:
        # Load the dataset from a CSV file (update the file name as needed)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_file.csv')  # Adjust the filename
        data = pd.read_csv(file_path)

        # Convert DataFrame to a list of dictionaries for JSON response
        data_list = data.to_dict(orient='records')
        
        # Return JSON response
        return jsonify(data_list), 200
    except FileNotFoundError:
        return jsonify({'error': 'File not found.'}), 404
    except Exception as e:
        # Handle any other exceptions
        return jsonify({'error': str(e)}), 500

@app.route('/train', methods=['GET', 'POST'])
def train():
    if request.method == 'POST':
        model_type = request.form.get('model-type')
        filename = request.form.get('filename')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if os.path.exists(filepath):
            if model_type == 'decision_tree':
                train_decision_tree_model(filepath)
            elif model_type == 'random_forest':
                train_random_forest_model(filepath)
            elif model_type == 'svm':
                train_svm_model(filepath)
            
            return jsonify({'message': 'Training started successfully.', 'progress': 0})
        else:
            return jsonify({'error': 'File not found'})

    # Load the dataset and get the first 5 rows
    filename = "your_data.csv"  # This can be dynamic based on your actual filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        preview_data = df.head(5).values.tolist()  # Get the first 5 rows
        return render_template('train.html', preview_data=preview_data)
    else:
        return render_template('train.html', preview_data=None)

@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        feature_1 = request.form.get('individualFeature_1')
        feature_2 = request.form.get('individualFeature_2')

        response = {
            'feature_1': feature_1,
            'feature_2': feature_2
        }
        return jsonify(response)

    return render_template('test.html')

@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        response = {
            'status': 'Results complete'
        }
        return jsonify(response)

    return render_template('results.html')

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    if request.method == 'POST':
        response = {
            'status': 'Analysis data received'
        }
        return jsonify(response)

    return render_template('analysis.html')


@app.route('/message_center', methods=['GET', 'POST'])
def message_center():
    if request.method == 'POST':
        # Handle message center data
        flash('results!', 'success')
    return render_template('message_center.html')


from flask import render_template, session
from flask import render_template, jsonify, request
from flask import render_template, jsonify, request, session

@app.route('/alerts_center')
def alerts_center():
    # Fetch the user ID from the session
    user_id = session.get('user_id')  # Adjust the key based on what you set in the session

    # Fetch all notifications for the user
    notifications = Notification.query.filter_by(user_id=user_id).all() if user_id else []

    context = []

    for notification in notifications:
        dataset = Dataset.query.get(notification.dataset_instance_id)  # Fetch dataset info if needed
        if notification.type == 'upload':
            context.append({
                'dataset_name': dataset.name if dataset else 'Unknown Dataset',
                'upload_time': notification.created_ON.strftime('%Y-%m-%d %H:%M:%S'),
                'dataset_instance_id': notification.dataset_instance_id,
                'notification_type': 'Dataset Upload'
            })
        elif notification.type == 'training':
            context.append({
                'dataset_name': dataset.name if dataset else 'Unknown Dataset',
                'training_time': notification.created_ON.strftime('%Y-%m-%d %H:%M:%S'),
                'dataset_instance_id': notification.dataset_instance_id,
                'notification_type': 'Model Training'
            })
        elif notification.type == 'testing':
            context.append({
                'dataset_name': dataset.name if dataset else 'Unknown Dataset',
                'test_time': notification.created_ON.strftime('%Y-%m-%d %H:%M:%S'),
                'dataset_instance_id': notification.dataset_instance_id,
                'notification_type': 'Data Testing'
            })
        elif notification.type == 'results':
            context.append({
                'dataset_name': dataset.name if dataset else 'Unknown Dataset',
                'results_time': notification.created_ON.strftime('%Y-%m-%d %H:%M:%S'),
                'dataset_instance_id': notification.dataset_instance_id,
                'notification_type': 'Results'
            })
        elif notification.type == 'analysis':
            context.append({
                'dataset_name': dataset.name if dataset else 'Unknown Dataset',
                'analysis_time': notification.created_ON.strftime('%Y-%m-%d %H:%M:%S'),
                'dataset_instance_id': notification.dataset_instance_id,
                'notification_type': 'Analysis'
            })

    # Render the template and pass the context
    return render_template('alerts_center.html', notifications=context)

@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    # Fetch the user ID from the session
    user_id = session.get('user_id')  # Adjust the key based on what you set in the session

    # Find the notification by ID
    notification = Notification.query.get(notification_id)

    if notification and notification.user_id == user_id:
        # Mark the notification as read
        notification.is_read = True
        db.session.commit()
        return jsonify({"message": "Notification marked as read"}), 200
    else:
        return jsonify({"error": "Notification not found or unauthorized"}), 404



from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from datetime import datetime

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        dob = request.form['date_of_birth']  # Match with the HTML name
        nrc = request.form['nrc']
        position = request.form['position']
        password = request.form['password']

        # Convert date from d-m-yyyy format to date object
        if dob:
            try:
                dob = datetime.strptime(dob, '%Y-%m-%d').date()  # Parse the date
            except ValueError:
                flash('Invalid date format. Please use d-m-yyyy.', 'danger')
                return render_template('create_user.html')

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('This user already exists. Please use a different email.', 'danger')
            return render_template('create_user.html')

        # Create new user instance
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=generate_password_hash(password),
            dob=dob,
            nrc=nrc,
            role=position,
            created_on=datetime.now()  # Automatically set created_on
        )

        # Add user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully!', 'success')
            return redirect(url_for('/create_user'))  # Redirect to a suitable route
        except IntegrityError:
            db.session.rollback()  # Roll back the session on error
            flash('An error occurred while creating the user. Please try again.', 'danger')

    return render_template('create_user.html')

# Function to retrieve all users from the database
def get_all_users():
    return User.query.all()  # Fetch all users

# Route to list all users
@app.route('/list_users', methods=['GET'])
def list_users():
    users = get_all_users()  # Fetch all users from the database
    return render_template('list_users.html', users=users)  # Render the template with users data

# Route to edit a specific user
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)  # Retrieve user or return 404 if not found

    if request.method == 'POST':
        # Update user details
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.dob = request.form['dob']
        user.nrc = request.form['nrc']
        user.position = request.form['position']
        db.session.commit()  # Save changes to the database

        message = "User details updated successfully!"
        message_type = "success"
        return render_template('edit_user.html', user=user, message=message, message_type=message_type)

    return render_template('edit_user.html', user=user)  # Render the edit form

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)  # Retrieve user or return 404 if not found
    db.session.delete(user)  # Delete the user
    db.session.commit()  # Commit the changes to the database

    # Retrieve the updated list of users after deletion
    users = User.query.all()  # Get all users again

    message = "User deleted successfully!"
    message_type = "success"
    return render_template('list_users.html', users=users, message=message, message_type=message_type)  # Render the template with updated user data

if __name__ == "__main__":
    app.run(debug=True)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)



if __name__ == '__main__':
    app.run(debug=True)
