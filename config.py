import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
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
    ADMIN_PASSWORD = 'Nmit@ncer'
    
    DEPARTMENTS = ['CS', 'AI', 'IT', 'ENTC', 'ENC', 'Mech']
    TECHNICAL_DEPARTMENTS = ['CS', 'AI', 'IT']
    NON_TECHNICAL_DEPARTMENTS = ['ENTC', 'ENC', 'Mech']
    
    MAX_VIOLATIONS = 5
    APTITUDE_QUESTIONS_COUNT = 60
    CODING_QUESTIONS_COUNT = 4
    NON_TECHNICAL_QUESTIONS_COUNT = 4
