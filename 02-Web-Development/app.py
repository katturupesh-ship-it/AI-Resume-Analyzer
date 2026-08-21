import os
import sys
import re
import time
from flask import Flask, render_template, request, jsonify
from pypdf import PdfReader
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Explicit path to .env file in 02-Web-Development
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Allow importing database module from parent 05-Database folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "05-Database")))
import database  # type: ignore

app = Flask(__name__)

# Initialize database
database.init_db()

# Initialize GenAI Client
api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
print(f"\n--- [DEBUG] Loaded API Key: {api_key[:8]}... (Length: {len(api_key)}) ---")

ai_client = None
if api_key and api_key != "YOUR_ACTUAL_GEMINI_API_KEY_HERE":
    try:
        ai_client = genai.Client(api_key=api_key)
        print("--- [DEBUG] Gemini AI Client Initialized Successfully ---\n")
    except Exception as e:
        print(f"--- [DEBUG] Failed to initialize Gemini Client: {e} ---\n")
else:
    print("--- [DEBUG] Warning: GEMINI_API_KEY is not set or still default ---\n")

PREDEFINED_SKILLS = [
    "Python", "Java", "C", "C++", "C#", "SQL", "MySQL", "PostgreSQL", "MongoDB",
    "HTML", "CSS", "JavaScript", "TypeScript", "React", "Angular", "Vue",
    "Node.js", "Express", "Flask", "Django", "FastAPI", "Spring Boot",
    "Machine Learning", "Deep Learning", "Data Science", "Artificial Intelligence",
    "NLP", "Computer Vision", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-Learn",
    "Git", "GitHub", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux"
]

SECTION_PATTERNS = {
    "Summary": [r"summary", r"professional summary", r"about me", r"objective", r"profile"],
    "Education": [r"education", r"academic background", r"academics", r"qualifications"],
    "Experience": [r"experience", r"work experience", r"employment history", r"internships", r"work history"],
    "Projects": [r"projects", r"academic projects", r"key projects", r"personal projects"],
    "Skills": [r"skills", r"technical skills", r"technologies", r"core competencies", r"competencies"],
    "Certifications": [r"certifications", r"certificates", r"courses", r"training"],
    "Achievements": [r"achievements", r"honors", r"awards", r"accomplishments"]
}


def clean_resume_text(raw_text):
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_skills(text):
    found_skills = []
    for skill in PREDEFINED_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            found_skills.append(skill)
    return sorted(found_skills)


def extract_sections(text):
    detected = {}
    lines = text.split("\n")

    for section, patterns in SECTION_PATTERNS.items():
        detected[section] = False
        for line in lines:
            cleaned = re.sub(r"[:\-_|]", "", line.strip().lower()).strip()
            for pattern in patterns:
                if re.fullmatch(pattern, cleaned, re.IGNORECASE):
                    detected[section] = True
                    break
            if detected[section]:
                break
    return detected


def match_job_description(resume_skills, jd_text):
    if not jd_text.strip():
        return None

    jd_skills = extract_skills(jd_text)
    if not jd_skills:
        return {
            "has_jd": True,
            "jd_skills": [],
            "matched_skills": [],
            "missing_skills": [],
            "match_percentage": 0,
            "message": "No recognized technical skills found in Job Description."
        }

    resume_set, jd_set = set(resume_skills), set(jd_skills)
    matched = sorted(list(resume_set.intersection(jd_set)))
    missing = sorted(list(jd_set.difference(resume_set)))
    match_percentage = round((len(matched) / len(jd_set)) * 100)

    return {
        "has_jd": True,
        "jd_skills": jd_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": match_percentage,
        "message": f"Matched {len(matched)} of {len(jd_skills)} required skills."
    }


def generate_insights_and_suggestions(sections, skills, word_count, jd_match=None):
    strengths = []
    weaknesses = []
    suggestions = []

    if sections.get("Experience"):
        strengths.append("Work Experience section is included.")
    else:
        weaknesses.append("Missing Work Experience section.")
        suggestions.append("Add an 'Experience' or 'Internship' section to demonstrate practical delivery.")

    if sections.get("Projects"):
        strengths.append("Projects section is present.")
    else:
        weaknesses.append("Missing Projects section.")
        suggestions.append("Include 2-3 technical projects showcasing real-world problem-solving.")

    if sections.get("Summary"):
        strengths.append("Professional Summary included.")
    else:
        weaknesses.append("Missing Summary / Objective.")
        suggestions.append("Add a 2-3 line Professional Summary at the top of your resume.")

    num_skills = len(skills)
    if num_skills >= 5:
        strengths.append(f"Solid skill variety ({num_skills} skills detected).")
    else:
        weaknesses.append(f"Only {num_skills} technical skills identified.")
        suggestions.append("Expand your skills section with relevant frameworks, tools, and databases.")

    if 250 <= word_count <= 800:
        strengths.append(f"Optimal resume word count ({word_count} words).")
    elif word_count < 200:
        weaknesses.append(f"Resume is concise ({word_count} words).")
        suggestions.append("Add detailed bullet points explaining your impact and tools used in each project.")

    if jd_match and jd_match.get("has_jd"):
        if jd_match["missing_skills"]:
            suggestions.append(f"Incorporate missing target skills: {', '.join(jd_match['missing_skills'][:4])}.")

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions
    }


def calculate_ats_score(sections, skills, text):
    breakdown = {
        "skills": 0,
        "experience": 0,
        "education": 0,
        "projects": 0,
        "supplementary": 0,
        "formatting": 0
    }

    num_skills = len(skills)
    if num_skills >= 6:
        breakdown["skills"] = 25
    elif num_skills >= 4:
        breakdown["skills"] = 18
    elif num_skills >= 2:
        breakdown["skills"] = 10
    elif num_skills == 1:
        breakdown["skills"] = 5

    if sections.get("Experience"): breakdown["experience"] = 20
    if sections.get("Education"): breakdown["education"] = 15
    if sections.get("Projects"): breakdown["projects"] = 15

    for s in ["Summary", "Certifications", "Achievements"]:
        if sections.get(s): breakdown["supplementary"] += 5

    word_count = len(text.split())
    if 150 <= word_count <= 1000:
        breakdown["formatting"] = 10
    elif word_count > 50:
        breakdown["formatting"] = 5

    return {
        "total_score": min(sum(breakdown.values()), 100),
        "breakdown": breakdown,
        "word_count": word_count
    }


def call_gemini_with_retry(contents, retries=3, delay=2):
    """Executes a Gemini API request with retry logic for 503/429 spikes."""
    if not ai_client:
        return None
    for attempt in range(retries):
        try:
            response = ai_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            if "503" in err_str or "429" in err_str or "UNAVAILABLE" in err_str:
                if attempt < retries - 1:
                    time.sleep(delay * (attempt + 1))
                    continue
            raise e
    return None


def generate_ai_analysis(resume_text, jd_text=""):
    if not ai_client:
        return {
            "available": False,
            "summary": "Gemini API Key not configured or invalid in .env file.",
            "recommendations": []
        }

    prompt = f"""
    You are an expert Technical Recruiter and ATS Specialist.
    Analyze the following resume content:
    ---
    {resume_text[:4000]}
    ---
    Target Job Description (if provided):
    ---
    {jd_text[:1500] if jd_text else "None provided"}
    ---

    Provide your evaluation in this strict format:
    [SUMMARY]
    A 2-3 sentence executive professional summary evaluating the candidate's career level and core background.

    [TIPS]
    - Bullet point 1: Actionable advice on resume phrasing or metrics.
    - Bullet point 2: Advice on technical depth or project impact.
    - Bullet point 3: Strategy to better align with industry or target job description.
    """

    try:
        raw_output = call_gemini_with_retry(prompt)
        if not raw_output:
            return {
                "available": False,
                "summary": "AI generation is temporarily busy on Google's servers. ATS metrics are still fully calculated below.",
                "recommendations": []
            }

        summary = ""
        tips = []

        if "[SUMMARY]" in raw_output and "[TIPS]" in raw_output:
            parts = raw_output.split("[TIPS]")
            summary = parts[0].replace("[SUMMARY]", "").strip()
            tips_text = parts[1].strip()
            tips = [re.sub(r"^[-*•]\s*", "", line).strip() for line in tips_text.split("\n") if line.strip()]
        else:
            summary = raw_output.strip()

        return {
            "available": True,
            "summary": summary,
            "recommendations": tips
        }
    except Exception as e:
        print(f"\n--- [DEBUG] Gemini API Call Error: {e} ---\n")
        return {
            "available": False,
            "summary": "AI generation is temporarily busy on Google's servers. ATS metrics are still fully calculated below.",
            "recommendations": []
        }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/history", methods=["GET"])
def history():
    recent_records = database.get_recent_analyses(limit=5)
    return jsonify({
        "success": True,
        "history": recent_records
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"success": False, "message": "No resume uploaded."})

    resume = request.files["resume"]
    job_desc = request.form.get("job_description", "")
    filename = resume.filename.lower()

    if not (filename.endswith(".pdf") or filename.endswith((".png", ".jpg", ".jpeg"))):
        return jsonify({"success": False, "message": "Please upload a valid PDF or Image file (.pdf, .png, .jpg, .jpeg)."})

    raw_text = ""

    try:
        # Case 1: Standard PDF extraction
        if filename.endswith(".pdf"):
            reader = PdfReader(resume)
            raw_text = "".join([p.extract_text() or "" for p in reader.pages])

            # Fallback for Scanned/Image-only PDFs: Use Gemini Vision with Retry
            if not raw_text.strip() and ai_client:
                resume.seek(0)
                file_bytes = resume.read()
                raw_text = call_gemini_with_retry([
                    types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
                    "Extract and transcribe all text from this resume document accurately as plain text."
                ]) or ""

        # Case 2: Direct Image extraction (PNG / JPG / JPEG)
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            if not ai_client:
                return jsonify({"success": False, "message": "Gemini API client is required to process image resumes."})

            file_bytes = resume.read()
            mime_type = "image/png" if filename.endswith(".png") else "image/jpeg"

            raw_text = call_gemini_with_retry([
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                "Extract and transcribe all text from this resume image accurately as plain text."
            ]) or ""

        if not raw_text.strip():
            return jsonify({
                "success": False,
                "message": "Could not extract text from this file. The AI transcription service is temporarily congested; please try again in a few seconds."
            })

        cleaned_text = clean_resume_text(raw_text)
        detected_skills = extract_skills(cleaned_text)
        detected_sections = extract_sections(cleaned_text)
        jd_match_result = match_job_description(detected_skills, job_desc)
        ats_result = calculate_ats_score(detected_sections, detected_skills, cleaned_text)
        insights = generate_insights_and_suggestions(detected_sections, detected_skills, ats_result["word_count"], jd_match_result)
        ai_insights = generate_ai_analysis(cleaned_text, job_desc)

        # Save to SQLite Database
        database.save_analysis(
            filename=resume.filename,
            ats_score=ats_result["total_score"],
            word_count=ats_result["word_count"],
            skills_list=detected_skills,
            ai_summary=ai_insights.get("summary", "")
        )

        return jsonify({
            "success": True,
            "message": "Resume analyzed successfully!",
            "skills": detected_skills,
            "sections": detected_sections,
            "ats": ats_result,
            "jd_match": jd_match_result,
            "strengths": insights["strengths"],
            "weaknesses": insights["weaknesses"],
            "suggestions": insights["suggestions"],
            "ai_insights": ai_insights,
            "text": cleaned_text
        })

    except Exception as error:
        print("Analysis Error:", error)
        return jsonify({"success": False, "message": f"Error processing file: {str(error)}"})


if __name__ == "__main__":
    app.run(debug=True)