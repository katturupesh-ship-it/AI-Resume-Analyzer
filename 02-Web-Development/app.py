import os
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from pypdf import PdfReader
from PIL import Image
import io
from google import genai

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Google Gemini Client
api_key = os.environ.get("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# SQLite Database Helper Functions
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "05-Database", "resume_analyzer.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            ats_score INTEGER,
            word_count INTEGER,
            skills_detected TEXT,
            ai_summary TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_analysis(filename, ats_score, word_count, skills, ai_summary):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analyses (filename, ats_score, word_count, skills_detected, ai_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            filename,
            ats_score,
            word_count,
            json.dumps(skills),
            ai_summary,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Database insert error:", e)

def get_recent_history(limit=5):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT filename, ats_score, word_count, created_at FROM analyses ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{"filename": r[0], "ats_score": r[1], "word_count": r[2], "created_at": r[3]} for r in rows]
    except Exception as e:
        print("Database query error:", e)
        return []

# Technical Skills List
TECHNICAL_SKILLS = [
    "Python", "JavaScript", "TypeScript", "HTML", "CSS", "SQL", "PostgreSQL",
    "MySQL", "MongoDB", "SQLite", "React", "Node.js", "Express", "Flask",
    "Django", "FastAPI", "Git", "GitHub", "Docker", "Kubernetes", "AWS",
    "Azure", "GCP", "Linux", "REST API", "GraphQL", "Pandas", "NumPy",
    "Scikit-Learn", "TensorFlow", "PyTorch", "Tailwind", "Bootstrap",
    "Next.js", "Vue", "Angular", "Java", "C++", "C#", "Go", "Rust"
]

def extract_text_from_pdf(file_stream):
    try:
        reader = PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        print("PDF extraction error:", e)
        return ""

def extract_text_from_image(file_stream):
    if not client:
        return ""
    try:
        image = Image.open(file_stream)
        prompt = "Transcribe all visible text from this resume image accurately. Do not add commentary."
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image]
        )
        return response.text.strip() if response.text else ""
    except Exception as e:
        print("Image vision transcription error:", e)
        return ""

def compute_ats_metrics(text):
    text_lower = text.lower()
    words = text.split()
    word_count = len(words)

    # 1. Skills (25 pts)
    detected_skills = [skill for skill in TECHNICAL_SKILLS if skill.lower() in text_lower]
    skills_score = min(25, len(detected_skills) * 3)

    # 2. Experience (20 pts)
    exp_keywords = ["experience", "employment", "work history", "internship", "developer", "engineer"]
    exp_score = 20 if any(k in text_lower for k in exp_keywords) else 0

    # 3. Education (15 pts)
    edu_keywords = ["education", "university", "college", "degree", "bachelor", "master", "b.tech", "b.e", "b.s"]
    edu_score = 15 if any(k in text_lower for k in edu_keywords) else 0

    # 4. Projects (15 pts)
    proj_keywords = ["projects", "personal projects", "academic projects", "key initiatives"]
    proj_score = 15 if any(k in text_lower for k in proj_keywords) else 0

    # 5. Supplementary Sections (15 pts)
    extra_sections = {
        "Summary": any(k in text_lower for k in ["summary", "objective", "profile", "about me"]),
        "Certifications": any(k in text_lower for k in ["certifications", "certificates", "licenses"]),
        "Achievements": any(k in text_lower for k in ["achievements", "awards", "honors", "publications"])
    }
    extra_score = sum(5 for found in extra_sections.values() if found)

    # 6. Formatting / Word Count (10 pts)
    format_score = 10 if 200 <= word_count <= 1000 else (5 if 100 <= word_count < 200 else 2)

    total_score = skills_score + exp_score + edu_score + proj_score + extra_score + format_score

    sections_found = {
        "Skills": len(detected_skills) > 0,
        "Experience": exp_score > 0,
        "Education": edu_score > 0,
        "Projects": proj_score > 0,
        "Summary": extra_sections["Summary"],
        "Certifications": extra_sections["Certifications"],
        "Achievements": extra_sections["Achievements"]
    }

    strengths = []
    weaknesses = []

    if detected_skills:
        strengths.append(f"Solid skill variety ({len(detected_skills)} skills detected).")
    else:
        weaknesses.append("No technical keywords identified.")

    if 300 <= word_count <= 800:
        strengths.append(f"Optimal resume word count ({word_count} words).")
    elif word_count < 200:
        weaknesses.append(f"Resume is short ({word_count} words). Expand on your experience.")

    for sec, found in sections_found.items():
        if not found and sec in ["Experience", "Projects", "Summary"]:
            weaknesses.append(f"Missing {sec} section.")

    suggestions = []
    if not sections_found["Experience"]:
        suggestions.append("Add an 'Experience' or 'Internship' section to demonstrate practical delivery.")
    if not sections_found["Projects"]:
        suggestions.append("Include 2-3 technical projects showcasing real-world problem-solving.")
    if not sections_found["Summary"]:
        suggestions.append("Add a 2-3 line Professional Summary at the top of your resume.")
    if len(detected_skills) < 5:
        suggestions.append("Add more specific tools, frameworks, and programming languages.")

    return {
        "total_score": total_score,
        "breakdown": {
            "skills": skills_score,
            "experience": exp_score,
            "education": edu_score,
            "projects": proj_score,
            "supplementary": extra_score,
            "formatting": format_score
        },
        "word_count": word_count,
        "skills": detected_skills,
        "sections": sections_found,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions
    }

def analyze_with_gemini(text, detected_skills):
    if not client or not text:
        return {"summary": "Gemini API key not configured or text empty.", "recommendations": []}
    
    prompt = f"""
    You are an expert ATS and technical recruiter. Analyze this resume text and provide a succinct executive review.

    Resume Text:
    {text[:3500]}

    Detected Skills: {', '.join(detected_skills) if detected_skills else 'None'}

    Provide your response as a valid JSON object matching this structure:
    {{
        "summary": "A 2-3 sentence executive profile evaluation highlighting candidate strengths and domain fit.",
        "recommendations": [
            "Specific phrasing and framing recommendation.",
            "Technical skill depth or missing industry keyword.",
            "Formatting or structural optimization."
        ]
    }}
    Return ONLY valid JSON.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        print("Gemini API error:", e)
        return {
            "summary": "AI summary generation currently unavailable.",
            "recommendations": ["Ensure clear section headers.", "Quantify project metrics.", "Add relevant industry keywords."]
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/history")
def history():
    return jsonify({"success": True, "history": get_recent_history()})

@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400

    file = request.files["resume"]
    filename = file.filename or "resume"
    job_desc = request.form.get("job_description", "").strip()

    file_bytes = file.read()
    file_stream = io.BytesIO(file_bytes)

    extracted_text = ""
    if filename.lower().endswith(".pdf"):
        extracted_text = extract_text_from_pdf(file_stream)
        if not extracted_text:
            file_stream.seek(0)
            extracted_text = extract_text_from_image(file_stream)
    elif filename.lower().endswith((".png", ".jpg", ".jpeg")):
        extracted_text = extract_text_from_image(file_stream)

    if not extracted_text:
        return jsonify({"success": False, "message": "Could not extract readable text from document."}), 400

    # ATS Scoring
    ats = compute_ats_metrics(extracted_text)

    # Gemini Analysis
    ai_insights = analyze_with_gemini(extracted_text, ats["skills"])

    # Job Description Matching
    jd_match = {"has_jd": False}
    if job_desc:
        jd_lower = job_desc.lower()
        target_skills = [s for s in TECHNICAL_SKILLS if s.lower() in jd_lower]
        if target_skills:
            matched = [s for s in target_skills if s in ats["skills"]]
            missing = [s for s in target_skills if s not in ats["skills"]]
            match_pct = round((len(matched) / len(target_skills)) * 100)
            jd_match = {
                "has_jd": True,
                "match_percentage": match_pct,
                "matched_skills": matched,
                "missing_skills": missing,
                "message": f"Matched {len(matched)} of {len(target_skills)} required technical skills."
            }

    # Save to SQLite
    save_analysis(filename, ats["total_score"], ats["word_count"], ats["skills"], ai_insights.get("summary", ""))

    return jsonify({
        "success": True,
        "text": extracted_text,
        "ats": ats,
        "skills": ats["skills"],
        "sections": ats["sections"],
        "strengths": ats["strengths"],
        "weaknesses": ats["weaknesses"],
        "suggestions": ats["suggestions"],
        "ai_insights": ai_insights,
        "jd_match": jd_match
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)