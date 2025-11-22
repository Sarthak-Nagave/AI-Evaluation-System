from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, AptitudeQuestion, AptitudeTest, CodingQuestion, CodingTest, NonTechnicalQuestion, NonTechnicalTest, MockInterview, ProctorLog
from config import Config
from aptitude_ai import evaluate_non_technical_answer, evaluate_mock_interview 
import os
import requests
import json
import random
import time
from datetime import datetime
from io import BytesIO
# PDF Generation Imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from sqlalchemy import func, case # Needed for new chart queries

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- Hardcoded Institute List ---
INSTITUTES = [
    'Nutan College of Engineering and Research',
    'Nutan Maharashtra Institude of Technology'
]

# --- Hardcoded Aptitude Questions (60 Total) ---
APTITUDE_SEEDS = [
    {"q": "If A is 4 times as efficient as B, and they complete a work in 20 days. How many days will A take to complete the work alone?", "a": "25 days", "b": "30 days", "c": "20 days", "d": "15 days", "correct": "B"},
    {"q": "A train passes a platform 90 m long in 30 seconds and a man standing on the platform in 15 seconds. The speed of the train is:", "a": "10.8 km/hr", "b": "21.6 km/hr", "c": "18 km/hr", "d": "7.2 km/hr", "correct": "B"},
    {"q": "What is the simple interest on Rs. 8000 for 3 years at 5% per annum?", "a": "1200", "b": "1000", "c": "800", "d": "1500", "correct": "A"},
    {"q": "A man buys an article for Rs. 500 and sells it for Rs. 600. His profit percentage is:", "a": "15%", "b": "20%", "c": "10%", "d": "25%", "correct": "B"},
    {"q": "Find the average of first 50 natural numbers.", "a": "25", "b": "25.5", "c": "26", "d": "24.5", "correct": "B"},
    {"q": "If 6 men can complete a work in 10 days, how many days will 15 men take?", "a": "4 days", "b": "5 days", "c": "6 days", "d": "3 days", "correct": "A"},
    {"q": "A can do a piece of work in 10 days and B in 15 days. How long will they take if they work together?", "a": "5 days", "b": "6 days", "c": "7.5 days", "d": "8 days", "correct": "B"},
    {"q": "The ratio of two numbers is 3:4 and their sum is 84. The greater number is:", "a": "36", "b": "48", "c": "42", "d": "56", "correct": "B"},
    {"q": "What is 15% of 250?", "a": "37.5", "b": "30", "c": "45", "d": "32.5", "correct": "A"},
    {"q": "At what rate of interest per annum will Rs. 1000 double in 5 years?", "a": "15%", "b": "20%", "c": "10%", "d": "25%", "correct": "B"},
    {"q": "The perimeter of a square is 32 cm. Its area is:", "a": "64 sq cm", "b": "16 sq cm", "c": "32 sq cm", "d": "128 sq cm", "correct": "A"},
    {"q": "A car covers a distance of 800 km in 10 hours. Its speed in m/s is:", "a": "22.22 m/s", "b": "80 m/s", "c": "25 m/s", "d": "8 m/s", "correct": "A"},
    {"q": "If the length of a rectangle is increased by 20% and the width is decreased by 10%, the percentage change in area is:", "a": "8% increase", "b": "10% increase", "c": "8% decrease", "d": "10% decrease", "correct": "A"},
    {"q": "The sum of the ages of 5 children is 60 years. What is the average age?", "a": "10 years", "b": "12 years", "c": "15 years", "d": "14 years", "correct": "B"},
    {"q": "What is the next number in the series: 2, 6, 12, 20, 30, ...?", "a": "42", "b": "40", "c": "44", "d": "46", "correct": "A"},
    {"q": "Find the odd one out: Car, Bus, Bicycle, Truck, Scooter", "a": "Car", "b": "Bus", "c": "Bicycle", "d": "Truck", "correct": "C"},
    {"q": "If 'WATER' is coded as 'XBUFS', then 'FIRE' is coded as:", "a": "GJRG", "b": "GJSG", "c": "GJTH", "d": "GJSI", "correct": "A"},
    {"q": "A is the brother of B. C is the father of A. D is the sister of E. E is the mother of B. Who is D to C?", "a": "Sister", "b": "Wife", "c": "Mother", "d": "Daughter", "correct": "B"},
    {"q": "In a certain code, 'RIVER' is written as 'REVIR'. How is 'OCEAN' written in that code?", "a": "NAECO", "b": "NAOCE", "c": "NACE", "d": "NAEC", "correct": "A"},
    {"q": "SCD, TEF, UGH, ___, WKL. What is the next term?", "a": "CMN", "b": "VIJ", "c": "IJT", "d": "IJW", "correct": "B"},
    {"q": "Pointing to a man, a woman said, 'His mother is the only daughter of my mother.' How is the woman related to the man?", "a": "Sister", "b": "Mother", "c": "Aunt", "d": "Wife", "correct": "B"},
    {"q": "If the day before yesterday was Sunday, what is the day after tomorrow?", "a": "Wednesday", "b": "Thursday", "c": "Friday", "d": "Saturday", "correct": "B"},
    {"q": "How many meaningful English words can be formed from the letters R T A W using each letter only once?", "a": "One", "b": "Two", "c": "Three", "d": "Four", "correct": "B"},
    {"q": "What letter comes next in the sequence: A, C, F, J, O, __?", "a": "U", "b": "V", "c": "T", "d": "S", "correct": "A"}, # A+2, C+3, F+4, J+5, O+6=U
    {"q": "If P ÷ Q means P is the father of Q, and P × Q means P is the mother of Q, then T × S ÷ R means:", "a": "R is the grandfather of T", "b": "T is the grandmother of R", "c": "T is the mother of R", "d": "R is the son of T", "correct": "B"},
    {"q": "Find the odd one out: Sphere, Circle, Square, Triangle", "a": "Sphere", "b": "Circle", "c": "Square", "d": "Triangle", "correct": "A"},
    {"q": "In a row of boys, if A who is 10th from the left and B who is 9th from the right interchange their positions, A becomes 15th from the left. How many boys are there in the row?", "a": "23", "b": "24", "c": "25", "d": "26", "correct": "A"},
    {"q": "If 'Light' is called 'Dark', 'Dark' is called 'Green', 'Green' is called 'Blue', then what is the color of the blood?", "a": "Dark", "b": "Green", "c": "Blue", "d": "Light", "correct": "B"},
    {"q": "Arrange the words in a meaningful sequence: 1. Gold 2. Iron 3. Sand 4. Platinum 5. Diamond", "a": "3, 2, 1, 5, 4", "b": "3, 1, 2, 4, 5", "c": "4, 5, 1, 2, 3", "d": "5, 4, 3, 2, 1", "correct": "A"},
    {"q": "Find the missing number: 1, 8, 27, 64, __, 216", "a": "100", "b": "125", "c": "150", "d": "180", "correct": "B"},
    {"q": "Choose the synonym for 'Ephemeral'.", "a": "Permanent", "b": "Transient", "c": "Substantial", "d": "Vast", "correct": "B"},
    {"q": "Choose the antonym for 'Perilous'.", "a": "Hazardous", "b": "Safe", "c": "Risk-taking", "d": "Intrepid", "correct": "B"},
    {"q": "Select the correct spelling:", "a": "Occurence", "b": "Occurrence", "c": "Occurrance", "d": "Ocurrence", "correct": "B"},
    {"q": "A person who is fluent in two languages is:", "a": "Monolingual", "b": "Polyglot", "c": "Bilingual", "d": "Linguist", "correct": "C"},
    {"q": "Fill in the blank: He is afraid ___ spiders.", "a": "of", "b": "from", "c": "with", "d": "at", "correct": "A"},
    {"q": "What is the collective noun for a group of lions?", "a": "Herd", "b": "Flock", "c": "Pride", "d": "Swarm", "correct": "C"},
    {"q": "Choose the correctly punctuated sentence.", "a": "She shouted, 'Wait for me!'", "b": "She shouted wait for me!", "c": "She shouted 'Wait for me'.", "d": "She shouted 'Wait for me'!", "correct": "A"},
    {"q": "The idiom 'To bury the hatchet' means:", "a": "To hide something", "b": "To make peace", "c": "To fight aggressively", "d": "To dig up treasure", "correct": "B"},
    {"q": "Fill in the blank: Neither John ___ his sister were at the party.", "a": "or", "b": "nor", "c": "but", "d": "and", "correct": "B"},
    {"q": "Choose the passive voice: The cat chased the mouse.", "a": "The cat was chased by the mouse.", "b": "The mouse was chased by the cat.", "c": "The mouse chased the cat.", "d": "The cat has chased the mouse.", "correct": "B"},
    {"q": "Which data structure uses LIFO principle?", "a": "Queue", "b": "Stack", "c": "Array", "d": "Linked List", "correct": "B"},
    {"q": "The primary key must contain:", "a": "Unique values", "b": "NULL values", "c": "Duplicate values", "d": "Two columns", "correct": "A"},
    {"q": "Which of the following is not an operating system?", "a": "Windows", "b": "Linux", "c": "Python", "d": "macOS", "correct": "C"},
    {"q": "What is the time complexity of binary search?", "a": "O(n)", "b": "O(n^2)", "c": "O(log n)", "d": "O(1)", "correct": "C"},
    {"q": "In OOP, the mechanism of hiding the implementation details and showing only the functionality is known as:", "a": "Inheritance", "b": "Polymorphism", "c": "Abstraction", "d": "Encapsulation", "correct": "C"},
    {"q": "Which layer of the OSI model is responsible for routing?", "a": "Data Link Layer", "b": "Transport Layer", "c": "Network Layer", "d": "Application Layer", "correct": "C"},
    {"q": "The standard protocol for wireless communication in smart homes is:", "a": "HTML", "b": "HTTP", "c": "ZigBee", "d": "TCP", "correct": "C"},
    {"q": "Which transistor technology is dominant in modern microprocessors?", "a": "BJT", "b": "JFET", "c": "CMOS", "d": "MOSFET (JFET)", "correct": "C"},
    {"q": "The efficiency of a Carnot engine depends on:", "a": "Working substance", "b": "Temperature of source and sink", "c": "Engine size", "d": "Heat supplied", "correct": "B"},
    {"q": "The concept of 'Deep Learning' is a subset of:", "a": "Data Science", "b": "Machine Learning", "c": "Statistics", "d": "Expert Systems", "correct": "B"},
    {"q": "Which sorting algorithm has the worst-case time complexity of O(n^2) and best-case of O(n)?", "a": "Merge Sort", "b": "Quick Sort", "c": "Insertion Sort", "d": "Heap Sort", "correct": "C"},
    {"q": "A firewall is primarily used for:", "a": "Data compression", "b": "Security", "c": "Speed optimization", "d": "Virus detection", "correct": "B"},
    {"q": "The equation E = 1/2 * m * v^2 relates to which type of energy?", "a": "Potential Energy", "b": "Kinetic Energy", "c": "Thermal Energy", "d": "Elastic Energy", "correct": "B"},
    {"q": "In electronics, the device used to increase the power of a signal is called:", "a": "Oscillator", "b": "Amplifier", "c": "Rectifier", "d": "Modulator", "correct": "B"},
    {"q": "Which of these is a non-volatile memory type?", "a": "RAM", "b": "Cache", "c": "ROM", "d": "Registers", "correct": "C"},
    {"q": "Which command is used to display the current working directory in Linux?", "a": "ls", "b": "cd", "c": "pwd", "d": "dir", "correct": "C"},
    {"q": "The force responsible for the operation of a simple electric motor is:", "a": "Gravitational force", "b": "Magnetic force", "c": "Nuclear force", "d": "Electrostatic force", "correct": "B"},
    {"q": "In mechanical engineering, the ability of a material to absorb energy and plastically deform without fracturing is called:", "a": "Hardness", "b": "Brittleness", "c": "Toughness", "d": "Stiffness", "correct": "C"},
    {"q": "What is the decimal equivalent of the binary number 1011?", "a": "9", "b": "10", "c": "11", "d": "13", "correct": "C"},
    {"q": "A leap year has how many days?", "a": "365", "b": "366", "c": "367", "d": "364", "correct": "B"}
]


# Initialize database and create admin users
def init_db():
    with app.app_context():
        # FIX: Create 'instance' directory if missing for SQLite
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        if db_uri and db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                    print(f"Created missing directory: {db_dir}")
                except Exception as e:
                    print(f"Error creating directory {db_dir}: {e}")
                    raise
        
        db.create_all()
        
        # Security warning for default password
        is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ENVIRONMENT') == 'production'
        
        if Config.ADMIN_PASSWORD == 'Nmit@ncer':
            print("\n" + "="*70)
            print("⚠️  WARNING: Using default admin password!")
            print("Please set ADMIN_PASSWORD environment variable for production.")
            print("Default password should ONLY be used for development/testing.")
            print("="*70 + "\n")
            
            if is_production:
                print("Continuing in development mode despite warning. Set ADMIN_PASSWORD for secure use.")
        
        # Create admin users (only if they don't exist)
        for i, email in enumerate(Config.ADMIN_EMAILS):
            admin = User.query.filter_by(email=email).first()
            if not admin:
                unique_prn = f"ADMIN-{i+1}" 
                admin = User(
                    email=email,
                    # --- UI UPDATE: Use first_name and last_name ---
                    first_name=email.split('@')[0].title(),
                    last_name="Admin",
                    is_admin=True,
                    prn=unique_prn, 
                    department=Config.DEPARTMENTS[0], 
                    institute=INSTITUTES[0]
                )
                admin.set_password(Config.ADMIN_PASSWORD)
                db.session.add(admin)
                print(f"Created admin account: {email}")
        
        # Create Hardcoded Aptitude Questions (60 Total)
        if AptitudeQuestion.query.count() == 0:
             print(f"Seeding {len(APTITUDE_SEEDS)} default aptitude questions for all departments...")
             
             for dept in Config.DEPARTMENTS:
                 for q_data in APTITUDE_SEEDS:
                     question = AptitudeQuestion(
                         department=dept, 
                         question=q_data['q'],
                         option_a=q_data['a'],
                         option_b=q_data['b'],
                         option_c=q_data['c'],
                         option_d=q_data['d'],
                         correct_answer=q_data['correct']
                     )
                     db.session.add(question)
             print("Aptitude questions seeded successfully.")

        # Create default coding questions with detailed descriptions
        if CodingQuestion.query.count() == 0:
            print(f"Seeding {Config.CODING_QUESTIONS_COUNT} default coding questions...")
            coding_questions = [
                {
                    "title": "Problem 1: Two Sum",
                    "description": """
                        <p>Given an array of integers <code>nums</code> and an integer <code>target</code>, return <i>indices of the two numbers such that they add up to <code>target</code></i>.</p>
                        <p>You may assume that each input would have <b>exactly one solution</b>, and you may not use the same element twice.</p>
                        <br/>
                        <p><b>Input Format:</b></p>
                        <ul class='list-disc list-inside ml-4'>
                            <li>The first line contains an integer <code>n</code> (the number of elements in the array).</li>
                            <li>The second line contains <code>n</code> space-separated integers (the elements of <code>nums</code>).</li>
                            <li>The third line contains the integer <code>target</code>.</li>
                        </ul>
                        <br/>
                        <p><b>Output Format:</b></p>
                        <p class='ml-4'>Print two space-separated indices (0-based).</p>
                        <br/>
                        <p><b>Example 1:</b></p>
                        <pre class='bg-gray-100 p-2 rounded-md text-sm'><b>Input:</b>\n4\n2 7 11 15\n9\n<b>Output:</b>\n0 1</pre>
                        <p><b>Explanation:</b> Because nums[0] + nums[1] == 9, we return 0 and 1.</p>
                        <br/>
                        <p><b>Example 2:</b></p>
                        <pre class='bg-gray-100 p-2 rounded-md text-sm'><b>Input:</b>\n3\n3 2 4\n6\n<b>Output:</b>\n1 2</pre>
                    """,
                    "difficulty": "Easy",
                    "test_cases": json.dumps([
                        {"input": "4\n2 7 11 15\n9", "output": "0 1"},
                        {"input": "3\n3 2 4\n6", "output": "1 2"}
                    ]),
                    "is_sql": False
                },
                {
                    "title": "Problem 2: Reverse a String",
                    "description": """
                        <p>Write a function that reverses a string. The input string is given as a single line.</p>
                        <br/>
                        <p><b>Input Format:</b></p>
                        <p class='ml-4'>A single line containing the string <code>s</code>.</p>
                        <br/>
                        <p><b>Output Format:</b></p>
                        <p class='ml-4'>Print the reversed string.</p>
                        <br/>
                        <p><b>Example 1:</b></p>
                        <pre class='bg-gray-100 p-2 rounded-md text-sm'><b>Input:</b>\nhello\n<b>Output:</b>\nolleh</pre>
                        <br/>
                        <p><b>Example 2:</b></p>
                        <pre class='bg-gray-100 p-2 rounded-md text-sm'><b>Input:</b>\nworld\n<b>Output:</b>\ndlrow</pre>
                    """,
                    "difficulty": "Easy",
                    "test_cases": json.dumps([
                        {"input": "hello", "output": "olleh"},
                        {"input": "world", "output": "dlrow"}
                    ]),
                    "is_sql": False
                },
                {
                    "title": "Problem 3: Find Duplicate Number",
                    "description": """
                        <p>Given an array of integers <code>nums</code> containing <code>n + 1</code> integers where each integer is in the range <code>[1, n]</code> inclusive.</p>
                        <p>There is only <b>one repeated number</b> in <code>nums</code>, return <i>this repeated number</i>.</p>
                        <p>You must solve the problem <b>without modifying the array <code>nums</code></b> and use only constant extra space.</p>
                        <br/>
                        <p><b>Input Format:</b></p>
                        <ul class='list-disc list-inside ml-4'>
                            <li>The first line contains <code>n+1</code> (the number of elements).</li>
                            <li>The second line contains <code>n+1</code> space-separated integers.</li>
                        </ul>
                        <br/>
                        <p><b>Output Format:</b></p>
                        <p class='ml-4'>Print the single repeated integer.</p>
                        <br/>
                        <p><b>Example 1:</b></p>
                        <pre class='bg-gray-100 p-2 rounded-md text-sm'><b>Input:</b>\n5\n1 3 4 2 2\n<b>Output:</b>\n2</pre>
                        <br/>
                        <p><b>Example 2:</b></p>
                        <pre class='bg-gray-100 p-2 rounded-md text-sm'><b>Input:</b>\n5\n3 1 3 4 2\n<b>Output:</b>\n3</pre>
                    """,
                    "difficulty": "Medium",
                    "test_cases": json.dumps([
                        {"input": "5\n1 3 4 2 2", "output": "2"},
                        {"input": "5\n3 1 3 4 2", "output": "3"}
                    ]),
                    "is_sql": False
                },
                {
                    "title": "Problem 4: SQL Query (Employees)",
                    "description": """
                        <p>You are given a table named <code>employees</code> with the following schema:</p>
                        <pre class='bg-gray-100 p-2 rounded-md text-sm'>
CREATE TABLE employees (
  id INT,
  name VARCHAR(100),
  salary INT,
  department VARCHAR(50)
);</pre>
                        <br/>
                        <p>Write a SQL query to find the names of all employees who have a salary greater than 50000 and work in the 'Engineering' department.</p>
                        <br/>
                        <p><b>Task:</b></p>
                        <p class='ml-4'>Write <b>only the SELECT statement</b> required to fetch this data.</p>
                        <br/>
                        <p><b>Expected Output (Example):</b></p>
                        <p class='ml-4'>If an employee 'John Doe' has a salary of 60000 in 'Engineering', his name should be in the result set.</p>
                    """,
                    "difficulty": "Easy",
                    "expected_output": "SELECT name FROM employees WHERE salary > 50000 AND department = 'Engineering';",
                    "is_sql": True
                }
            ]
            
            for q in coding_questions:
                question = CodingQuestion(
                    title=q['title'],
                    description=q['description'],
                    difficulty=q['difficulty'],
                    is_sql=q.get('is_sql', False)
                )
                if 'test_cases' in q:
                    question.test_cases = q['test_cases']
                if 'expected_output' in q:
                    question.expected_output = q['expected_output']
                db.session.add(question)
            print("Coding questions seeded successfully.")
        
        # Create default non-technical questions
        if NonTechnicalQuestion.query.count() == 0:
            print(f"Seeding {Config.NON_TECHNICAL_QUESTIONS_COUNT} default non-technical questions...")
            nt_questions = [
                "Describe a challenging project you worked on and how you overcame the obstacles.",
                "What are your strengths and weaknesses as an engineer?",
                "How do you stay updated with the latest technologies in your field?",
                "Explain a situation where you had to work in a team. What was your role?"
            ]
            
            for q_text in nt_questions:
                question = NonTechnicalQuestion(question=q_text)
                db.session.add(question)
            print("Non-technical questions seeded successfully.")
        
        db.session.commit()
        print("Database initialization and seeding complete!")

# --- Helper Functions for Round Progression ---
def check_round_completion(user):
    aptitude_test = AptitudeTest.query.filter_by(user_id=user.id).first()
    
    round1_completed = aptitude_test is not None
    round2_completed = False
    
    if user.department in Config.TECHNICAL_DEPARTMENTS:
        coding_tests = CodingTest.query.filter_by(user_id=user.id).all()
        # ---
        # --- USER REQUEST: Mark as complete after 1 submission
        # ---
        round2_completed = len(coding_tests) > 0 
    else:
        nt_tests = NonTechnicalTest.query.filter_by(user_id=user.id).all()
        # ---
        # --- USER REQUEST: Mark as complete after 1 submission
        # ---
        round2_completed = len(nt_tests) > 0
        
    mock_interview = MockInterview.query.filter_by(user_id=user.id).first()
    round3_completed = mock_interview is not None
    
    return round1_completed, round2_completed, round3_completed

# --- Routes ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    # --- UI UPDATE: Render new standalone index page ---
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        
        prn = data.get('prn') 
        institute = data.get('institute')
        
        # --- UI UPDATE: Check for new name fields ---
        if not prn or not institute or not data.get('email') or not data.get('first_name') or not data.get('last_name') or not data.get('department') or not data.get('password'):
             return jsonify({'success': False, 'message': 'Missing required fields (Name, PRN, Email, Institute, Department, Password)'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        if User.query.filter_by(prn=prn).first():
            return jsonify({'success': False, 'message': 'PRN already registered'}), 400
            
        user = User(
            email=data['email'],
            # --- UI UPDATE: Save new name fields ---
            first_name=data['first_name'],
            last_name=data['last_name'],
            prn=prn,
            institute=institute,
            department=data['department'],
            is_admin=False
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    # --- UI UPDATE: Pass departments and institutes to new register page ---
    return render_template('register.html', departments=Config.DEPARTMENTS, institutes=INSTITUTES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            login_user(user)
            return jsonify({
                'success': True,
                'is_admin': user.is_admin,
                'redirect': url_for('admin_dashboard') if user.is_admin else url_for('student_dashboard')
            })
        
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    # --- UI UPDATE: Render new login page ---
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    r1, r2, r3 = check_round_completion(current_user)
    
    is_technical = current_user.department in Config.TECHNICAL_DEPARTMENTS
    
    # --- UI UPDATE: Render new student dashboard ---
    return render_template('student_dashboard.html',
                           aptitude_completed=r1,
                           round2_completed=r2,
                           interview_completed=r3,
                           is_technical=is_technical,
                           department=current_user.department)

# Aptitude Test Routes
@app.route('/aptitude/start')
@login_required
def aptitude_start():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    r1, _, _ = check_round_completion(current_user)
    if r1:
        return redirect(url_for('student_dashboard'))
    
    return render_template('aptitude.html', question_count=Config.APTITUDE_QUESTIONS_COUNT)

@app.route('/api/aptitude/questions', methods=['GET'])
@login_required
def get_aptitude_questions():
    if not current_user.is_authenticated:
        return jsonify({'error': 'User not logged in'}), 401
    
    r1, _, _ = check_round_completion(current_user)
    if r1:
        return jsonify({'error': 'Aptitude test already completed'}), 403
        
    if not current_user.department:
        return jsonify({'error': 'User department is missing. Please contact administration.'}), 400

    questions = AptitudeQuestion.query.filter_by(department=current_user.department).all()
    
    if len(questions) < Config.APTITUDE_QUESTIONS_COUNT:
        return jsonify({
            'error': f'Database only contains {len(questions)} questions for department "{current_user.department}". Expected {Config.APTITUDE_QUESTIONS_COUNT}. This usually means the database was seeded incorrectly or the user data is corrupted. Please clear the database and re-register.'
        }), 500
    
    questions_list = list(questions)
    random.shuffle(questions_list)
    questions_list = questions_list[:Config.APTITUDE_QUESTIONS_COUNT]
    
    questions_data = []
    question_ids = []
    
    for q in questions_list:
        questions_data.append({
            'id': q.id,
            'question': q.question,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d
            }
        })
        question_ids.append(q.id)
    
    return jsonify({
        'questions': questions_data,
        'question_order': question_ids
    })

@app.route('/api/aptitude/submit', methods=['POST'])
@login_required
def submit_aptitude():
    r1, _, _ = check_round_completion(current_user)
    if r1:
        return jsonify({'error': 'Aptitude test already submitted'}), 403
        
    data = request.get_json()
    answers = data.get('answers', {})
    time_taken = data.get('time_taken', 0)
    question_order = data.get('question_order', [])
    
    score = 0
    for qid, answer in answers.items():
        question = AptitudeQuestion.query.get(int(qid))
        if question and question.correct_answer == answer:
            score += 1
    
    test = AptitudeTest(
        user_id=current_user.id,
        score=score,
        total_questions=Config.APTITUDE_QUESTIONS_COUNT,
        time_taken=time_taken
    )
    test.set_answers(answers)
    test.set_question_order(question_order)
    
    db.session.add(test)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'score': score,
        'total': Config.APTITUDE_QUESTIONS_COUNT
    })

# Coding Test Routes
@app.route('/coding/start')
@login_required
def coding_start():
    if current_user.is_admin or current_user.department not in Config.TECHNICAL_DEPARTMENTS:
        return redirect(url_for('student_dashboard'))
        
    r1, r2, _ = check_round_completion(current_user)
    if not r1:
        return redirect(url_for('student_dashboard'))
        
    if r2:
        return redirect(url_for('student_dashboard'))
    
    return render_template('coding.html', question_count=Config.CODING_QUESTIONS_COUNT)

@app.route('/api/coding/questions', methods=['GET'])
@login_required
def get_coding_questions():
    r1, r2, _ = check_round_completion(current_user)
    if not r1 or r2 or current_user.department not in Config.TECHNICAL_DEPARTMENTS:
        return jsonify({'error': 'Prerequisites not met or test completed'}), 403
        
    questions = CodingQuestion.query.all()
    
    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'title': q.title,
            'description': q.description,
            'difficulty': q.difficulty,
            'is_sql': q.is_sql
        })
    
    return jsonify({'questions': questions_data})

@app.route('/api/coding/run', methods=['POST'])
@login_required
def run_code():
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'python')
    question_id = data.get('question_id')
    
    r1, r2, _ = check_round_completion(current_user)
    if not r1 or r2 or current_user.department not in Config.TECHNICAL_DEPARTMENTS:
        return jsonify({'error': 'Prerequisites not met or test completed'}), 403
    
    language_map = {
        'python': 71,
        'c': 50,
        'cpp': 54,
        'java': 62,
        'sql': 82
    }
    
    question = CodingQuestion.query.get(question_id)
    
    if question.is_sql:
        return jsonify({
            'success': False,
            'output': None,
            'error': 'SQL queries cannot be "run". Please "Submit" your query for evaluation.'
        })
    
    # Judge0 API Execution Logic
    try:
        test_cases = question.get_test_cases()
        if not test_cases:
            return jsonify({
                'success': False,
                'output': None,
                'error': 'No test cases defined for this question.'
            })
            
        test_input = test_cases[0]['input']
        
        url = f"{Config.JUDGE0_API_URL}/submissions?base64_encoded=false&wait=true&fields=stdout,stderr,status_id,language_id"
        
        payload = {
            "source_code": code,
            "language_id": language_map.get(language, 71),
            "stdin": test_input
        }
        
        headers = {
            "X-RapidAPI-Key": Config.JUDGE0_API_KEY,
            "X-RapidAPI-Host": Config.JUDGE0_API_HOST,
            "Content-Type": "application/json"
        }
        
        if not Config.JUDGE0_API_KEY:
            # --- Simulation Block (If no API Key is set) ---
            output = f"Code execution SIMULATED. Set JUDGE0_API_KEY for real execution.\nLanguage: {language}\nInput: {test_input[:50]}..."
            error = None
            return jsonify({
                'success': True,
                'output': output,
                'error': error
            })
            # --- End Simulation Block ---

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        
        result = response.json()
        
        status_id = result.get('status_id')
        
        if status_id == 3: # Accepted
            output = result.get('stdout', '').strip()
            # Check if output matches expected output
            expected_output = test_cases[0]['output']
            if output == expected_output:
                output = f"Test Case 1 Passed!\n\nOutput:\n{output}"
                error = None
            else:
                output = f"Test Case 1 Failed.\n\nExpected:\n{expected_output}\n\nGot:\n{output}"
                error = None # Not a runtime error, just wrong answer
        elif status_id == 6: # Compilation Error
            output = "Compilation Error"
            error = result.get('stderr', '')
        elif status_id in [7, 8, 9, 10, 11, 12]: # Runtime Errors
            output = f"Runtime Error (Status: {status_id})"
            error = result.get('stderr', '')
        else:
            output = f"Execution Failed (Status: {status_id})"
            error = result.get('stderr', '') or result.get('message', 'Unknown error')

        return jsonify({
            'success': True,
            'output': output,
            'error': error
        })
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Judge0 API Error: {e}")
        return jsonify({
            'success': False,
            'output': None,
            'error': f"API connection error: {e}"
        })
    except Exception as e:
        app.logger.error(f"Unexpected error in run_code: {e}")
        return jsonify({
            'success': False,
            'output': None,
            'error': str(e)
        })

@app.route('/api/coding/submit', methods=['POST'])
@login_required
def submit_code():
    data = request.get_json()
    question_id = data.get('question_id')
    code = data.get('code', '')
    language = data.get('language', 'python')
    output = data.get('output', '')
    error = data.get('error', '')
    
    r1, r2, _ = check_round_completion(current_user)
    if not r1 or current_user.department not in Config.TECHNICAL_DEPARTMENTS:
        return jsonify({'error': 'Prerequisites not met'}), 403
    
    existing_submission = CodingTest.query.filter_by(
        user_id=current_user.id,
        question_id=question_id
    ).first()
    
    if existing_submission:
        return jsonify({'success': False, 'message': 'Already submitted this question'}), 400
    
    submission = CodingTest(
        user_id=current_user.id,
        question_id=question_id,
        code=code,
        language=language,
        output=output,
        error=error,
        score=0 # Score 0, admin will review
    )
    
    db.session.add(submission)
    db.session.commit()
    
    # Re-check completion status AFTER submitting
    r1, r2_new, _ = check_round_completion(current_user)
    
    return jsonify({
        'success': True,
        'round2_complete': r2_new, # This will now be true if 1+ submissions
        'message': f"Submission saved. {Config.CODING_QUESTIONS_COUNT - len(CodingTest.query.filter_by(user_id=current_user.id).all())} questions remaining."
    })

# Non-Technical Test Routes
@app.route('/non-technical/start')
@login_required
def non_technical_start():
    if current_user.is_admin or current_user.department not in Config.NON_TECHNICAL_DEPARTMENTS:
        return redirect(url_for('student_dashboard'))
        
    r1, r2, _ = check_round_completion(current_user)
    if not r1:
        return redirect(url_for('student_dashboard'))
        
    if r2:
        return redirect(url_for('student_dashboard'))
    
    return render_template('non_technical.html', question_count=Config.NON_TECHNICAL_QUESTIONS_COUNT)

@app.route('/api/non-technical/questions', methods=['GET'])
@login_required
def get_non_technical_questions():
    r1, r2, _ = check_round_completion(current_user)
    if not r1 or r2 or current_user.department not in Config.NON_TECHNICAL_DEPARTMENTS:
        return jsonify({'error': 'Prerequisites not met or test completed'}), 403
        
    questions = NonTechnicalQuestion.query.all()[:Config.NON_TECHNICAL_QUESTIONS_COUNT]
    
    questions_data = []
    for q in questions:
        submitted = NonTechnicalTest.query.filter_by(
            user_id=current_user.id,
            question_id=q.id
        ).first()
        
        questions_data.append({
            'id': q.id,
            'question': q.question,
            'submitted': submitted is not None,
            'score': submitted.ai_score if submitted else None,
            'feedback': submitted.ai_feedback if submitted else None
        })
    
    return jsonify({'questions': questions_data})

@app.route('/api/non-technical/submit', methods=['POST'])
@login_required
def submit_non_technical():
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer', '')
    
    r1, r2, _ = check_round_completion(current_user)
    if not r1 or r2 or current_user.department not in Config.NON_TECHNICAL_DEPARTMENTS:
        return jsonify({'error': 'Prerequisites not met or test completed'}), 403

    existing_submission = NonTechnicalTest.query.filter_by(
        user_id=current_user.id,
        question_id=question_id
    ).first()
    
    if existing_submission:
        return jsonify({'success': False, 'message': 'Already submitted this question'}), 400
    
    question = NonTechnicalQuestion.query.get(question_id)
    
    score, feedback = evaluate_non_technical_answer(question.question, answer)
    
    submission = NonTechnicalTest(
        user_id=current_user.id,
        question_id=question_id,
        answer=answer,
        ai_score=score,
        ai_feedback=feedback
    )
    
    db.session.add(submission)
    db.session.commit()
    
    r1, r2_new, _ = check_round_completion(current_user)
    
    return jsonify({
        'success': True,
        'score': score,
        'feedback': feedback,
        'round2_complete': r2_new,
        'message': f"Submission saved. {Config.NON_TECHNICAL_QUESTIONS_COUNT - len(NonTechnicalTest.query.filter_by(user_id=current_user.id).all())} questions remaining."
    })

# Mock Interview Routes
@app.route('/interview/start')
@login_required
def interview_start():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    r1, r2, r3 = check_round_completion(current_user)
    if not r1 or not r2:
        return redirect(url_for('student_dashboard'))
        
    if r3:
        return redirect(url_for('student_dashboard'))
    
    return render_template('interview.html')

@app.route('/api/interview/submit', methods=['POST'])
@login_required
def submit_interview():
    r1, r2, r3 = check_round_completion(current_user)
    if not r1 or not r2 or r3:
        return jsonify({'error': 'Prerequisites not met or interview already submitted'}), 403
        
    data = request.get_json()
    transcript = data.get('transcript', '')
    
    evaluation = evaluate_mock_interview(transcript)
    
    overall_score = (
        evaluation.get('communication_score', 0) +
        evaluation.get('confidence_score', 0) +
        evaluation.get('clarity_score', 0) +
        evaluation.get('relevance_score', 0)
    ) // 4
    
    interview = MockInterview(
        user_id=current_user.id,
        transcript=transcript,
        communication_score=evaluation.get('communication_score', 0),
        confidence_score=evaluation.get('confidence_score', 0),
        clarity_score=evaluation.get('clarity_score', 0),
        relevance_score=evaluation.get('relevance_score', 0),
        overall_score=overall_score,
        feedback=evaluation.get('feedback', 'No detailed feedback provided.')
    )
    
    db.session.add(interview)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'scores': evaluation
    })

@app.route('/api/proctor/log', methods=['POST'])
@login_required
def log_violation():
    data = request.get_json()
    
    log = ProctorLog(
        user_id=current_user.id,
        violation_type=data.get('type', 'unknown'),
        round_name=data.get('round', ''),
        details=json.dumps(data.get('details', {}))
    )
    
    db.session.add(log)
    db.session.commit()
    
    violation_count = ProctorLog.query.filter_by(user_id=current_user.id).count()
    
    return jsonify({
        'success': True,
        'violation_count': violation_count,
        # --- FIX: Strict 5-violation limit ---
        'flagged': violation_count > Config.MAX_VIOLATIONS
    })

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    # --- UI UPDATE: Render new admin dashboard ---
    # The student data is now fetched via API
    #
    # *** THIS IS THE FIX: ***
    # Pass the 'Config' object to the template
    return render_template('admin_dashboard.html',
                           departments=Config.DEPARTMENTS,
                           Config=Config)

@app.route('/api/admin/students', methods=['GET'])
@login_required
def get_students():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    department = request.args.get('department', '')
    
    query = User.query.filter_by(is_admin=False)
    if department:
        query = query.filter_by(department=department)
    
    students = query.all()
    
    students_data = []
    for student in students:
        aptitude = AptitudeTest.query.filter_by(user_id=student.id).first()
        interview = MockInterview.query.filter_by(user_id=student.id).first()
        
        round2_score = 'N/A'
        
        if student.department in Config.TECHNICAL_DEPARTMENTS:
            coding_tests = CodingTest.query.filter_by(user_id=student.id).all()
            if coding_tests:
                # --- LOGIC CHANGE: This will now show 1/4, 2/4 etc. ---
                round2_score = f"{len(coding_tests)}/{Config.CODING_QUESTIONS_COUNT} Submitted"
        else:
            nt_tests = NonTechnicalTest.query.filter_by(user_id=student.id).all()
            if nt_tests:
                avg_score = sum(t.ai_score for t in nt_tests) / len(nt_tests)
                round2_score = f"{avg_score:.1f}/100"
        
        violations = ProctorLog.query.filter_by(user_id=student.id).count()
        
        students_data.append({
            'id': student.id,
            # --- UI UPDATE: Use new name property ---
            'name': student.name,
            'prn': student.prn or 'N/A', 
            'email': student.email,
            'department': student.department,
            'institute': student.institute, 
            'aptitude_score': f"{aptitude.score}/{aptitude.total_questions}" if aptitude else 'N/A',
            'round2_score': round2_score,
            'interview_score': f"{interview.overall_score}/100" if interview else 'N/A',
            'violations': violations,
            'flagged': violations > Config.MAX_VIOLATIONS
        })
    
    return jsonify({'students': students_data})

@app.route('/api/admin/student/<int:student_id>', methods=['GET'])
@login_required
def get_student_details(student_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = db.session.get(User, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    aptitude = AptitudeTest.query.filter_by(user_id=student_id).first()
    coding_tests = CodingTest.query.filter_by(user_id=student_id).all()
    nt_tests = NonTechnicalTest.query.filter_by(user_id=student_id).all()
    interview = MockInterview.query.filter_by(user_id=student_id).first()
    violations = ProctorLog.query.filter_by(user_id=student_id).all()
    
    data = {
        'student': {
            # --- UI UPDATE: Use new name property ---
            'name': student.name,
            'email': student.email,
            'prn': student.prn or 'N/A', 
            'department': student.department,
            'institute': student.institute
        },
        'aptitude': {
            'completed': aptitude is not None,
            'score': aptitude.score if aptitude else 0,
            'total': aptitude.total_questions if aptitude else 0,
            'time_taken_sec': aptitude.time_taken if aptitude else 0,
            'answers': aptitude.get_answers() if aptitude else {},
            'question_order': aptitude.get_question_order() if aptitude else []
        },
        'coding': [{
            'id': ct.id,
            'question_title': ct.question.title,
            'code': ct.code,
            'language': ct.language,
            'output': ct.output,
            'error': ct.error
        } for ct in coding_tests],
        'non_technical': [{
            'id': nt.id,
            'question': nt.question.question,
            'answer': nt.answer,
            'ai_score': nt.ai_score,
            'ai_feedback': nt.ai_feedback
        } for nt in nt_tests],
        'interview': {
            'completed': interview is not None,
            'overall_score': interview.overall_score if interview else 0,
            'communication_score': interview.communication_score if interview else 0,
            'confidence_score': interview.confidence_score if interview else 0,
            'clarity_score': interview.clarity_score if interview else 0,
            'relevance_score': interview.relevance_score if interview else 0,
            'feedback': interview.feedback if interview else '',
            'transcript': interview.transcript if interview else ''
        },
        'violations': [{
            'type': v.violation_type,
            'round': v.round_name,
            'timestamp': v.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'details': v.get_details()
        } for v in violations]
    }
    
    return jsonify(data)

# --- NEW ADMIN API ENDPOINTS ---

@app.route('/api/admin/stats', methods=['GET'])
@login_required
def get_admin_stats():
    """Provides KPI card data for the admin dashboard."""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    total_students = User.query.filter_by(is_admin=False).count()
    
    # "Completed" = finished all 3 rounds
    completed_students = db.session.query(User.id).filter(
        User.is_admin == False,
        User.aptitude_tests.any(),
        User.mock_interviews.any()
    ).count()
    
    # "Active" = started round 1 but not finished round 3
    active_interviews = db.session.query(User.id).filter(
        User.is_admin == False,
        User.aptitude_tests.any(),
        ~User.mock_interviews.any()
    ).count()
    
    # Avg score (combining Aptitude and Interview)
    avg_apti_score = db.session.query(func.avg(AptitudeTest.score)).scalar() or 0
    avg_hr_score = db.session.query(func.avg(MockInterview.overall_score)).scalar() or 0
    
    # Simple average logic (can be refined)
    total_avg_score = (avg_apti_score / 60 * 100 + avg_hr_score) / 2 if (avg_apti_score > 0 and avg_hr_score > 0) else (avg_apti_score / 60 * 100 or avg_hr_score)

    stats = {
        'total_students': total_students,
        'active_interviews': active_interviews,
        'completed': completed_students,
        'average_score': round(total_avg_score, 1)
    }
    return jsonify(stats)

@app.route('/api/admin/charts', methods=['GET'])
@login_required
def get_chart_data():
    """Provides data for all 4 admin dashboard charts."""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    # 1. Department Performance (Bar Chart)
    dept_performance = {}
    for dept in Config.DEPARTMENTS:
        # Get average aptitude score for this dept
        avg_score = db.session.query(func.avg(AptitudeTest.score)).join(User).filter(User.department == dept).scalar()
        dept_performance[dept] = round(avg_score, 1) if avg_score else 0
        
    # 2. Performance Trend (Line Chart) - Mock data for 5 weeks
    performance_trend = {
        'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'],
        'data': [65, 68, 72, 71, 75] # Mock data
    }
    
    # 3. Enrollment Distribution (Bar Chart)
    enrollment_dist_query = db.session.query(User.department, func.count(User.id)).filter(User.is_admin == False).group_by(User.department).all()
    enrollment_dist = {dept: count for dept, count in enrollment_dist_query}
    
    # 4. Score Distribution (Pie Chart) - Based on Aptitude scores
    
    # FIX for Aptitude score buckets (out of 60)
    # 0-24 (Fail), 25-40 (Avg), 41-50 (Good), 51-60 (Excellent)
    score_dist_query_apti = db.session.query(
        func.sum(case((AptitudeTest.score.between(0, 24), 1), else_=0)),
        func.sum(case((AptitudeTest.score.between(25, 40), 1), else_=0)),
        func.sum(case((AptitudeTest.score.between(41, 50), 1), else_=0)),
        func.sum(case((AptitudeTest.score.between(51, 60), 1), else_=0))
    ).one()

    score_dist = {
        'labels': ['0-24 (Fail)', '25-40 (Average)', '41-50 (Good)', '51-60 (Excellent)'],
        'data': [
            score_dist_query_apti[0] or 0,
            score_dist_query_apti[1] or 0,
            score_dist_query_apti[2] or 0,
            score_dist_query_apti[3] or 0
        ]
    }
    
    chart_data = {
        'dept_performance': dept_performance,
        'performance_trend': performance_trend,
        'enrollment_dist': enrollment_dist,
        'score_dist': score_dist
    }
    return jsonify(chart_data)


# --- (End of New Admin Endpoints) ---

@app.route('/api/admin/export/<int:student_id>', methods=['GET'])
@login_required
def export_student_pdf(student_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = db.session.get(User, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Fetch all details
    aptitude = AptitudeTest.query.filter_by(user_id=student_id).first()
    coding_tests = CodingTest.query.filter_by(user_id=student_id).all()
    nt_tests = NonTechnicalTest.query.filter_by(user_id=student_id).all()
    interview = MockInterview.query.filter_by(user_id=student_id).first()
    violations = ProctorLog.query.filter_by(user_id=student_id).all()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        leftMargin=0.5*inch, 
        rightMargin=0.5*inch, 
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()

    # ✅ FIX — prevent duplicate style errors
    if "Code" not in styles.byName:
        styles.add(ParagraphStyle(
            name='Code', 
            fontName='Courier', 
            fontSize=8, 
            leading=10, 
            textColor=colors.black, 
            backColor=colors.lavenderblush,
            borderPadding=4, 
            borderRadius=2, 
            wordWrap='CJK'
        ))

    if "Output" not in styles.byName:
        styles.add(ParagraphStyle(
            name='Output', 
            fontName='Courier', 
            fontSize=8, 
            leading=10, 
            textColor=colors.darkgreen, 
            backColor=colors.honeydew,
            borderPadding=4, 
            borderRadius=2, 
            wordWrap='CJK'
        ))

    if "Error" not in styles.byName:
        styles.add(ParagraphStyle(
            name='Error', 
            fontName='Courier', 
            fontSize=8, 
            leading=10, 
            textColor=colors.red, 
            backColor=colors.mistyrose,
            borderPadding=4, 
            borderRadius=2, 
            wordWrap='CJK'
        ))

    if "Transcript" not in styles.byName:
        styles.add(ParagraphStyle(
            name='Transcript', 
            fontName='Helvetica', 
            fontSize=9, 
            leading=12, 
            backColor=colors.whitesmoke,
            borderPadding=4, 
            borderRadius=2
        ))

    story = []

    # Title
    # --- UI UPDATE: Use new name property ---
    title = Paragraph(f"<b>Interview Evaluation Report - {student.name}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Student info
    info_text = f"<b>Email:</b> {student.email}<br/><b>PRN:</b> {student.prn or 'N/A'}<br/><b>Institute:</b> {student.institute}<br/><b>Department:</b> {student.department}<br/><b>Proctoring Violations:</b> <font color='red'>{len(violations)}</font>"
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Round 1: Aptitude
    story.append(Paragraph("<b>--- Round 1: Aptitude Test ---</b>", styles['h2']))
    if aptitude:
        story.append(Paragraph(f"Score: <b>{aptitude.score}/{aptitude.total_questions}</b>", styles['Normal']))
        story.append(Paragraph(f"Time Taken: <b>{aptitude.time_taken // 60}m {aptitude.time_taken % 60}s</b>", styles['Normal']))
    else:
        story.append(Paragraph("Status: Not Completed", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Round 2: Technical / Non-Technical
    if student.department in Config.TECHNICAL_DEPARTMENTS:
        story.append(Paragraph("<b>--- Round 2: Technical Coding Test ---</b>", styles['h2']))
        if coding_tests:
            story.append(Paragraph(f"Submissions: <b>{len(coding_tests)}/{Config.CODING_QUESTIONS_COUNT}</b>", styles['Normal']))
            for ct in coding_tests:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(f"<b>Q: {ct.question.title} ({ct.language.upper()})</b>", styles['h3']))
                story.append(Paragraph("<u>Code Submitted:</u>", styles['Normal']))
                story.append(Paragraph(ct.code.replace('\n', '<br/>'), styles['Code']))
                if ct.output:
                    story.append(Paragraph("<u>Output:</u>", styles['Normal']))
                    story.append(Paragraph(ct.output.replace('\n', '<br/>'), styles['Output']))
                if ct.error:
                    story.append(Paragraph("<u>Error:</u>", styles['Normal']))
                    story.append(Paragraph(ct.error.replace('\n', '<br/>'), styles['Error']))
        else:
            story.append(Paragraph("Status: Not Completed", styles['Normal']))
    else:
        story.append(Paragraph("<b>--- Round 2: Non-Technical Assessment ---</b>", styles['h2']))
        if nt_tests:
            story.append(Paragraph(f"Submissions: <b>{len(nt_tests)}/{Config.NON_TECHNICAL_QUESTIONS_COUNT}</b>", styles['Normal']))
            for nt in nt_tests:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(f"<b>Q: {nt.question.question}</b>", styles['h3']))
                story.append(Paragraph(f"AI Score: <b>{nt.ai_score}/100</b>", styles['Normal']))
                story.append(Paragraph("<u>AI Feedback:</u>", styles['Normal']))
                story.append(Paragraph(nt.ai_feedback, styles['Transcript']))
                story.append(Paragraph("<u>Answer:</u>", styles['Normal']))
                story.append(Paragraph(nt.answer, styles['Transcript']))
        else:
            story.append(Paragraph("Status: Not Completed", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Round 3: Mock Interview
    story.append(Paragraph("<b>--- Round 3: HR Mock Interview ---</b>", styles['h2']))
    if interview:
        story.append(Paragraph(f"Overall Score: <b>{interview.overall_score}/100</b>", styles['Normal']))
        data_scores = [
            ['Metric', 'Score'],
            ['Communication', f"{interview.communication_score}/100"],
            ['Confidence', f"{interview.confidence_score}/100"],
            ['Clarity', f"{interview.clarity_score}/100"],
            ['Relevance', f"{interview.relevance_score}/100"],
        ]
        score_table = Table(data_scores, colWidths=[2.5*inch, 2.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(score_table)
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("<b>AI Feedback:</b>", styles['Normal']))
        story.append(Paragraph(interview.feedback, styles['Transcript']))
        story.append(Paragraph("<b>Full Transcript:</b>", styles['Normal']))
        story.append(Paragraph(interview.transcript.replace('\n', '<br/>'), styles['Transcript']))
    else:
        story.append(Paragraph("Status: Not Completed", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Proctoring Logs
    story.append(Paragraph("<b>--- Proctoring Logs ---</b>", styles['h2']))
    if violations:
        log_data = [['Timestamp', 'Round', 'Type', 'Details']]
        for v in violations:
            log_data.append([
                v.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                v.round_name,
                v.violation_type,
                Paragraph(json.dumps(v.get_details()), styles['Normal'])
            ])
        log_table = Table(log_data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 3.3*inch])
        log_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(log_table)
    else:
        story.append(Paragraph("No violations recorded.", styles['Normal']))


    doc.build(story)
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{student.name}_report.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)