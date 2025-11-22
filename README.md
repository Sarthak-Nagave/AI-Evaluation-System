# 🧠 AI Evaluation System

### **A Complete AI-Powered Student Assessment Platform**

Built with **Flask + Python + Tailwind + SQLite + Judge0 API**

---

## 📌 Overview

**AI Evaluation System** is a full-featured online testing platform used for college placements, mock assessments, and technical screening.
It provides:

* **Aptitude Test (60 MCQs)**
* **Coding Test (with Judge0 Code Execution API)**
* **Non-Technical Assessment (AI-scored answers)**
* **HR Mock Interview (AI Transcript Scoring)**
* **Live Proctoring**

  * Camera monitoring
  * Tab switch detection
  * Fullscreen enforcement
  * Right-click & DevTools blocking
  * Violation logging

Admin users get a full dashboard to analyze scores, export PDF reports, and verify student integrity.

---

## 🚀 Features

### 🎯 Round 1 — Aptitude Test

* 60 MCQs auto-seeded for each department
* Randomized question order
* Timer, progress bar
* Proctoring enabled

### 💻 Round 2 — Coding Test

* Supports Python / C / C++ / Java
* Integrated **Judge0 API** for compilation + execution
* SQL questions with manual admin review
* Auto-saving test cases

### 📝 Round 2 (Non-Technical Track)

* 4 descriptive questions
* AI scoring (communication, relevance, structure)

### 🎤 Round 3 — HR Mock Interview

* Student records response
* Auto transcript scoring (Communication, Confidence, Clarity, Relevance)

### 🔒 Proctoring System

* Camera access check
* Tab switch detection
* Enter/exit fullscreen
* Developer tools blocking
* All events logged into DB

---

## 🗃️ Folder Structure

```
AIEvalSystem/
│ app.py
│ config.py
│ models.py
│ aptitude_ai.py
│ main.py
│ requirements.txt
│ README.md
│ .env (not included in repo)
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── aptitude.html
│   ├── coding.html
│   ├── non_technical.html
│   ├── interview.html
│   ├── admin_dashboard.html
│   └── student_dashboard.html
│
├── static/
│   ├── css/
│   └── js/
│       ├── aptitude.js
│       ├── coding.js
│       ├── proctoring.js
│       └── interview.js
│
└── instance/
    └── app.db (auto-generated)
```

---

# ⚙️ Requirements

Create a virtual environment:

```
python -m venv venv
```

Activate:

Windows:

```
venv\Scripts\activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# 🔑 Environment Variables (`.env`)

Create a file:

```
OPENAI_API_KEY=your_key
JUDGE0_API_KEY=your_key
SESSION_SECRET=any_secure_key
ADMIN_PASSWORD=Nmit@ncer
SQLALCHEMY_DATABASE_URI=sqlite:///instance/app.db
```

---

# ▶️ Run the Project

```
python app.py
```

Server starts on:

```
http://127.0.0.1:5000
```

---

# 👨‍💻 Admin Panel Login

Default admin emails:

```
dattatraykarande07@gmail.com
virajbhambhure@gmail.com
omkar01@gmail.com
pranavkale@gmail.com
```

Default password:

```
Nmit@ncer
```

---

# 📄 PDF Export

Admins can export student performance as a professional PDF report including:

* Aptitude
* Coding answers
* Non-technical evaluation
* Interview transcript
* Proctoring logs

---

# 📊 Analytics Dashboard

Admin can view:

* Average aptitude score per department
* Interview performance
* Total students
* Violation count

---

# 🤝 Contributing

Pull requests are welcome!
For major changes, please open an issue first to discuss what you would like to change.

---

# 📜 License

```
MIT License
```

