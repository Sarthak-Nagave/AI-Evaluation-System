from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # --- UI UPDATE: Split 'name' into 'first_name' and 'last_name' ---
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    
    prn = db.Column(db.String(50), unique=True, nullable=True) 
    password_hash = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100)) 
    institute = db.Column(db.String(100)) 
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    aptitude_tests = db.relationship('AptitudeTest', backref='student', lazy=True, cascade='all, delete-orphan')
    coding_tests = db.relationship('CodingTest', backref='student', lazy=True, cascade='all, delete-orphan')
    non_technical_tests = db.relationship('NonTechnicalTest', backref='student', lazy=True, cascade='all, delete-orphan')
    mock_interviews = db.relationship('MockInterview', backref='student', lazy=True, cascade='all, delete-orphan')
    proctor_logs = db.relationship('ProctorLog', backref='student', lazy=True, cascade='all, delete-orphan')
    
    # Helper property to get full name
    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AptitudeQuestion(db.Model):
    __tablename__ = 'aptitude_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100), nullable=False, index=True) 
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AptitudeTest(db.Model):
    __tablename__ = 'aptitude_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=60)
    time_taken = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    question_order = db.Column(db.Text)
    
    def set_answers(self, answers_dict):
        self.answers = json.dumps(answers_dict)
    
    def get_answers(self):
        return json.loads(self.answers) if self.answers else {}
    
    def set_question_order(self, order_list):
        self.question_order = json.dumps(order_list)
    
    def get_question_order(self):
        return json.loads(self.question_order) if self.question_order else []

class CodingQuestion(db.Model):
    __tablename__ = 'coding_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20))
    test_cases = db.Column(db.Text)
    is_sql = db.Column(db.Boolean, default=False)
    expected_output = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_test_cases(self, cases_list):
        self.test_cases = json.dumps(cases_list)
    
    def get_test_cases(self):
        return json.loads(self.test_cases) if self.test_cases else []

class CodingTest(db.Model):
    __tablename__ = 'coding_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('coding_questions.id'), nullable=False)
    code = db.Column(db.Text)
    language = db.Column(db.String(20))
    output = db.Column(db.Text)
    error = db.Column(db.Text)
    score = db.Column(db.Integer, default=0)
    execution_time = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    question = db.relationship('CodingQuestion', backref='submissions')

class NonTechnicalQuestion(db.Model):
    __tablename__ = 'non_technical_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NonTechnicalTest(db.Model):
    __tablename__ = 'non_technical_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('non_technical_questions.id'), nullable=False)
    answer = db.Column(db.Text)
    ai_score = db.Column(db.Integer, default=0)
    ai_feedback = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    question = db.relationship('NonTechnicalQuestion', backref='submissions')

class MockInterview(db.Model):
    __tablename__ = 'mock_interviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transcript = db.Column(db.Text)
    communication_score = db.Column(db.Integer, default=0)
    confidence_score = db.Column(db.Integer, default=0)
    clarity_score = db.Column(db.Integer, default=0)
    relevance_score = db.Column(db.Integer, default=0)
    overall_score = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProctorLog(db.Model):
    __tablename__ = 'proctor_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    violation_type = db.Column(db.String(50), nullable=False)
    round_name = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)
    
    def set_details(self, details_dict):
        self.details = json.dumps(details_dict)
    
    def get_details(self):
        return json.loads(self.details) if self.details else {}