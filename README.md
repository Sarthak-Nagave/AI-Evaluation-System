# AI Interview Evaluation System

A complete, production-ready AI-powered interview evaluation platform with multi-round testing, anti-cheat proctoring, and comprehensive analytics.

## Features

### 🎯 Multi-Round Testing System

#### Round 1: Aptitude Test
- 60 AI-generated MCQ questions tailored to each department
- Randomized question order per student
- Auto-scoring with instant results
- Time tracking and management
- Questions cover: logical reasoning, quantitative aptitude, verbal ability, and technical knowledge

#### Round 2: Technical/Non-Technical Assessment

**For Technical Departments (CS/AI/IT):**
- 4 coding questions (1 mandatory SQL)
- Support for multiple languages: Python, C, C++, Java, SQL
- Real-time code execution using Judge0 API
- Ace code editor with syntax highlighting
- Output and error display
- Auto-scoring capability

**For Non-Technical Departments (ENTC/ENC/Mech):**
- 4 subjective questions
- AI-powered evaluation (0-100 scoring)
- Detailed feedback on each answer
- Word count tracking

#### Round 3: HR Mock Interview
- Voice-based interview using Web Speech API
- Real-time speech-to-text transcription
- AI evaluation on 4 parameters:
  - Communication Skills (0-100)
  - Confidence (0-100)
  - Clarity (0-100)
  - Relevance (0-100)
- Comprehensive AI feedback

### 🛡️ Anti-Cheat Proctoring System

- **Camera Monitoring**: WebRTC-based continuous camera feed
- **Fullscreen Lock**: Automatic fullscreen enforcement
- **Tab Switch Detection**: Logs every tab switch attempt
- **Window Blur Detection**: Tracks focus loss events
- **Violation Logging**: All violations stored in database
- **Automatic Flagging**: Students flagged after exceeding violation limit (5)
- **Developer Tools Prevention**: Blocks common shortcuts for dev tools

### 👨‍💼 Admin Dashboard

- **Student Management**: View all students with comprehensive data
- **Department Filtering**: Filter students by department
- **Performance Analytics**: Department-wise performance charts
- **Detailed Views**:
  - Aptitude test scores
  - Coding submissions with code review
  - Non-technical answers with AI feedback
  - Mock interview transcripts with detailed scores
  - Proctoring violation logs
- **PDF Export**: Generate detailed student reports
- **Chart.js Visualizations**: Interactive performance charts

## Technology Stack

### Backend
- **Python 3.11**
- **Flask**: Web framework
- **SQLAlchemy**: ORM for database operations
- **Flask-Login**: User authentication
- **PostgreSQL**: Database (Neon-backed on Replit)
- **OpenAI API**: AI question generation and evaluation
- **ReportLab**: PDF generation

### Frontend
- **HTML5**
- **Tailwind CSS**: Responsive styling
- **Vanilla JavaScript**: No framework dependencies
- **Web Speech API**: Voice recognition
- **WebRTC**: Camera access
- **Ace Editor**: Code editing
- **Chart.js**: Data visualization

## Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL database
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd <project-directory>
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Create a `.env` file or set the following environment variables:
```
DATABASE_URL=<your-postgresql-url>
OPENAI_API_KEY=<your-openai-api-key>
SESSION_SECRET=<random-secret-key>
ADMIN_PASSWORD=<your-secure-admin-password>
```

⚠️ **SECURITY WARNING**: The default admin password is `Nmit@ncer` (for development/testing only). 
You **MUST** set a custom `ADMIN_PASSWORD` environment variable for production deployments!

4. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Default Admin Credentials

⚠️ **CRITICAL SECURITY NOTE**: These credentials are for development/testing ONLY!

**Admin Emails:**
1. dattatraykarande07@gmail.com
2. virajbhambhure@gmail.com
3. omkar01@gmail.com
4. pranavkale@gmail.com

**Default Password (DEV/TEST ONLY):** `Nmit@ncer`

**For Production:**
- Set the `ADMIN_PASSWORD` environment variable to a strong, unique password
- Admin accounts are created only once (on first run)
- Existing admin passwords are NOT overwritten on subsequent runs
- Consider changing admin emails in `config.py` for your deployment

## User Roles

### Admin
- Access to admin dashboard
- View all student data
- Export reports to PDF
- View analytics and charts
- Review coding submissions
- Check proctoring violations

### Student
- Register with department selection
- Complete 3 rounds of testing
- View progress on dashboard
- Locked progression (must complete rounds in order)

## Departments

The system supports 6 departments:
- **CS** (Computer Science) - Technical track
- **AI** (Artificial Intelligence) - Technical track
- **IT** (Information Technology) - Technical track
- **ENTC** (Electronics & Telecommunication) - Non-technical track
- **ENC** (Electronics) - Non-technical track
- **Mech** (Mechanical) - Non-technical track

## Database Schema

### Tables
1. **users**: Student and admin information
2. **aptitude_questions**: MCQ questions by department
3. **aptitude_tests**: Student aptitude test results
4. **coding_questions**: Programming challenges
5. **coding_tests**: Student coding submissions
6. **non_technical_questions**: Subjective questions
7. **non_technical_tests**: Non-technical test submissions
8. **mock_interviews**: Interview transcripts and scores
9. **proctor_logs**: Anti-cheat violation logs

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - Student registration
- `GET /logout` - User logout

### Student Routes
- `GET /student/dashboard` - Student dashboard
- `GET /aptitude/start` - Start aptitude test
- `GET /coding/start` - Start coding test
- `GET /non-technical/start` - Start non-technical test
- `GET /interview/start` - Start mock interview

### API Routes
- `GET /api/aptitude/questions` - Get aptitude questions
- `POST /api/aptitude/submit` - Submit aptitude test
- `GET /api/coding/questions` - Get coding questions
- `POST /api/coding/run` - Run code
- `POST /api/coding/submit` - Submit coding solution
- `GET /api/non-technical/questions` - Get non-technical questions
- `POST /api/non-technical/submit` - Submit non-technical answer
- `POST /api/interview/submit` - Submit interview
- `POST /api/proctor/log` - Log proctoring violation

### Admin Routes
- `GET /admin/dashboard` - Admin dashboard
- `GET /api/admin/students` - Get students list
- `GET /api/admin/student/<id>` - Get student details
- `GET /api/admin/analytics` - Get analytics data
- `GET /api/admin/export/<id>` - Export student PDF

## Security Features

- **Password Hashing**: Using Werkzeug security (bcrypt-based)
- **Session Management**: Flask-Login with secure sessions
- **Environment Variables**: Secrets managed via environment variables
- **Admin Security**: 
  - Admins created only on first run (not overwritten)
  - Custom admin password via `ADMIN_PASSWORD` env var
  - Security warning displayed when using default password
- **Anti-cheat Monitoring**: All violations logged to database
- **Fullscreen Enforcement**: Prevents windowed cheating
- **Developer Tools Prevention**: Blocks common dev tool shortcuts

### Production Security Checklist

Before deploying to production, ensure:

1. ✅ Set `ADMIN_PASSWORD` environment variable (NOT the default)
2. ✅ Set strong `SESSION_SECRET` environment variable
3. ✅ Use production PostgreSQL database (not SQLite)
4. ✅ Set `debug=False` in Flask app
5. ✅ Enable HTTPS/SSL
6. ✅ Review and customize admin emails in config
7. ✅ Set up proper firewall rules
8. ✅ Regular security audits and updates

## Production Deployment

For production deployment, consider:

1. **Web Server**: Use Gunicorn or uWSGI instead of Flask development server
2. **Database**: Use production PostgreSQL instance
3. **Environment**: Set `debug=False` in production
4. **Tailwind CSS**: Install via npm instead of CDN
5. **HTTPS**: Enable SSL/TLS encryption
6. **Rate Limiting**: Add rate limiting for API endpoints
7. **Monitoring**: Set up error tracking and logging

## Browser Compatibility

- **Chrome**: Full support (recommended)
- **Edge**: Full support
- **Firefox**: Partial support (Web Speech API limited)
- **Safari**: Partial support (Web Speech API not supported)

For best experience, use Chrome or Edge browsers.

## License

This project is developed for educational and interview assessment purposes.

## Support

For issues or questions, please contact the development team.
