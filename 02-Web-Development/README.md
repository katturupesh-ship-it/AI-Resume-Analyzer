# ⚡ AI Resume Analyzer & ATS Optimization Engine

An intelligent web application that evaluates candidate resumes against ATS (Applicant Tracking System) criteria, analyzes job description alignment, and generates strategic career recommendations using the Google Gemini API.

---

## 📌 Features

- **Multimodal Resume Parsing**: Ingests and extracts content from digital text PDFs (`pypdf`) and transcribes scanned/image-based resumes (`.pdf`, `.png`, `.jpg`) using Gemini vision capabilities.
- **Weighted ATS Scoring Engine**: Evaluates content density across 6 key metrics:
  - Technical Skills Coverage (25 pts)
  - Work / Internship Experience (20 pts)
  - Education Verification (15 pts)
  - Technical Projects (15 pts)
  - Supplementary Sections (Summary, Certifications, Awards) (15 pts)
  - Word Count & Format Density (10 pts)
- **Job Description (JD) Keyword Matching**: Compares resume technical skills against target JD requirements to identify matched keywords and skill gaps.
- **AI Executive Insights**: Powered by Google Gemini (`gemini-3.6-flash`) via the `google-genai` SDK to deliver high-level summaries and actionable resume improvements.
- **SQLite Database Persistence**: Automatically logs scan histories, word counts, detected skills, and scores for quick retrieval.
- **Export Capabilities**: Download structured reports as `.json` or generate print-ready PDF summaries directly from the browser.

---

## 🏗️ Project Architecture

```text
AI-Resume-Analyzer/
├── 01-Python-Learning/        # Core scripting & fundamentals practice
├── 02-Web-Development/        # Flask web application & frontend assets
│   ├── static/
│   │   ├── style.css          # Modern UI styling & print stylesheet
│   │   └── script.js          # Client-side validation, charts & API handlers
│   ├── templates/
│   │   └── index.html         # Main dashboard interface
│   ├── .env                   # Environment secrets (GEMINI_API_KEY)
│   └── app.py                 # Flask server & analysis pipeline
├── 05-Database/               # Persistence layer
│   ├── database.py            # SQLite schema, connections & queries
│   └── resume_analyzer.db     # SQLite database file
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation