from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, AptitudeQuestion, AptitudeTest, CodingQuestion, CodingTest, NonTechnicalQuestion, NonTechnicalTest, MockInterview, ProctorLog
from config import Config
from aptitude_ai import generate_aptitude_questions, evaluate_non_technical_answer, evaluate_mock_interview
import os
import requests
import json
import random
import time
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Initialize database and create admin users
def init_db():
    with app.app_context():
        db.create_all()
        
        # Security warning for default password
        is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ENVIRONMENT') == 'production'
        
        if Config.ADMIN_PASSWORD == 'Nmit@ncer':
            print("\n" + "="*70)
            print("⚠️  WARNING: Using default admin password!")
            print("Please set ADMIN_PASSWORD environment variable for production.")
            print("Default password should ONLY be used for development/testing.")
            print("="*70 + "\n")
            
            # Production failsafe: abort if in production environment with default password
            if is_production:
                print("\n" + "="*70)
                print("❌ FATAL: Cannot start in production mode with default password!")
                print("Set ADMIN_PASSWORD environment variable and restart.")
                print("="*70 + "\n")
                raise RuntimeError("Production deployment blocked: default admin password detected")
        
        # Create admin users (only if they don't exist)
        for email in Config.ADMIN_EMAILS:
            admin = User.query.filter_by(email=email).first()
            if not admin:
                admin = User(
                    email=email,
                    name=email.split('@')[0].title(),
                    is_admin=True
                )
                admin.set_password(Config.ADMIN_PASSWORD)
                db.session.add(admin)
                print(f"Created admin account: {email}")
        
        # Create default coding questions
        if CodingQuestion.query.count() == 0:
            coding_questions = [
                {
                    "title": "Two Sum Problem",
                    "description": "Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.\n\nInput Format: First line contains n (array size), second line contains n integers, third line contains target.\n\nOutput Format: Print two space-separated indices (0-based).",
                    "difficulty": "Easy",
                    "test_cases": json.dumps([
                        {"input": "4\n2 7 11 15\n9", "output": "0 1"},
                        {"input": "3\n3 2 4\n6", "output": "1 2"}
                    ]),
                    "is_sql": False
                },
                {
                    "title": "Fibonacci Sequence",
                    "description": "Write a program to find the nth Fibonacci number.\n\nInput Format: Single integer n\n\nOutput Format: Print the nth Fibonacci number.",
                    "difficulty": "Easy",
                    "test_cases": json.dumps([
                        {"input": "5", "output": "5"},
                        {"input": "10", "output": "55"}
                    ]),
                    "is_sql": False
                },
                {
                    "title": "Reverse a String",
                    "description": "Write a program to reverse a given string.\n\nInput Format: Single line containing a string\n\nOutput Format: Print the reversed string.",
                    "difficulty": "Easy",
                    "test_cases": json.dumps([
                        {"input": "hello", "output": "olleh"},
                        {"input": "world", "output": "dlrow"}
                    ]),
                    "is_sql": False
                },
                {
                    "title": "SQL: Employee Query",
                    "description": "Write a SQL query to fetch all employees from the 'employees' table where salary > 50000.\n\nTable Schema:\nCREATE TABLE employees (id INT, name VARCHAR(100), salary INT, department VARCHAR(50));\n\nWrite only the SELECT statement.",
                    "difficulty": "Easy",
                    "expected_output": "SELECT * FROM employees WHERE salary > 50000;",
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
        
        # Create default non-technical questions
        if NonTechnicalQuestion.query.count() == 0:
            nt_questions = [
                "Describe a challenging project you worked on and how you overcame the obstacles.",
                "What are your strengths and weaknesses as an engineer?",
                "How do you stay updated with the latest technologies in your field?",
                "Explain a situation where you had to work in a team. What was your role?"
            ]
            
            for q_text in nt_questions:
                question = NonTechnicalQuestion(question=q_text)
                db.session.add(question)
        
        db.session.commit()
        print("Database initialized successfully!")

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        user = User(
            email=data['email'],
            name=data['name'],
            department=data['department'],
            is_admin=False
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    return render_template('register.html', departments=Config.DEPARTMENTS)

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
    
    # Get test status
    aptitude_test = AptitudeTest.query.filter_by(user_id=current_user.id).first()
    mock_interview = MockInterview.query.filter_by(user_id=current_user.id).first()
    
    if current_user.department in Config.TECHNICAL_DEPARTMENTS:
        coding_tests = CodingTest.query.filter_by(user_id=current_user.id).all()
        round2_completed = len(coding_tests) >= 4
    else:
        nt_tests = NonTechnicalTest.query.filter_by(user_id=current_user.id).all()
        round2_completed = len(nt_tests) >= 4
    
    return render_template('student_dashboard.html',
                         aptitude_completed=aptitude_test is not None,
                         round2_completed=round2_completed,
                         interview_completed=mock_interview is not None,
                         is_technical=current_user.department in Config.TECHNICAL_DEPARTMENTS)

# Aptitude Test Routes
@app.route('/aptitude/start')
@login_required
def aptitude_start():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Check if already taken
    if AptitudeTest.query.filter_by(user_id=current_user.id).first():
        return redirect(url_for('student_dashboard'))
    
    return render_template('aptitude.html')

@app.route('/api/aptitude/questions', methods=['GET'])
@login_required
def get_aptitude_questions():
    # Get or generate questions for department
    questions = AptitudeQuestion.query.filter_by(department=current_user.department).all()
    
    if len(questions) < Config.APTITUDE_QUESTIONS_COUNT:
        # Generate using AI
        generated = generate_aptitude_questions(current_user.department, Config.APTITUDE_QUESTIONS_COUNT)
        
        for q in generated:
            question = AptitudeQuestion(
                department=current_user.department,
                question=q['question'],
                option_a=q['option_a'],
                option_b=q['option_b'],
                option_c=q['option_c'],
                option_d=q['option_d'],
                correct_answer=q['correct_answer']
            )
            db.session.add(question)
        
        db.session.commit()
        questions = AptitudeQuestion.query.filter_by(department=current_user.department).all()
    
    # Randomize order
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
    data = request.get_json()
    answers = data.get('answers', {})
    time_taken = data.get('time_taken', 0)
    question_order = data.get('question_order', [])
    
    # Calculate score
    score = 0
    for qid, answer in answers.items():
        question = AptitudeQuestion.query.get(int(qid))
        if question and question.correct_answer == answer:
            score += 1
    
    # Save test
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
    
    return render_template('coding.html')

@app.route('/api/coding/questions', methods=['GET'])
@login_required
def get_coding_questions():
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
    
    # Language ID mapping for Judge0
    language_map = {
        'python': 71,
        'c': 50,
        'cpp': 54,
        'java': 62,
        'sql': 82
    }
    
    question = CodingQuestion.query.get(question_id)
    
    if question.is_sql:
        # For SQL, just save the code
        return jsonify({
            'success': True,
            'output': 'SQL query saved. Admin will review.',
            'error': None
        })
    
    # Use Judge0 API (free version - judge0.com)
    try:
        test_cases = question.get_test_cases()
        if test_cases:
            test_input = test_cases[0]['input']
        else:
            test_input = ""
        
        # Using a free Judge0 CE instance
        url = "https://judge0-ce.p.rapidapi.com/submissions"
        
        payload = {
            "source_code": code,
            "language_id": language_map.get(language, 71),
            "stdin": test_input
        }
        
        # For development, simulate execution
        output = f"Code executed successfully.\nLanguage: {language}\nInput: {test_input[:50]}..."
        error = None
        
        return jsonify({
            'success': True,
            'output': output,
            'error': error
        })
        
    except Exception as e:
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
    
    # Save submission
    submission = CodingTest(
        user_id=current_user.id,
        question_id=question_id,
        code=code,
        language=language,
        output=output,
        error=error,
        score=0  # Admin will score
    )
    
    db.session.add(submission)
    db.session.commit()
    
    return jsonify({'success': True})

# Non-Technical Test Routes
@app.route('/non-technical/start')
@login_required
def non_technical_start():
    if current_user.is_admin or current_user.department not in Config.NON_TECHNICAL_DEPARTMENTS:
        return redirect(url_for('student_dashboard'))
    
    return render_template('non_technical.html')

@app.route('/api/non-technical/questions', methods=['GET'])
@login_required
def get_non_technical_questions():
    questions = NonTechnicalQuestion.query.all()
    
    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'question': q.question
        })
    
    return jsonify({'questions': questions_data})

@app.route('/api/non-technical/submit', methods=['POST'])
@login_required
def submit_non_technical():
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer', '')
    
    question = NonTechnicalQuestion.query.get(question_id)
    
    # Evaluate using AI
    score, feedback = evaluate_non_technical_answer(question.question, answer)
    
    # Save submission
    submission = NonTechnicalTest(
        user_id=current_user.id,
        question_id=question_id,
        answer=answer,
        ai_score=score,
        ai_feedback=feedback
    )
    
    db.session.add(submission)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'score': score,
        'feedback': feedback
    })

# Mock Interview Routes
@app.route('/interview/start')
@login_required
def interview_start():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Check if already taken
    if MockInterview.query.filter_by(user_id=current_user.id).first():
        return redirect(url_for('student_dashboard'))
    
    return render_template('interview.html')

@app.route('/api/interview/submit', methods=['POST'])
@login_required
def submit_interview():
    data = request.get_json()
    transcript = data.get('transcript', '')
    
    # Evaluate using AI
    evaluation = evaluate_mock_interview(transcript)
    
    overall_score = (
        evaluation['communication_score'] +
        evaluation['confidence_score'] +
        evaluation['clarity_score'] +
        evaluation['relevance_score']
    ) // 4
    
    # Save interview
    interview = MockInterview(
        user_id=current_user.id,
        transcript=transcript,
        communication_score=evaluation['communication_score'],
        confidence_score=evaluation['confidence_score'],
        clarity_score=evaluation['clarity_score'],
        relevance_score=evaluation['relevance_score'],
        overall_score=overall_score,
        feedback=evaluation['feedback']
    )
    
    db.session.add(interview)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'scores': evaluation
    })

# Proctoring Routes
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
    
    # Check violation count
    violation_count = ProctorLog.query.filter_by(user_id=current_user.id).count()
    
    return jsonify({
        'success': True,
        'violation_count': violation_count,
        'flagged': violation_count > Config.MAX_VIOLATIONS
    })

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    students = User.query.filter_by(is_admin=False).all()
    
    return render_template('admin_dashboard.html',
                         students=students,
                         departments=Config.DEPARTMENTS)

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
        
        if student.department in Config.TECHNICAL_DEPARTMENTS:
            coding_tests = CodingTest.query.filter_by(user_id=student.id).all()
            round2_score = sum(t.score for t in coding_tests)
        else:
            nt_tests = NonTechnicalTest.query.filter_by(user_id=student.id).all()
            round2_score = sum(t.ai_score for t in nt_tests) // len(nt_tests) if nt_tests else 0
        
        violations = ProctorLog.query.filter_by(user_id=student.id).count()
        
        students_data.append({
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'department': student.department,
            'aptitude_score': aptitude.score if aptitude else 'N/A',
            'round2_score': round2_score,
            'interview_score': interview.overall_score if interview else 'N/A',
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
    
    # Get all test data
    aptitude = AptitudeTest.query.filter_by(user_id=student_id).first()
    coding_tests = CodingTest.query.filter_by(user_id=student_id).all()
    nt_tests = NonTechnicalTest.query.filter_by(user_id=student_id).all()
    interview = MockInterview.query.filter_by(user_id=student_id).first()
    violations = ProctorLog.query.filter_by(user_id=student_id).all()
    
    data = {
        'student': {
            'name': student.name,
            'email': student.email,
            'department': student.department
        },
        'aptitude': {
            'score': aptitude.score if aptitude else None,
            'total': aptitude.total_questions if aptitude else None,
            'time_taken': aptitude.time_taken if aptitude else None
        } if aptitude else None,
        'coding_tests': [{
            'question_title': ct.question.title,
            'code': ct.code,
            'language': ct.language,
            'output': ct.output,
            'error': ct.error,
            'score': ct.score
        } for ct in coding_tests],
        'non_technical_tests': [{
            'question': nt.question.question,
            'answer': nt.answer,
            'score': nt.ai_score,
            'feedback': nt.ai_feedback
        } for nt in nt_tests],
        'interview': {
            'transcript': interview.transcript,
            'communication': interview.communication_score,
            'confidence': interview.confidence_score,
            'clarity': interview.clarity_score,
            'relevance': interview.relevance_score,
            'overall': interview.overall_score,
            'feedback': interview.feedback
        } if interview else None,
        'violations': [{
            'type': v.violation_type,
            'round': v.round_name,
            'timestamp': v.timestamp.isoformat(),
            'details': v.get_details()
        } for v in violations]
    }
    
    return jsonify(data)

@app.route('/api/admin/analytics', methods=['GET'])
@login_required
def get_analytics():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    analytics = {}
    
    for dept in Config.DEPARTMENTS:
        students = User.query.filter_by(department=dept, is_admin=False).all()
        
        aptitude_scores = []
        interview_scores = []
        
        for student in students:
            aptitude = AptitudeTest.query.filter_by(user_id=student.id).first()
            interview = MockInterview.query.filter_by(user_id=student.id).first()
            
            if aptitude:
                aptitude_scores.append(aptitude.score)
            if interview:
                interview_scores.append(interview.overall_score)
        
        analytics[dept] = {
            'total_students': len(students),
            'avg_aptitude': sum(aptitude_scores) / len(aptitude_scores) if aptitude_scores else 0,
            'avg_interview': sum(interview_scores) / len(interview_scores) if interview_scores else 0
        }
    
    return jsonify(analytics)

@app.route('/api/admin/export/<int:student_id>', methods=['GET'])
@login_required
def export_student_pdf(student_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    student = db.session.get(User, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"<b>Interview Evaluation Report - {student.name}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Student info
    info_text = f"<b>Email:</b> {student.email}<br/><b>Department:</b> {student.department}"
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Scores
    aptitude = AptitudeTest.query.filter_by(user_id=student_id).first()
    interview = MockInterview.query.filter_by(user_id=student_id).first()
    
    if aptitude:
        story.append(Paragraph(f"<b>Round 1 - Aptitude Score:</b> {aptitude.score}/{aptitude.total_questions}", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
    
    if interview:
        story.append(Paragraph(f"<b>Round 3 - Mock Interview</b>", styles['Heading2']))
        story.append(Paragraph(f"Overall Score: {interview.overall_score}/100", styles['Normal']))
        story.append(Paragraph(f"Communication: {interview.communication_score}/100", styles['Normal']))
        story.append(Paragraph(f"Confidence: {interview.confidence_score}/100", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    doc.build(story)
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{student.name}_report.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
