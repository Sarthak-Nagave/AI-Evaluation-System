import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key-change-in-production'
    
    # FIX: Use SQLALCHEMY_DATABASE_URI from the environment, which is what your .env file defines.
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL') or 'sqlite:///instance/app.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    JUDGE0_API_URL = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY = os.environ.get('JUDGE0_API_KEY', '')
    JUDGE0_API_HOST = "judge0-ce.p.rapidapi.com"
    
    ADMIN_EMAILS = [
        'dattatraykarande07@gmail.com',
        'virajbhambhure@gmail.com',
        'omkar01@gmail.com',
        'pranavkale@gmail.com'
    ]
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Nmit@ncer')
    
    # --- FINALIZED FULL NAMES ---
    DEPARTMENTS = [
        'Computer Science', 
        'Artificial Intelligence', 
        'Information Technology', 
        'Electronics and Telecommunication', 
        'Electronics', 
        'Mechanical Engineering'
    ]
    TECHNICAL_DEPARTMENTS = [
        'Computer Science', 
        'Artificial Intelligence', 
        'Information Technology'
    ]
    NON_TECHNICAL_DEPARTMENTS = [
        'Electronics and Telecommunication', 
        'Electronics', 
        'Mechanical Engineering'
    ]
    
    MAX_VIOLATIONS = 5
    APTITUDE_QUESTIONS_COUNT = 60
    CODING_QUESTIONS_COUNT = 4
    NON_TECHNICAL_QUESTIONS_COUNT = 4