# AI Interview Evaluation System

## Project Overview
A comprehensive Flask-based interview evaluation platform with AI-powered multi-round testing, anti-cheat proctoring, and admin analytics.

## Current Status
✅ **Fully Functional** - All features implemented and tested

## Key Features
1. **Multi-Round Testing System**
   - Round 1: AI-generated aptitude MCQs (60 questions per department)
   - Round 2: Coding tests (CS/AI/IT) or Non-technical (ENTC/ENC/Mech)
   - Round 3: Voice-based HR mock interviews

2. **Anti-Cheat Proctoring**
   - WebRTC camera monitoring
   - Fullscreen enforcement
   - Tab-switch detection
   - Violation logging

3. **Admin Dashboard**
   - Student management with department filtering
   - Performance analytics with Chart.js
   - PDF export functionality
   - Detailed student reports

## Technology Stack
- **Backend**: Python 3.11, Flask, SQLAlchemy, PostgreSQL
- **AI**: OpenAI GPT-3.5 for question generation and evaluation
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **APIs**: Web Speech API (voice), WebRTC (camera), Ace Editor (code)

## Admin Credentials (Development)
**Emails**: 
- dattatraykarande07@gmail.com
- virajbhambhure@gmail.com
- omkar01@gmail.com
- pranavkale@gmail.com

**Password**: Nmit@ncer (DEV ONLY - set ADMIN_PASSWORD env var for production)

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (auto-configured)
- `OPENAI_API_KEY`: Required for AI features (configured)
- `SESSION_SECRET`: Flask session secret (auto-configured)
- `ADMIN_PASSWORD`: Admin password (defaults to 'Nmit@ncer' in dev)

## Security Features
- Password hashing with Werkzeug
- Admin accounts created only on first run
- Production failsafe prevents startup with default password
- Environment-based secret management
- Anti-cheat violation tracking

## Project Structure
```
.
├── app.py                 # Main Flask application
├── models.py              # SQLAlchemy database models
├── config.py              # Configuration settings
├── aptitude_ai.py         # OpenAI integration for AI features
├── requirements.txt       # Python dependencies
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── student_dashboard.html
│   ├── aptitude.html
│   ├── coding.html
│   ├── non_technical.html
│   ├── interview.html
│   └── admin_dashboard.html
└── static/
    └── js/                # JavaScript files
        ├── proctoring.js
        ├── aptitude.js
        ├── coding.js
        ├── non_technical.js
        ├── interview.js
        └── admin.js
```

## Database Models
1. **users** - Student and admin accounts
2. **aptitude_questions** - MCQ question bank
3. **aptitude_tests** - Student test submissions
4. **coding_questions** - Programming challenges
5. **coding_tests** - Code submissions
6. **non_technical_questions** - Subjective questions
7. **non_technical_tests** - Subjective answers
8. **mock_interviews** - Interview transcripts and scores
9. **proctor_logs** - Anti-cheat violation logs

## Development Notes
- Application runs on port 5000 (required for Replit webview)
- Database automatically initializes on first run
- Default coding questions and admin accounts are seeded
- SQLAlchemy 2.x compatible (using Session.get instead of Query.get)

## Production Deployment Checklist
1. Set ADMIN_PASSWORD environment variable
2. Set ENVIRONMENT='production' or FLASK_ENV='production'
3. Use production WSGI server (Gunicorn)
4. Enable HTTPS/SSL
5. Install Tailwind CSS via npm (remove CDN)
6. Set debug=False
7. Configure proper firewall rules
8. Regular security audits

## Known Issues / Future Improvements
- Tailwind CSS currently uses CDN (should use npm for production)
- Judge0 API integration is simulated (needs API key for real execution)
- Consider adding video recording for interviews
- Add bulk student import/export via CSV
- Implement email notifications

## Browser Compatibility
- **Best**: Chrome, Edge (full Web Speech API support)
- **Limited**: Firefox (partial Web Speech API)
- **Not Supported**: Safari (no Web Speech API)

## Recent Updates
- ✅ Fixed admin password security (environment variable based)
- ✅ Added production failsafe for default passwords
- ✅ Fixed SQLAlchemy deprecation warnings
- ✅ Improved error handling for user lookups
- ✅ Added comprehensive security documentation

## Support
For technical issues, check:
1. Workflow logs in the Replit console
2. Browser console for frontend errors
3. README.md for detailed documentation
