from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func

# Initialize SQLAlchemy
db = SQLAlchemy()

from sqlalchemy.sql import func
from models.models import db

# User Model
class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    nrc = db.Column(db.String(50), nullable=True, unique=True)
    role = db.Column(db.String(50), nullable=True)
    created_on = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    last_login = db.Column(db.TIMESTAMP, nullable=True)
    user_status = db.Column(db.String(50), nullable=True, default='active')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,  # Corrected to 'last_name'
            'email': self.email,
            'dob': self.dob.isoformat() if self.dob else None,  # Convert date to ISO format
            'nrc': self.nrc,
            'role': self.role,
            'created_on': self.created_on.isoformat() if self.created_on else None,  # Convert timestamp to ISO format
            'last_login': self.last_login.isoformat() if self.last_login else None,  # Convert timestamp to ISO format
            'user_status': self.user_status
        }


# Instance Model
class Instance(db.Model):
    __tablename__ = 'instances'

    instance_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # ForeignKey to users table
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.dataset_id'), nullable=True)  # ForeignKey to datasets table
    instance_name = db.Column(db.String(100), nullable=True)
    created_on = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    instance_status = db.Column(db.String(50), nullable=True, default='pending')

    user = db.relationship('User', backref='instances', lazy=True)
    dataset = db.relationship('Dataset', backref='instances', lazy=True)

# Dataset Model
class Dataset(db.Model):
    __tablename__ = 'datasets'

    dataset_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dataset_name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    upload_date = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    dataset_status = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            'dataset_id': self.dataset_id,
            'dataset_name': self.dataset_name,
            'file_path': self.file_path,
            'upload_date': self.upload_date,
            'dataset_status': self.dataset_status
        }

# ErrorLog Model
class ErrorLog(db.Model):
    __tablename__ = 'error_logs'

    error_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    process_type = db.Column(db.String(50), nullable=True)
    process_id = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())

    def to_dict(self):
        return {
            'error_id': self.error_id,
            'process_type': self.process_type,
            'process_id': self.process_id,
            'error_message': self.error_message,
            'timestamp': self.timestamp
        }

# Model Model
class Model(db.Model):
    __tablename__ = 'model'

    model_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(100), nullable=True)
    parameters = db.Column(db.JSON, nullable=True)
    created_on = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    trained = db.Column(db.Boolean, default=False)
    training_accuracy = db.Column(db.Numeric(5, 2), nullable=True)
    testing_accuracy = db.Column(db.Numeric(5, 2), nullable=True)
    last_updated = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    def to_dict(self):
        return {
            'model_id': self.model_id,
            'model_name': self.model_name,
            'model_type': self.model_type,
            'parameters': self.parameters,
            'created_on': self.created_on,
            'trained': self.trained,
            'training_accuracy': self.training_accuracy,
            'testing_accuracy': self.testing_accuracy,
            'last_updated': self.last_updated
        }

# Notification Model
class Notification(db.Model):
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # ForeignKey to users table
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    created_ON = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    is_read = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='notifications', lazy=True)

    def to_dict(self):
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'message': self.message,
            'link': self.link,
            'created_ON': self.created_ON,
            'is_read': self.is_read
        }

# Preprocessing Model
class Preprocessing(db.Model):
    __tablename__ = 'preprocessing'

    preprocessing_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.dataset_id'), nullable=True)  # ForeignKey to datasets table
    step_name = db.Column(db.String(100), nullable=True)
    parameters = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(50), nullable=True)
    start_time = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    end_time = db.Column(db.TIMESTAMP, nullable=True)

    dataset = db.relationship('Dataset', backref='preprocessing', lazy=True)

    def to_dict(self):
        return {
            'preprocessing_id': self.preprocessing_id,
            'dataset_id': self.dataset_id,
            'step_name': self.step_name,
            'parameters': self.parameters,
            'status': self.status,
            'start_time': self.start_time,
            'end_time': self.end_time
        }

# Process Model
class Process(db.Model):
    __tablename__ = 'processes'

    process_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    process_type = db.Column(db.Enum('training', 'testing', 'preprocessing', 'analysis'), nullable=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.model_id'), nullable=True)  # ForeignKey to model table
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.dataset_id'), nullable=True)  # ForeignKey to datasets table
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # ForeignKey to users table
    status = db.Column(db.String(50), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    end_time = db.Column(db.TIMESTAMP, nullable=True)
    duration = db.Column(db.Integer, nullable=True)

    model = db.relationship('Model', backref='processes', lazy=True)
    dataset = db.relationship('Dataset', backref='processes', lazy=True)
    user = db.relationship('User', backref='processes', lazy=True)

    def to_dict(self):
        return {
            'process_id': self.process_id,
            'process_type': self.process_type,
            'model_id': self.model_id,
            'dataset_id': self.dataset_id,
            'user_id': self.user_id,
            'status': self.status,
            'error_message': self.error_message,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration
        }

# TestResult Model
class TestResult(db.Model):
    __tablename__ = 'test_results'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    instance_id = db.Column(db.Integer, db.ForeignKey('instances.instance_id'), nullable=False)  # ForeignKey to instances table
    test_type = db.Column(db.String(255), nullable=False)
    accuracy = db.Column(db.Numeric(5, 2), nullable=True)
    result_details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())

    instance = db.relationship('Instance', backref='test_results', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'test_type': self.test_type,
            'accuracy': self.accuracy,
            'result_details': self.result_details,
            'created_at': self.created_at
        }

# TrainingProcess Model
class TrainingProcess(db.Model):
    __tablename__ = 'training_process'

    training_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.model_id'), nullable=True)  # ForeignKey to model table
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.dataset_id'), nullable=True)  # ForeignKey to datasets table
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # ForeignKey to users table
    parameters = db.Column(db.JSON, nullable=True)
    training_status = db.Column(db.String(50), nullable=True)
    training_accuracy = db.Column(db.Numeric(5, 2), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.TIMESTAMP, nullable=True, server_default=func.current_timestamp())
    end_time = db.Column(db.TIMESTAMP, nullable=True)

    model = db.relationship('Model', backref='training_process', lazy=True)
    dataset = db.relationship('Dataset', backref='training_process', lazy=True)
    user = db.relationship('User', backref='training_process', lazy=True)

    def to_dict(self):
        return {
            'training_id': self.training_id,
            'model_id': self.model_id,
            'dataset_id': self.dataset_id,
            'user_id': self.user_id,
            'parameters': self.parameters,
            'training_status': self.training_status,
            'training_accuracy': self.training_accuracy,
            'error_message': self.error_message,
            'start_time': self.start_time,
            'end_time': self.end_time
        }

