# Standard library imports
import os
import time
from datetime import datetime

# Third-party imports
import pymysql
import pandas as pd
import subprocess
import os
import logging
import joblib

from joblib import load
from flask import abort
from models.evaluation_functions import load_data, ensure_data_types, remove_duplicates, basic_one_hot_encode, \
    preprocess_data
from data_cleaning import load_and_clean_data, ensure_data_types, remove_duplicates, basic_one_hot_encode, \
    save_cleaned_data
from flask import Flask, request, jsonify, current_app

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
from models.random_forest import train_random_forest
from models.isolation_forest import train_isolation_forest
from models.svm import train_one_class_svm
from models.analyse_results_for_labelling import (load_csv_to_dataframe, save_report, generate_statistics, plot_correlation_heatmap, plot_anomalies_distribution_by_group_one_hot)
# Import the scripts from the models folder
from models.analyse_results_for_labelling import load_csv_to_dataframe, save_report
from models.anomaly_detection import load_csv_to_dataframe, save_report

# Import the necessary functions from anomaly_detection script in the models folder
from models.anomaly_detection import load_csv_to_dataframe, save_report


from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import joblib
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

import os
import pandas as pd
from flask import Flask, request, jsonify, render_template
from sklearn.model_selection import train_test_split
from utils import convert_hyperparams

import os
from flask import Flask, jsonify, request
import pandas as pd
from datetime import datetime
import subprocess

from flask import session, flash, redirect, url_for, request, render_template
from werkzeug.security import check_password_hash
from datetime import datetime
from flask import jsonify
from datetime import timedelta

from flask import Flask, session, jsonify
from datetime import datetime, timedelta


# Configure PyMySQL to be used as MySQLdb
pymysql.install_as_MySQLdb()

# Initialize the app
app = Flask(__name__)

# Apply the configurations from config.py
app.config.from_object(Config)

model = joblib.load('models/trained_model_random_forest.joblib')

# Set up database configurations (optional if already in config.py)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://dbmasteruser:mypassword@ls-07e0ef4f1e34959472eab621b30ef9cad6b83a49.c3ueawe2gzde.ap-south-1.rds.amazonaws.com/dbmaster'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_DATASET_FOLDER'] = 'dataset'
app.config['REPORT_FOLDER'] = 'report'
app.config['PREPROCESSED_FOLDER'] = 'preprocessed_data'
app.config['PROCESSED_DATASET_FOLDER'] = os.path.join('uploads', 'dataset')
app.config['MODEL_FOLDER'] = 'models'
app.config['MODEL_SAVE_PATH'] = 'models/saved_models'
app.config['DEPLOYED_MODEL_PATH'] = 'models/deployed_models'
app.config['PREPROCESSED_FOLDER'] = os.path.join(app.root_path, 'preprocessed_data')

# Ensure the PROCESSED_DATASET_FOLDER exists
if not os.path.exists(app.config['PROCESSED_DATASET_FOLDER']):
    os.makedirs(app.config['PROCESSED_DATASET_FOLDER'])

    # Paths for datasets and reports
    dataset_folder = app.config['PROCESSED_DATASET_FOLDER']
    dataset_path = os.path.join(dataset_folder, filename)
    report_folder = app.config['REPORT_FOLDER']

#Global Variables

# Global variable to store evaluation metrics
evaluation_metrics = {}

# Storing the last cleaned dataset name in a global variable
last_cleaned_dataset = None

# Storing the last trained model name in a global variable
last_trained_model = None

# Storing the last cleaned dataset name in a global variable
last_saved_model = None

ABSOLUTE_MODEL_PATH = 'models/deployed_models/current_model.pkl'
MODEL_SAVE_PATH = './summary/trained_model_{}.joblib'
EVALUATION_SAVE_PATH = './summary/evaluation_results_{}.txt'
SUMMARY_SAVE_PATH = './summary/summary_report.txt'

# Initialize db and Flask-Migrate
db.init_app(app)
migrate = Migrate(app, db)


#Database User tables

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

# Dummy function to simulate saving and deploying the model.
def save_and_deploy_model(model, file_path):
    joblib.dump(model, file_path)
    print(f"Model saved at {file_path}.")
    # Add your deployment logic here.
    return True


# Utility function to convert hyperparameter values
def convert_hyperparams(hyperparams):
    def strtobool(value):
        if isinstance(value, str):
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
        return value

    def handle_numbers(value):
        if isinstance(value, bool):
            return value  # Bypass boolean values
        try:
            if isinstance(value, str):
                if '.' in value:
                    return float(value)
                return int(value)
        except (ValueError, TypeError):
            return value

    return {k: handle_numbers(strtobool(v)) for k, v in hyperparams.items()}


#User management

# API Endpoint to get all users
@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    total_users = len(users)
    # Assuming each user instance has a .to_dict() method to serialize their data
    return jsonify({
        "total_users": total_users,
        "users": [user.to_dict() for user in users]
    })

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


#Dataset Management
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

############################Dashboard############################

@app.route('/api/get_folder_counts', methods=['GET'])
def get_folder_counts():
    try:
        upload_folder_count = len(os.listdir(app.config['UPLOAD_FOLDER']))
        preprocessed_folder_count = len(os.listdir(app.config['PREPROCESSED_FOLDER']))

        response = {
            'uploads': upload_folder_count,
            'preprocessed_data': preprocessed_folder_count
        }

        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"Error fetching folder counts: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/current_users', methods=['GET'])
def get_current_users():
    # Define "current" as within the last hour
    time_threshold = datetime.utcnow() - timedelta(hours=1)

    # Query users who logged in within the last hour
    current_users_count = User.query.filter(User.last_login >= time_threshold).count()

    return jsonify({"current_users": current_users_count}), 200


@app.route('/api/get_trained_model_count', methods=['GET'])
def get_trained_model_count():
    try:
        model_path = app.config['MODEL_SAVE_PATH']
        if not os.path.exists(model_path):
            os.makedirs(model_path)

        # Count the number of files in the model directory
        count = len([name for name in os.listdir(model_path) if os.path.isfile(os.path.join(model_path, name))])
        return jsonify({"trained_model_count": count}), 200
    except Exception as e:
        app.logger.error(f"Error fetching trained model count: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


############################Initial Processes###########################
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

            # Update the last login time
            user.last_login = datetime.utcnow()
            db.session.commit()

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


############################Main Processes###########################
############################Upload Route############################
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
@app.route('/api/preview/<int:instance_id>/<filename>', methods=['GET'])
def get_preview_data(instance_id, filename):
    # Construct the file path
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    # Load data from the file (assuming CSV format for this example)
    try:
        data = pd.read_csv(file_path)
        return jsonify(data.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/clean/<dataset_id>/<filename>', methods=['POST'])
def clean_data(dataset_id, filename):
    global last_cleaned_dataset
    try:
        app.logger.info(f"Received request to clean data for dataset ID: {dataset_id}, filename: {filename}")

        # Generate unique output filename
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"cleaned_{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_path = os.path.join(app.config['PROCESSED_DATASET_FOLDER'], unique_filename)

        app.logger.info(f"UPLOAD_FOLDER config: {app.config['UPLOAD_FOLDER']}")
        app.logger.info(f"File path resolved to: {file_path}")
        app.logger.info(f"Output path resolved to: {output_path}")
        app.logger.info(f"Contents of UPLOAD_FOLDER: {os.listdir(app.config['UPLOAD_FOLDER'])}")

        if not os.path.exists(file_path):
            app.logger.error(f"File does not exist: {file_path}")
            return jsonify({"message": "File not found."}), 404

        # Run the data cleaning script
        result = subprocess.run(['python', 'data_cleaning.py', file_path, output_path], capture_output=True, text=True)

        if result.returncode == 0:
            app.logger.info("Data cleaning script executed successfully.")

            # Update the last cleaned dataset
            last_cleaned_dataset = unique_filename

            # Load the cleaned dataset
            cleaned_df = pd.read_csv(output_path)

            # Optionally, return the cleaned data directly
            cleaned_data_json = cleaned_df.to_json(orient='records')
            return jsonify({
                "message": "Data cleaned successfully.",
                "cleaned_data": cleaned_data_json,
                "output_path": output_path
            }), 200
        else:
            app.logger.error(f"Data cleaning script failed with error: {result.stderr}")
            return jsonify({
                "message": "Failed to clean data.",
                "error": result.stderr
            }), 500

    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({
            "message": "An unexpected error occurred.",
            "error": str(e)
        }), 500


@app.route('/api/get_last_cleaned_dataset', methods=['GET'])
def get_last_cleaned_dataset():
    global last_cleaned_dataset
    if last_cleaned_dataset:
        return jsonify({"last_cleaned_dataset": last_cleaned_dataset}), 200
    else:
        return jsonify({"message": "No dataset has been cleaned yet."}), 404


@app.route('/api/save_cleaned_data', methods=['POST'])
def save_cleaned_data():
    try:
        # Ensure the request content type is JSON
        if request.content_type != 'application/json':
            return jsonify({'message': 'Content-Type must be application/json', 'error': 'Unsupported Media Type'}), 415

        # Parse the JSON data from the request
        data = request.get_json()

        if not data or 'data' not in data:
            return jsonify({'message': 'No cleaned data provided'}), 400

        cleaned_data = data['data']

        # Convert the data to a DataFrame
        df = pd.DataFrame(cleaned_data)

        # Define the directory and file path
        directory = os.path.join(os.getcwd(), 'models', 'dataset')
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_path = os.path.join(directory, 'cleaned_data.csv')

        # Save the DataFrame to a CSV file
        df.to_csv(file_path, index=False)

        return jsonify({'message': 'Dataset saved successfully', 'file_path': file_path})

    except Exception as e:
        return jsonify({'message': 'An error occurred while saving the cleaned dataset', 'error': str(e)}), 500


@app.route('/list-datasets')
def list_datasets():
    datasets = []
    try:
        dataset_folder = app.config['PROCESSED_DATASET_FOLDER']
        # List all files in the datasets directory
        datasets = os.listdir(dataset_folder)
    except Exception as e:
        print(f"Error while fetching datasets: {e}")

    return jsonify({'datasets': datasets})


logging.basicConfig(level=logging.DEBUG)

############################Anomaly Route############################
@app.route('/api/anomaly_detection/<dataset_id>/<filename>', methods=['POST'])
def anomaly_detection(dataset_id, filename):
    app.logger.debug(f"Received request for anomaly detection with dataset_id: {dataset_id}, filename: {filename}")

    # Verify that the dataset path is correct
    if not os.path.exists(dataset_path):
        app.logger.error(f"Dataset path does not exist: {dataset_path}")
        return jsonify({"error": "Dataset path does not exist."}), 400

    try:
        # Load the dataset
        df = load_csv_to_dataframe(dataset_path)
        if df.empty:
            app.logger.error('Failed to load dataset into DataFrame.')
            return jsonify({"error": "Failed to load dataset."}), 400

        # Create a directory for the report
        report_directory = os.path.join(report_folder, dataset_id)
        os.makedirs(report_directory, exist_ok=True)

        # Perform anomaly detection and save the report
        save_report(report_directory, df)

        return jsonify({
            "message": "Anomaly detection completed successfully.",
            "report_directory": report_directory
        })
    except Exception as e:
        app.logger.error(f"Exception during anomaly detection: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/label/<dataset_id>/<filename>', methods=['POST'])
def label_data(dataset_id, filename):
    try:
        app.logger.info(f"Received request to label data for dataset ID: {dataset_id}, filename: {filename}")

        # Construct the file path for the original data
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({"message": "File not found."}), 404

        # Load the original data
        df = pd.read_csv(file_path)

        # Perform labeling (add your labeling logic here)
        # Example: Adding an 'is_fraud' column (this part depends on your labeling logic)
        # df['is_fraud'] = df['some_column'].apply(some_labeling_function)

        # Save the labeled dataset in the 'dataset' folder
        labeled_file_path = os.path.join(app.config['PROCESSED_DATASET_FOLDER'], f"labeled_{filename}")
        df.to_csv(labeled_file_path, index=False)
        app.logger.info(f"Processed labeled dataset saved to {labeled_file_path}")

        # Generate and save the report
        report_directory = os.path.join(app.config['REPORT_FOLDER'], str(dataset_id))
        if not os.path.exists(report_directory):
            os.makedirs(report_directory)
        save_report(report_directory, df)
        app.logger.info(f"Report saved to {report_directory}")

        # Return paths to the labeled dataset and generated reports
        response = {
            "status": "Success",
            "labeled_data": labeled_file_path,
            "report_directory": report_directory
        }
        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"message": "An unexpected error occurred.", "error": str(e)}), 500

############################Preprocessing Route############################
#preprocessing data
@app.route('/load-dataset', methods=['POST'])
def load_dataset():
    dataset = request.form.get('dataset')
    if not dataset:
        return jsonify({'error': 'No dataset specified'}), 400

    try:
        filepath = os.path.join(app.config['PROCESSED_DATASET_FOLDER'], dataset)
        df = load_data(filepath)
        if df is None:
            return jsonify({'error': 'Data loading failed'}), 500
        preview_data = df.head(5).to_dict(orient='records')
        return jsonify({'preview_data': preview_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from models.evaluation_functions import load_data, ensure_data_types, remove_duplicates, basic_one_hot_encode, \
    preprocess_data

@app.route('/preview-clean-dataset', methods=['GET'])
def preview_clean_dataset():
    dataset_name = request.args.get('dataset')
    if not dataset_name:
        return jsonify({'error': 'Dataset name is required'}), 400

    try:
        file_path = os.path.join(app.config['PROCESSED_DATASET_FOLDER'], dataset_name)
        df = pd.read_csv(file_path)
        column_names = df.columns.tolist()
        preview_data = df.head(10).values.tolist()
        return jsonify({'columns': column_names, 'preview_data': preview_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/preprocessing', methods=['POST'])
def preprocessing():
    dataset = request.form.get('dataset')
    if not dataset:
        return jsonify({'error': 'No dataset specified'}), 400

    try:
        filepath = os.path.join(app.config['PROCESSED_DATASET_FOLDER'], dataset)
        df = load_data(filepath)
        if df is None:
            return jsonify({'error': 'Data loading failed'}), 500

        df = ensure_data_types(df)
        df = remove_duplicates(df)
        df = basic_one_hot_encode(df)
        df = preprocess_data(df)

        output_filename = f'preprocessed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        output_path = os.path.join(app.config['PREPROCESSED_FOLDER'], output_filename)
        df.to_csv(output_path, index=False)

        return jsonify({'result': 'Preprocessing completed successfully', 'output_file': output_filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preprocessing-form', methods=['GET'])
def preprocessing_form():
    return render_template('preprocessing.html', preview_data=[], filename='')

@app.route('/load-data', methods=['GET'])
def load_data(filepath):
    try:
        # Load the CSV file into a pandas DataFrame
        df = pd.read_csv(filepath)
        return df
    except Exception as e:
        print(f"Error loading data from {filepath}: {e}")
        return None

############################training Route############################

@app.route('/train', methods=['POST'])
def train():
    global last_trained_model
    dataset_name = request.form.get('dataset-name')
    model_type = request.form.get('model-type')
    hyperparameters = request.form.get('hyperparameters')
    hyperparameters = eval(hyperparameters) if hyperparameters else {}
    hyperparameters = convert_hyperparams(hyperparameters)

    if not dataset_name or not model_type:
        return jsonify({'error': 'Dataset name and Model type are required'}), 400

    try:
        dataset_path = os.path.join(app.config['PREPROCESSED_FOLDER'], dataset_name)
        df = pd.read_csv(dataset_path)

        # Define the model save path
        model_path = os.path.join(app.config['MODEL_SAVE_PATH'], model_type.lower().replace(" ", "_") + "_model.pkl")

        result = None
        if model_type == 'Isolation Forest':
            result = train_isolation_forest(data=df, hyperparameters=hyperparameters, save_path=model_path)
        elif model_type == 'One-Class SVM':
            # Correcting the call to train_one_class_svm
            result = train_one_class_svm(X_train=df, hyperparameters=hyperparameters, save_path=model_path)
        elif model_type == 'Random Forest':
            # Assuming the dataframe has the features in all columns except the last one which is the label
            X = df.iloc[:, :-1]
            y = df.iloc[:, -1]  # Assuming labels are in the last column
            # Split the data into training and test sets
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            result = train_random_forest(X_train=X_train, y_train=y_train, X_test=X_test, y_test=y_test,
                                         hyperparameters=hyperparameters, save_path=model_path)
        else:
            return jsonify({'error': 'Invalid model type'}), 400

        model = result['model']
        global evaluation_metrics
        evaluation_metrics = result['metrics']
        app.logger.info(f"Model saved to {model_path}")

        # Update the last trained model
        last_trained_model = model_type

        return jsonify({
            'message': 'Training completed successfully.',
            'model_path': model_path,
            'metrics': evaluation_metrics
        }), 200

    except Exception as e:
        app.logger.error(f"Error during training: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_last_model_trained', methods=['GET'])
def get_last_model_trained():
    global last_trained_model
    if last_trained_model:
        return jsonify({"last_model_trained": last_trained_model}), 200
    else:
        return jsonify({"message": "No model has been trained yet."}), 404


@app.route('/train', methods=['GET'])
def render_training_page():
    try:
        datasets = os.listdir(app.config['PREPROCESSED_FOLDER'])
        return render_template('train.html', datasets=datasets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-evaluation-results', methods=['GET'])
def get_evaluation_results():
    try:
        global evaluation_metrics
        if not evaluation_metrics:
            raise ValueError("No evaluation metrics available. Train the model first.")

        return jsonify(evaluation_metrics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Save & Deploy endpoint
@app.route('/api/save-deploy', methods=['POST'])
def save_deploy():
    try:
        data = request.json
        model_name = data.get('model_name')
        if not model_name:
            return jsonify({'error': 'Model name is required'}), 400

        # Temporary model path where the trained model is initially saved
        model_temp_path = os.path.join(app.config['MODEL_SAVE_PATH'], model_name + '.pkl')
        if os.path.exists(model_temp_path):
            saved_path = os.path.join(app.config['MODEL_SAVE_PATH'], model_name + '.pkl')
            deploy_path = os.path.join(app.config['DEPLOYED_MODEL_PATH'], model_name + '.pkl')

            # Create directories if they don't exist
            os.makedirs(app.config['MODEL_SAVE_PATH'], exist_ok=True)
            os.makedirs(app.config['DEPLOYED_MODEL_PATH'], exist_ok=True)

            # Move the model to the saved models folder
            os.rename(model_temp_path, saved_path)
            app.logger.info(f"Model saved to {saved_path}")

            # Deploy the model
            joblib.dump(joblib.load(saved_path), deploy_path)

            # Update the ABSOLUTE_MODEL_PATH to the new deployed model
            global ABSOLUTE_MODEL_PATH
            ABSOLUTE_MODEL_PATH = deploy_path

            app.logger.info(f"Model deployed to {deploy_path}")

            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Model file not found'}), 400
    except Exception as e:
        app.logger.error(f"Error during saving and deploying: {str(e)}", exc_info=True)
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500



# Configuration paths
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_SAVE_PATH = os.path.join(APP_ROOT, 'categories.json')
ABSOLUTE_MODEL_PATH = r'C:\Users\USER\Desktop\proj\models\trained_model_random_forestv2.joblib'

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def flatten_columns(json_data):
    logging.info("Flattening columns of the input JSON data")
    flattened_data = []
    for record in json_data:
        flat_record = {}
        for key, value in record.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_record[f"{key}_{sub_key}"] = sub_value
            else:
                flat_record[key] = value
        flattened_data.append(flat_record)
    logging.info("Flattened data: %s", flattened_data)
    return flattened_data

def prepare_data(records):
    df = pd.DataFrame(records)
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Reconstruct 'payment date' from year, month, and day
    if 'payment date_year' in df.columns and 'payment date_month' in df.columns and 'payment date_day' in df.columns:
        df['payment date'] = pd.to_datetime(
            df['payment date_year'].astype(str) + '-' +
            df['payment date_month'].astype(str).str.zfill(2) + '-' +
            df['payment date_day'].astype(str).str.zfill(2),
            format="%Y-%m-%d"
        )
    else:
        raise KeyError("'Payment Date' columns are missing from the dataset")

    # Reconstruct 'period from' and 'period to' as well
    if 'period from_year' in df.columns and 'period from_month' in df.columns and 'period from_day' in df.columns:
        df['period from'] = pd.to_datetime(
            df['period from_year'].astype(str) + '-' +
            df['period from_month'].astype(str).str.zfill(2) + '-' +
            df['period from_day'].astype(str).str.zfill(2),
            format="%Y-%m-%d"
        )
    else:
        raise KeyError("'Period From' columns are missing from the dataset")

    if 'period to_year' in df.columns and 'period to_month' in df.columns and 'period to_day' in df.columns:
        df['period to'] = pd.to_datetime(
            df['period to_year'].astype(str) + '-' +
            df['period to_month'].astype(str).str.zfill(2) + '-' +
            df['period to_day'].astype(str).str.zfill(2),
            format="%Y-%m-%d"
        )
    else:
        raise KeyError("'Period To' columns are missing from the dataset")

    return df


# Sample function to prepare the data; adapt as necessary
def prepare_data(data):
    df = pd.DataFrame(data)
    # Apply necessary data transformations
    return df


# Predict route
@app.route('/predict-route', methods=['POST'])
def predict_route():
    try:
        logging.info("Loading trained model from %s", ABSOLUTE_MODEL_PATH)
        model = joblib.load(ABSOLUTE_MODEL_PATH)

        input_data = request.json.get('input_data')
        filename = request.json.get('filename')

        logging.info("Received input data: %s", input_data)
        logging.info("Received filename: %s", filename)

        if input_data is None and filename is None:
            return jsonify({"error": "No input data or filename provided"}), 400

        if filename:
            file_path = os.path.join(app.config['PREPROCESSED_FOLDER'], filename)
            if not os.path.exists(file_path):
                logging.error("File not found: %s", filename)
                return jsonify({"error": f"File '{filename}' not found"}), 404

            df = pd.read_csv(file_path)
            input_df = prepare_data(df.to_dict(orient='records'))
        elif isinstance(input_data, list):
            if not all(isinstance(item, dict) for item in input_data):
                logging.error("Invalid data format for batch input")
                return jsonify({"error": "Invalid data format for batch input"}), 400
            input_df = prepare_data(input_data)
        elif isinstance(input_data, dict):
            input_df = prepare_data([input_data])
        else:
            logging.error("Invalid data format")
            return jsonify({"error": "Invalid data format"}), 400

        model_columns = model.feature_names_in_
        missing_cols = [col for col in model_columns if col not in input_df.columns]
        for col in missing_cols:
            input_df[col] = 0

        input_df = input_df[model_columns]
        predictions = model.predict(input_df)
        logging.info("Generated predictions: %s", predictions)

        if filename:
            return jsonify({"filename": filename, "predictions": predictions.tolist()}), 200
        elif isinstance(input_data, list):
            return jsonify({"batch_input": input_data, "predictions": predictions.tolist()}), 200
        elif isinstance(input_data, dict):
            transaction_id = input_data.get("Transaction_ID")
            if all(input_df["Transaction_ID"] == transaction_id):
                prediction = predictions[0]
                message = "transaction is predicted as potentially fraudulent" if prediction else "transaction is NOT predicted as potentially fraudulent"
                return jsonify({"individual_input": input_data, "prediction": prediction, "result": message}), 200
            else:
                return jsonify({"error": "Transaction not found in the dataset"}), 404

    except Exception as e:
        logging.error(f"Error in /predict-route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# Prediction form rendering
@app.route('/predict-form')
def predict_form():
    logging.info("Rendering prediction form")
    return render_template('predict.html')


# List preprocessed datasets
@app.route('/list-preprocessed-datasets', methods=['GET'])
def list_preprocessed_datasets():
    try:
        datasets = os.listdir(app.config['PREPROCESSED_FOLDER'])
        logging.info("Listing preprocessed datasets: %s", datasets)
        return jsonify({'datasets': datasets})
    except Exception as e:
        logging.error(f"Error in /list-preprocessed-datasets: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# Preview preprocessed dataset
@app.route('/preview-preprocessed-dataset', methods=['GET'])
def preview_preprocessed_dataset():
    dataset_name = request.args.get('dataset')
    logging.info("Previewing preprocessed dataset: %s", dataset_name)

    if not dataset_name:
        logging.error("Dataset name is required")
        return jsonify({'error': 'Dataset name is required'}), 400

    try:
        file_path = os.path.join(app.config['PREPROCESSED_FOLDER'], dataset_name)
        df = pd.read_csv(file_path)
        column_names = df.columns.tolist()
        preview_data = df.head(10).values.tolist()
        logging.info("Preview data fetched for dataset %s: %s", dataset_name, preview_data)
        return jsonify({'columns': column_names, 'preview_data': preview_data})
    except Exception as e:
        logging.error(f"Error in /preview-preprocessed-dataset: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500



@app.route('/get-dynamic-fields', methods=['GET'])
def get_dynamic_fields():
    try:
        tpin = request.args.get('tpin')
        dataset_name = request.args.get('dataset')  # Ensure dataset name is passed

        if not dataset_name or not tpin:
            logging.error("Both dataset name and TPIN are required")
            return jsonify({'error': 'Both dataset name and TPIN are required'}), 400

        file_path = os.path.join(app.config['PREPROCESSED_FOLDER'], dataset_name)
        df = pd.read_csv(file_path)

        # Assuming your dataset has columns like 'TPIN', 'Location', 'Tax_Type', etc.
        dynamic_fields = df[df['TPIN'] == tpin]

        if dynamic_fields.empty:
            return jsonify({'error': 'No data found for provided TPIN'}), 404

        # Example: Extracting some dynamic fields from the matched rows
        locations = dynamic_fields['Location'].unique().tolist()
        tax_types = dynamic_fields['Tax_Type'].unique().tolist()
        transaction_ids = dynamic_fields['Transaction_ID'].unique().tolist()
        payment_dates = {
            'year': dynamic_fields['Payment_Date_year'].iloc[0],
            'month': dynamic_fields['Payment_Date_month'].iloc[0],
            'day': dynamic_fields['Payment_Date_day'].iloc[0]
        }
        period_from_dates = {
            'year': dynamic_fields['Period_From_year'].iloc[0],
            'month': dynamic_fields['Period_From_month'].iloc[0],
            'day': dynamic_fields['Period_From_day'].iloc[0]
        }
        period_to_dates = {
            'year': dynamic_fields['Period_To_year'].iloc[0],
            'month': dynamic_fields['Period_To_month'].iloc[0],
            'day': dynamic_fields['Period_To_day'].iloc[0]
        }

        return jsonify({
            'locations': locations,
            'tax_types': tax_types,
            'transaction_ids': transaction_ids,
            'payment_dates': payment_dates,
            'period_from_dates': period_from_dates,
            'period_to_dates': period_to_dates
        })

    except Exception as e:
        logging.error(f"Error in /get-dynamic-fields: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


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
