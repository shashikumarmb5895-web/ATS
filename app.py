from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import os
import uuid
import csv
import io
import re
import random
from datetime import datetime
from nlp_engine import extract_text_from_bytes, clean_text, extract_skills, calculate_similarity, analyze_skill_gap
from hr_module.api import hr_bp

app = Flask(__name__)
app.secret_key = 'career_quest_secret_key_2024' # Change this in production
CORS(app)

# Register HR Interview Blueprint
app.register_blueprint(hr_bp)

# No disk folder needed — files are processed in-memory for Vercel serverless compatibility

# Mock Job Database
jobs = [
    {"id": 1, "title": "Software Engineer (Full Stack)", "company": "TechVision AI", "description": "Looking for a full-stack developer with Python, React, and Flask experience. Join our team building innovative AI-driven apps.", "skills": ["python", "react", "flask", "sql", "aws"]},
    {"id": 2, "title": "Data Scientist", "company": "DataStream Solutions", "description": "Seeking a Data Scientist proficient in Python, Machine Learning, and NLP. Experience with TensorFlow or PyTorch is required.", "skills": ["python", "machine learning", "nlp", "tensorflow", "pytorch"]},
    {"id": 3, "title": "Frontend Developer", "company": "PixelPerfect UI", "description": "Looking for a Frontend Developer with strong skills in JavaScript, HTML, CSS, and React. Experience with Flutter is a bonus.", "skills": ["javascript", "html", "css", "react", "flutter"]},
    {"id": 4, "title": "DevOps Engineer", "company": "CloudShield", "description": "Experienced DevOps Engineer with Docker, Kubernetes, and AWS experience. Knowledge of Git and Python scripting is essential.", "skills": ["docker", "kubernetes", "aws", "git", "python"]},
    {"id": 5, "title": "Cybersecurity Analyst", "company": "SecureNet", "description": "Monitor network for security breaches and investigate violations. Expertise in firewalls and penetration testing required.", "skills": ["security", "network", "firewalls", "penetration testing", "linux"]},
    {"id": 6, "title": "Product Manager", "company": "LaunchPad", "description": "Lead the product lifecycle from concept to launch. Strong agile and user research skills are must-haves.", "skills": ["product management", "agile", "user research", "roadmap", "analytics"]},
    {"id": 7, "title": "UX Designer", "company": "Creative Minds", "description": "Create intuitive and beautiful user experiences. Proficiency in Figma and user research methodologies.", "skills": ["figma", "sketch", "user research", "prototyping", "ui/ux"]},
    {"id": 8, "title": "Backend Developer (Go)", "company": "ScaleX", "description": "Build high-performance microservices using Go and Redis. Experience with gRPC and Docker is highly preferred.", "skills": ["go", "microservices", "redis", "docker", "grpc"]},
    {"id": 9, "title": "Machine Learning Engineer", "company": "AI Vision", "description": "Develop and deploy computer vision models using OpenCV and PyTorch. Deep learning expertise is essential.", "skills": ["python", "opencv", "pytorch", "deep learning", "cuda"]},
    {"id": 10, "title": "Marketing Manager", "company": "GrowthLoop", "description": "Drive user acquisition through digital marketing channels like SEO, SEM, and social media.", "skills": ["seo", "sem", "content marketing", "google analytics", "social media"]},
    {"id": 11, "title": "Cloud Architect", "company": "SkyHigh Cloud", "description": "Design scalable cloud infrastructure solutions using AWS, Azure, and Terraform.", "skills": ["aws", "azure", "terraform", "ansible", "architecture"]},
    {"id": 12, "title": "Mobile Developer (iOS)", "company": "AppFlow", "description": "Build premium iOS applications using Swift and SwiftUI. Focus on premium mobile design.", "skills": ["swift", "swiftui", "ios", "xcode", "mobile design"]},
    {"id": 13, "title": "Full Stack Developer (Node)", "company": "QuickStream", "description": "Develop modern web applications using Node.js, Express, and MongoDB.", "skills": ["node.js", "express", "mongodb", "react", "aws"]},
    {"id": 14, "title": "SRE Engineer", "company": "SteadyState", "description": "Ensure reliability and performance of critical systems using Prometheus, Grafana, and Terraform.", "skills": ["prometheus", "grafana", "linux", "python", "terraform"]},
    {"id": 15, "title": "AI Content Specialist", "company": "PromptMaster", "description": "Optimize AI outputs and prompt engineering workflows for LLM-based applications.", "skills": ["prompt engineering", "nlp", "llm", "content strategy", "python"]},
    {"id": 16, "title": "Data Engineer", "company": "StreamFlow", "description": "Build robust data pipelines using Spark, Kafka, and Hadoop for real-time analytics.", "skills": ["spark", "kafka", "hadoop", "sql", "python"]}
]

# Mock Databases
candidates = {} # Map candidate_id -> profile
applications = [] 
interviews = [] # Track scheduled interviews

# Mock Career Graph for Trajectory Prediction
CAREER_GRAPH = {
    "python": ["Backend Developer", "Data Engineer", "Machine Learning Engineer", "AI Solutions Architect", "Head of AI"],
    "javascript": ["Full Stack Developer", "Frontend Lead", "Solutions Architect", "Product Owner", "Tech Consultant"],
    "react": ["Frontend Architect", "UI/UX Lead", "Product Designer", "Product Manager", "Director of Engineering"],
    "data scientist": ["Senior Data Scientist", "MLOps Engineer", "AI Researcher", "Lead Data Scientist", "CDO"],
    "devops": ["Site Reliability Engineer", "Cloud Architect", "Infrastructure Lead", "Platform Engineer", "VP of Operations"],
    "java": ["Enterprise Architect", "System Design Lead", "Technical Manager", "VP of Technology", "CTO"]
}

# Mock Course Catalog
COURSE_CATALOG = {
    "python": {"title": "Python for Data Science and AI", "platform": "Coursera", "url": "https://coursera.org"},
    "react": {"title": "Modern React with Redux", "platform": "Udemy", "url": "https://udemy.com"},
    "docker": {"title": "Docker & Kubernetes: The Practical Guide", "platform": "Udemy", "url": "https://udemy.com"},
    "aws": {"title": "AWS Certified Solutions Architect", "platform": "A Cloud Guru", "url": "https://acloudguru.com"},
    "machine learning": {"title": "Machine Learning Specialization", "platform": "Coursera", "url": "https://coursera.org"},
    "sql": {"title": "The Complete SQL Bootcamp", "platform": "Udemy", "url": "https://udemy.com"},
    "kubernetes": {"title": "Kubernetes for Developers", "platform": "edX", "url": "https://edx.org"},
    "nlp": {"title": "Natural Language Processing", "platform": "Coursera", "url": "https://coursera.org"},
    "javascript": {"title": "JavaScript: The Good Parts", "platform": "Frontend Masters", "url": "https://frontendmasters.com"},
    "flask": {"title": "REST APIs with Flask and Python", "platform": "Udemy", "url": "https://udemy.com"}
}

# Mock Company Cultures (Glassdoor Analysis Simulation)
COMPANY_CULTURES = {
    "TechVision AI": {"tags": ["python", "innovation", "ai"], "sentiment": 4.8, "trait": "Innovative"},
    "DataStream Solutions": {"tags": ["analytical", "collaborative", "data"], "sentiment": 4.2, "trait": "Analytical"},
    "PixelPerfect UI": {"tags": ["creative", "design-led", "react"], "sentiment": 4.5, "trait": "Creative"},
    "CloudShield": {"tags": ["security", "stability", "aws"], "sentiment": 4.0, "trait": "Secure"},
    "SecureNet": {"tags": ["security", "vigilant", "detailed"], "sentiment": 4.1, "trait": "Security-Focused"},
    "LaunchPad": {"tags": ["agile", "fast-paced", "growth"], "sentiment": 4.6, "trait": "High-Energy"},
    "Creative Minds": {"tags": ["design", "collaborative", "artistic"], "sentiment": 4.7, "trait": "Collaborative"},
    "ScaleX": {"tags": ["engineering", "performance", "scalable"], "sentiment": 4.3, "trait": "Growth-Minded"},
    "AI Vision": {"tags": ["research", "innovation", "math"], "sentiment": 4.9, "trait": "Research-Oriented"},
    "GrowthLoop": {"tags": ["marketing", "data-driven", "creative"], "sentiment": 4.2, "trait": "Results-Driven"},
    "SkyHigh Cloud": {"tags": ["cloud", "architecture", "reliable"], "sentiment": 4.4, "trait": "Reliable"},
    "AppFlow": {"tags": ["mobile", "design", "user-focused"], "sentiment": 4.6, "trait": "User-Centric"},
    "QuickStream": {"tags": ["full-stack", "fast", "efficient"], "sentiment": 4.1, "trait": "Efficient"},
    "SteadyState": {"tags": ["reliability", "detailed", "on-call"], "sentiment": 3.9, "trait": "Stable"},
    "PromptMaster": {"tags": ["creative", "nlp", "experimental"], "sentiment": 4.8, "trait": "Experimental"},
    "StreamFlow": {"tags": ["data", "real-time", "scalable"], "sentiment": 4.3, "trait": "Real-Time"}
}

# Indian Market Salary Benchmarks (Lakhs Per Annum - LPA)
SALARY_BASE = {
    "Software Engineer (Full Stack)": 1800000,
    "Data Scientist": 2200000,
    "Frontend Developer": 1400000,
    "DevOps Engineer": 2000000,
    "Cybersecurity Analyst": 1600000,
    "Product Manager": 2500000,
    "UX Designer": 1200000,
    "Backend Developer (Go)": 2000000,
    "Machine Learning Engineer": 2800000,
    "Marketing Manager": 1000000,
    "Cloud Architect": 3500000,
    "Mobile Developer (iOS)": 1800000,
    "Full Stack Developer (Node)": 1600000,
    "SRE Engineer": 2400000,
    "AI Content Specialist": 1200000,
    "Data Engineer": 2200000
}

SKILL_PREMIUMS = {
    "python": 100000, "aws": 200000, "kubernetes": 300000, "react": 80000, 
    "security": 150000, "prompt engineering": 400000, "go": 120000,
    "terraform": 150000, "pytorch": 250000, "docker": 100000
}

def predict_salary(title, candidate_skills):
    base = SALARY_BASE.get(title, 1200000)
    bonus = sum([SKILL_PREMIUMS.get(s.lower(), 50000) for s in candidate_skills])
    low = (base + bonus) * 0.95
    high = (base + bonus) * 1.05
    return {
        "range": f"₹{low/100000:.1f}L - ₹{high/100000:.1f}L",
        "trend": "up" if any(s in ["prompt engineering", "aws", "kubernetes"] for s in candidate_skills) else "stable"
    }

def calculate_culture_fit(candidate_skills, company_name):
    culture = COMPANY_CULTURES.get(company_name, {"tags": ["professional", "growth"], "sentiment": 4.0, "trait": "Professional"})
    # Match skills to culture tags
    matches = [s for s in candidate_skills if s in culture['tags']]
    # Simulate a score based on matches + base sentiment
    score = (culture['sentiment'] / 5.0) * 80 + (len(matches) * 5)
    return round(min(score, 98), 2), culture['trait'], culture['sentiment']

# ─── Resume Doctor Engine ──────────────────────────────────────────────────────

WEAK_VERBS = ["worked", "helped", "did", "made", "was responsible for", "handled", "involved in", "assisted"]
STRONG_VERBS = ["achieved", "accelerated", "built", "designed", "engineered", "launched", "led", "optimized", "reduced", "scaled", "delivered", "automated", "increased", "improved", "developed"]
REQUIRED_SECTIONS = ["experience", "education", "skills", "summary", "objective", "work experience"]
FILLER_PHRASES = ["team player", "hard worker", "go-getter", "motivated individual", "results-oriented", "detail-oriented", "self-starter", "passionate about"]
POWER_QUANTIFIERS = ["%", "million", "billion", "k users", "$", "revenue", "roi", "cost", "reduced by", "increased by", "x faster", "projects", "clients"]

def diagnose_resume(text, skills):
    text_lower = text.lower()
    word_count = len(text.split())
    sentences = [s.strip() for s in text.replace('\n', '. ').split('.') if len(s.strip()) > 10]
    
    critical, warnings, suggestions, strengths = [], [], [], []
    ats_score = 100  # start at 100, deduct for issues

    # ── CRITICAL CHECKS ────────────────────────────

    # Missing contact info signals
    has_email = bool(re.search(r'\S+@\S+\.\S+', text))
    has_phone = bool(re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{10,13})', text))
    if not has_email:
        critical.append({"id": "no_email", "title": "Missing Email Address", "detail": "Recruiters cannot contact you without an email. Add it in the header.", "fix": "Add: yourname@email.com in the contact section."})
        ats_score -= 15
    if not has_phone:
        critical.append({"id": "no_phone", "title": "Missing Phone Number", "detail": "Many companies require a phone number for screening calls.", "fix": "Add your phone number in international format: +91-XXXXXXXXXX"})
        ats_score -= 10

    # Length issues
    if word_count < 200:
        critical.append({"id": "too_short", "title": f"Resume Too Short ({word_count} words)", "detail": "A resume under 200 words signals a lack of experience or effort.", "fix": "Expand each role with responsibilities and 2-3 key accomplishments. Aim for 400–700 words."})
        ats_score -= 20
    elif word_count > 1000:
        warnings.append({"id": "too_long", "title": f"Resume Too Long ({word_count} words)", "detail": "Ideal resumes are 1 page (400–700 words). Long resumes lose recruiter attention.", "fix": "Cut duplicate entries, old roles (>10yr), and remove filler phrases."})
        ats_score -= 8

    # Missing section keywords
    missing_sections = [s for s in REQUIRED_SECTIONS if s not in text_lower]
    if len(missing_sections) >= 3:
        critical.append({"id": "missing_sections", "title": "Key Sections Missing", "detail": f"Could not detect: {', '.join(missing_sections[:3])}. ATS systems look for these headers.", "fix": "Add clearly labeled sections: Summary, Skills, Work Experience, Education."})
        ats_score -= 15

    # No quantified achievements
    has_numbers = any(q in text_lower for q in POWER_QUANTIFIERS)
    if not has_numbers:
        critical.append({"id": "no_metrics", "title": "Zero Quantified Achievements", "detail": "No metrics, percentages, or numbers found. Resumes without impact data rank poorly.", "fix": "Add numbers: 'Led team of 5', 'Reduced load time by 40%', 'Grew revenue by ₹2Cr'."})
        ats_score -= 12

    # ── WARNING CHECKS ─────────────────────────────

    # Weak verbs
    found_weak = [v for v in WEAK_VERBS if v in text_lower]
    if len(found_weak) >= 2:
        warnings.append({"id": "weak_verbs", "title": f"Weak Action Verbs Detected ({len(found_weak)} found)", "detail": f"Found: {', '.join(found_weak[:4])}. Weak verbs dilute your impact.", "fix": f"Replace with power verbs: {', '.join(STRONG_VERBS[:5])}, etc."})
        ats_score -= 8
    
    # Filler phrases
    found_fillers = [f for f in FILLER_PHRASES if f in text_lower]
    if found_fillers:
        warnings.append({"id": "filler_phrases", "title": f"Cliché Phrases Detected ({len(found_fillers)})", "detail": f"Phrases like '{found_fillers[0]}' add no value and are ignored by ATS.", "fix": "Delete all filler phrases. Replace with specific examples and real outcomes."})
        ats_score -= 5

    # No skills listed
    if len(skills) < 5:
        warnings.append({"id": "few_skills", "title": f"Only {len(skills)} Skills Detected", "detail": "ATS systems match skills in job descriptions. A thin skills list means low match scores.", "fix": "Add a dedicated 'Technical Skills' section with 10–15 relevant skills."})
        ats_score -= 10

    # Missing LinkedIn / GitHub
    has_links = bool(re.search(r'(linkedin|github|portfolio|behance)', text_lower))
    if not has_links:
        warnings.append({"id": "no_links", "title": "No Online Profile Links", "detail": "LinkedIn and GitHub are checked by 87% of tech recruiters.", "fix": "Add: linkedin.com/in/yourname | github.com/yourname to your header."})
        ats_score -= 6

    # Passive voice detection
    passive_count = len(re.findall(r'\b(was|were|been|is|are)\s+\w+ed\b', text_lower))
    if passive_count > 3:
        warnings.append({"id": "passive_voice", "title": f"Passive Voice Overuse ({passive_count} instances)", "detail": "Passive voice weakens your narrative. Active voice demonstrates ownership.", "fix": "Change: 'Was responsible for testing' → 'Led QA testing for 3 products'"})
        ats_score -= 5

    # ── SUGGESTION CHECKS ──────────────────────────

    # No summary section
    has_summary = any(kw in text_lower for kw in ["summary", "objective", "about me", "profile"])
    if not has_summary:
        suggestions.append({"id": "no_summary", "title": "Missing Professional Summary", "detail": "A 3-line summary at the top helps recruiters instantly categorize your profile.", "fix": "Add a 3-sentence summary: Role | Key Skills | Career Goal."})

    # Dates format check
    has_dates = bool(re.search(r'(20\d\d|19\d\d)', text))
    if not has_dates:
        suggestions.append({"id": "no_dates", "title": "No Employment Dates Visible", "detail": "ATS systems use dates to calculate experience levels. Missing dates = unknown seniority.", "fix": "Add year ranges: 'Software Engineer at ABC Corp (2021 – 2024)'"})

    # Repetitive words
    words = re.findall(r'\b[a-z]{4,}\b', text_lower)
    from collections import Counter
    freq = Counter(words)
    repeated = [(w, c) for w, c in freq.most_common(10) if c > 5 and w not in ["with", "that", "this", "from", "have", "your", "will", "been", "they", "their", "team", "work", "using", "which", "were", "able", "more", "also", "into", "over", "some", "such"]]
    if repeated:
        suggestions.append({"id": "repetition", "title": f"Repetitive Word: '{repeated[0][0]}' ({repeated[0][1]}x)", "detail": "Repeating the same word too often signals lack of vocabulary.", "fix": f"Use synonyms or restructure sentences to vary your language."})

    # No certifications
    has_certs = bool(re.search(r'(certif|aws |gcp |azure|google cloud|pmp|scrum|cpa|cfa)', text_lower))
    if not has_certs:
        suggestions.append({"id": "no_certs", "title": "No Certifications Listed", "detail": "Certifications increase shortlisting rates by 30% for technical roles.", "fix": "Add relevant certs: AWS, GCP, PMP, Scrum, or Coursera certificates."})

    # ── STRENGTH RECOGNITION ───────────────────────

    strong_verbs_found = [v for v in STRONG_VERBS if v in text_lower]
    if len(strong_verbs_found) >= 3:
        strengths.append({"title": "Strong Action Verbs", "detail": f"Great use of: {', '.join(strong_verbs_found[:5])}. This makes your contributions stand out!"})

    if has_numbers:
        strengths.append({"title": "Quantified Achievements", "detail": "You've included metrics and numbers. This is a top signal for recruiters!"})

    if len(skills) >= 8:
        strengths.append({"title": "Rich Skill Set", "detail": f"Detected {len(skills)} skills. A diverse technical profile improves ATS match rates."})

    if has_email and has_phone:
        strengths.append({"title": "Complete Contact Info", "detail": "Email and phone number are present. Recruiters can reach you without friction."})

    if has_links:
        strengths.append({"title": "Online Presence", "detail": "LinkedIn/GitHub detected. This builds credibility instantly with tech recruiters."})

    # ── READABILITY SCORE ──────────────────────────
    avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    readability = "Excellent" if avg_sentence_len < 15 else ("Good" if avg_sentence_len < 22 else "Needs Improvement")

    # Cap ATS score between 20 and 98
    ats_score = max(20, min(98, ats_score))

    return {
        "ats_score": ats_score,
        "word_count": word_count,
        "readability": readability,
        "critical": critical,
        "warnings": warnings,
        "suggestions": suggestions,
        "strengths": strengths,
        "total_issues": len(critical) + len(warnings),
        "skills_count": len(skills)
    }

@app.route('/api/resume/diagnose', methods=['GET'])
def diagnose_resume_endpoint():
    candidate_id = request.args.get('candidate_id')
    resume_id = request.args.get('resume_id')
    
    if not candidate_id or candidate_id not in candidates:
        return jsonify({"error": "Candidate not found"}), 404
    
    cand = candidates[candidate_id]
    if not cand.get('resumes'):
        return jsonify({"error": "No resume uploaded yet"}), 400

    # Use specific resume_id or latest
    resume = next((r for r in cand['resumes'] if r['id'] == resume_id), cand['resumes'][-1])
    result = diagnose_resume(resume['text'], resume['skills'])
    return jsonify(result)

# ──────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('portal_hub.html')

@app.route('/candidate')
def candidate_portal():
    return render_template('index.html', default_view='candidate')

@app.route('/recruiter')
def recruiter_portal():
    return render_template('index.html', default_view='recruiter')

@app.route('/hr-interviews')
def hr_interviews_page():
    if not session.get('hr_logged_in'):
        return redirect(url_for('hr_login_page'))
    return render_template('hr/dashboard.html')

@app.route('/hr-login', methods=['GET', 'POST'])
def hr_login_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Hardcoded credentials as requested for the separate page
        if email == 'hr@careerquest.ai' and password == 'password123':
            session['hr_logged_in'] = True
            return redirect(url_for('hr_interviews_page'))
        else:
            return render_template('hr/login.html', error="Invalid email or password")
            
    return render_template('hr/login.html')

@app.route('/hr-logout')
def hr_logout():
    session.pop('hr_logged_in', None)
    return redirect(url_for('hr_login_page'))

@app.route('/api/jobs', methods=['GET', 'POST'])
def handle_jobs():
    if request.method == 'POST':
        data = request.json
        new_job = {
            "id": len(jobs) + 1,
            "title": data.get('title'),
            "company": data.get('company'),
            "description": data.get('description'),
            "skills": [s.strip().lower() for s in data.get('skills', '').split(',')]
        }
        jobs.append(new_job)
        return jsonify(new_job), 201
    return jsonify(jobs)

# Realistic Talent Pool Seeding
TALENT_POOL = [
    # India Tech Hubs
    {"lat": 12.9716, "lng": 77.5946, "skill": "python", "count": 1450, "city": "Bengaluru"},
    {"lat": 18.5204, "lng": 73.8567, "skill": "python", "count": 890, "city": "Pune"},
    {"lat": 17.3850, "lng": 78.4867, "skill": "java", "count": 1200, "city": "Hyderabad"},
    {"lat": 12.9716, "lng": 77.5946, "skill": "react", "count": 950, "city": "Bengaluru"},
    {"lat": 28.6139, "lng": 77.2090, "skill": "aws", "count": 670, "city": "Delhi"},
    # North America
    {"lat": 37.7749, "lng": -122.4194, "skill": "python", "count": 2100, "city": "San Francisco"},
    {"lat": 40.7128, "lng": -74.0060, "skill": "rust", "count": 450, "city": "New York"},
    {"lat": 47.6062, "lng": -122.3321, "skill": "kubernetes", "count": 1100, "city": "Seattle"},
    {"lat": 34.0522, "lng": -118.2437, "skill": "react", "count": 1500, "city": "Los Angeles"},
    # Europe
    {"lat": 52.5200, "lng": 13.4050, "skill": "python", "count": 1100, "city": "Berlin"},
    {"lat": 48.8566, "lng": 2.3522, "skill": "security", "count": 560, "city": "Paris"},
    {"lat": 51.5074, "lng": -0.1278, "skill": "go", "count": 890, "city": "London"},
    # Remote/Digital Nomads
    {"lat": -8.4095, "lng": 115.1889, "skill": "python", "count": 320, "city": "Bali"},
    {"lat": 38.7223, "lng": -9.1393, "skill": "rust", "count": 180, "city": "Lisbon"},
    {"lat": 13.7563, "lng": 100.5018, "skill": "react", "count": 410, "city": "Bangkok"}
]

# Advanced Talent Analytics
DIVERSITY_METRICS = {
    "Bengaluru": {"Gender": {"M": 62, "F": 38}, "DiversityIndex": 0.84, "Seniority": {"Junior": 25, "Mid": 50, "Senior": 25}},
    "San Francisco": {"Gender": {"M": 58, "F": 42}, "DiversityIndex": 0.91, "Seniority": {"Junior": 15, "Mid": 45, "Senior": 40}},
    "Berlin": {"Gender": {"M": 60, "F": 40}, "DiversityIndex": 0.88, "Seniority": {"Junior": 20, "Mid": 55, "Senior": 25}},
    "London": {"Gender": {"M": 59, "F": 41}, "DiversityIndex": 0.89, "Seniority": {"Junior": 18, "Mid": 52, "Senior": 30}},
    "Pune": {"Gender": {"M": 65, "F": 35}, "DiversityIndex": 0.81, "Seniority": {"Junior": 30, "Mid": 50, "Senior": 20}}
}

MIGRATION_FLOWS = [
    {"source": [12.9716, 77.5946], "target": [37.7749, -122.4194], "volume": 140, "label": "Bengaluru -> SF"},
    {"source": [51.5074, -0.1278], "target": [52.5200, 13.4050], "volume": 85, "label": "London -> Berlin"},
    {"source": [28.6139, 77.209, "Delhi"], "target": [12.9716, 77.5946, "Bengaluru"], "volume": 320, "label": "Internal Migration"},
    {"source": [-8.4095, 115.1889], "target": [13.7563, 100.5018], "volume": 45, "label": "Nomad Flow"}
]

MARKET_COMPETITION = {
    "Bengaluru": {"Difficulty": "High", "TimeFill": "45 days", "TopCompetitors": ["Flipkart", "Infosys", "Google"]},
    "San Francisco": {"Difficulty": "Extreme", "TimeFill": "68 days", "TopCompetitors": ["OpenAI", "Meta", "Anthropic"]},
    "Berlin": {"Difficulty": "Medium", "TimeFill": "38 days", "TopCompetitors": ["SAP", "HelloFresh", "Zalando"]},
    "London": {"Difficulty": "High", "TimeFill": "52 days", "TopCompetitors": ["Revolut", "DeepMind", "Barclays"]}
}

# Skill Demand Trends (MoM velocity)
SKILL_TRENDS = {
    "python":     {"trend": "+18%", "dir": "up",   "qoq": "+31%", "rank": 1},
    "javascript": {"trend": "+12%", "dir": "up",   "qoq": "+22%", "rank": 2},
    "react":      {"trend": "+9%",  "dir": "up",   "qoq": "+15%", "rank": 3},
    "rust":       {"trend": "+41%", "dir": "up",   "qoq": "+78%", "rank": 4},
    "java":       {"trend": "-3%",  "dir": "down", "qoq": "-7%",  "rank": 5},
    "go":         {"trend": "+22%", "dir": "up",   "qoq": "+36%", "rank": 6},
    "aws":        {"trend": "+14%", "dir": "up",   "qoq": "+29%", "rank": 7},
    "kubernetes": {"trend": "+19%", "dir": "up",   "qoq": "+35%", "rank": 8},
    "ai":         {"trend": "+62%", "dir": "up",   "qoq": "+110%","rank": 9},
    "ml":         {"trend": "+55%", "dir": "up",   "qoq": "+89%", "rank": 10},
    "docker":     {"trend": "+7%",  "dir": "up",   "qoq": "+11%", "rank": 11},
    "sql":        {"trend": "-1%",  "dir": "down", "qoq": "-2%",  "rank": 12},
}

# Regional Salary Benchmarks (INR LPA / USD K based on region)
SALARY_BENCHMARKS = {
    "Bengaluru":    {"currency": "₹", "unit": "LPA", "Junior": "8–14",  "Mid": "18–32",  "Senior": "38–65",  "Lead": "70–120"},
    "Pune":         {"currency": "₹", "unit": "LPA", "Junior": "7–12",  "Mid": "16–28",  "Senior": "32–58",  "Lead": "60–100"},
    "Hyderabad":    {"currency": "₹", "unit": "LPA", "Junior": "7–13",  "Mid": "17–30",  "Senior": "35–62",  "Lead": "65–110"},
    "San Francisco":{"currency": "$", "unit": "K",   "Junior": "95–130","Mid": "145–195","Senior": "210–290","Lead": "300–450"},
    "Berlin":       {"currency": "€", "unit": "K",   "Junior": "45–60", "Mid": "65–90",  "Senior": "95–130", "Lead": "140–200"},
    "London":       {"currency": "£", "unit": "K",   "Junior": "50–70", "Mid": "80–110", "Senior": "120–160","Lead": "175–260"},
    "Singapore":    {"currency": "S$","unit": "K",   "Junior": "55–75", "Mid": "85–120", "Senior": "130–175","Lead": "190–280"},
    "Bangkok":      {"currency": "฿", "unit": "K/mo","Junior": "40–65", "Mid": "75–120", "Senior": "130–200","Lead": "210–350"},
}

# Remote vs On-site preferences per city
REMOTE_PROFILES = {
    "Bengaluru":    {"Remote": 42, "Hybrid": 38, "OnSite": 20, "trend": "Remote ↑"},
    "San Francisco":{"Remote": 61, "Hybrid": 28, "OnSite": 11, "trend": "Remote ↑↑"},
    "Berlin":       {"Remote": 55, "Hybrid": 32, "OnSite": 13, "trend": "Hybrid ↑"},
    "London":       {"Remote": 48, "Hybrid": 35, "OnSite": 17, "trend": "Hybrid ↑"},
    "Pune":         {"Remote": 38, "Hybrid": 40, "OnSite": 22, "trend": "Hybrid ↑"},
    "Singapore":    {"Remote": 35, "Hybrid": 42, "OnSite": 23, "trend": "Stable"},
    "Bangkok":      {"Remote": 58, "Hybrid": 30, "OnSite": 12, "trend": "Remote ↑"},
    "Hyderabad":    {"Remote": 40, "Hybrid": 39, "OnSite": 21, "trend": "Hybrid ↑"},
}

# Talent Pipeline Health Score (composite of supply, growth, quality)
PIPELINE_HEALTH = {
    "Bengaluru":    {"Score": 91, "Grade": "A+", "Supply": "High",   "Growth": "+18%", "Quality": "Excellent"},
    "Hyderabad":    {"Score": 86, "Grade": "A",  "Supply": "High",   "Growth": "+14%", "Quality": "Very Good"},
    "Pune":         {"Score": 82, "Grade": "A",  "Supply": "Medium", "Growth": "+11%", "Quality": "Good"},
    "San Francisco":{"Score": 78, "Grade": "B+", "Supply": "Low",    "Growth": "+6%",  "Quality": "Excellent"},
    "Berlin":       {"Score": 80, "Grade": "A-", "Supply": "Medium", "Growth": "+12%", "Quality": "Very Good"},
    "London":       {"Score": 77, "Grade": "B+", "Supply": "Medium", "Growth": "+9%",  "Quality": "Excellent"},
    "Singapore":    {"Score": 74, "Grade": "B",  "Supply": "Low",    "Growth": "+8%",  "Quality": "Very Good"},
    "Bangkok":      {"Score": 68, "Grade": "B-", "Supply": "Medium", "Growth": "+15%", "Quality": "Good"},
}

@app.route('/api/talent-heatmap', methods=['GET'])
def get_talent_heatmap():
    skill = request.args.get('skill', '').lower()
    points = TALENT_POOL
    if skill:
        points = [p for p in TALENT_POOL if p['skill'] == skill]
        if not points:
            points = [p for p in TALENT_POOL if random.random() > 0.7]
    
    return jsonify({
        "points": points,
        "migration": MIGRATION_FLOWS,
        "metrics": DIVERSITY_METRICS,
        "market": MARKET_COMPETITION
    })

@app.route('/api/talent-analytics', methods=['GET'])
def get_talent_analytics():
    skill = request.args.get('skill', 'python').lower()
    city = request.args.get('city', 'Bengaluru')
    
    trend = SKILL_TRENDS.get(skill, {"trend": "+5%", "dir": "up", "qoq": "+8%", "rank": 99})
    salary = SALARY_BENCHMARKS.get(city, SALARY_BENCHMARKS["Bengaluru"])
    remote = REMOTE_PROFILES.get(city, REMOTE_PROFILES["Bengaluru"])
    health = PIPELINE_HEALTH.get(city, PIPELINE_HEALTH["Bengaluru"])
    
    # Top 5 trending skills
    top_skills = sorted(SKILL_TRENDS.items(), key=lambda x: x[1]['rank'])[:6]
    
    return jsonify({
        "skill_trend": trend,
        "salary": salary,
        "remote_profile": remote,
        "pipeline_health": health,
        "all_cities_health": PIPELINE_HEALTH,
        "all_salaries": SALARY_BENCHMARKS,
        "top_skills": [{"skill": k, **v} for k, v in top_skills],
        "all_remote": REMOTE_PROFILES
    })

def anonymize_text(text, name=None):
    # Redact Emails
    text = re.sub(r'\S+@\S+\.\S+', '[EMAIL REDACTED]', text)
    # Redact Phone Numbers
    text = re.sub(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{10})', '[PHONE REDACTED]', text)
    # Redact specific candidate name if provided
    if name:
        text = re.sub(re.escape(name), '[NAME REDACTED]', text, flags=re.IGNORECASE)
    # Redact location patterns
    text = re.sub(r'(?i)(Address|Location|City|State|Zip|Street):?\s*[^\n]+', r'\1: [REDACTED]', text)
    return text

@app.route('/api/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Read file bytes directly into memory — no disk writes (required for Vercel serverless)
        file_bytes = file.read()
        if not file_bytes:
            return jsonify({"error": "Uploaded file is empty"}), 400

        # Parse Resume from memory
        text = extract_text_from_bytes(file_bytes, file.filename)
        if not text:
            return jsonify({"error": "Failed to extract text from resume. Ensure it's a valid PDF or TXT file."}), 400
            
        cleaned_text = clean_text(text)
        skills = extract_skills(cleaned_text)
        
        candidate_id = request.form.get('candidate_id')
        if not candidate_id:
            candidate_id = str(uuid.uuid4())
            
        if candidate_id not in candidates:
            candidates[candidate_id] = {
                "id": candidate_id,
                "name": request.form.get('name', 'Anonymous'),
                "resumes": []
            }
        
        # Anonymize resume for blind screening
        anonymized_text = anonymize_text(cleaned_text, candidates[candidate_id]['name'])
        
        resume_entry = {
            "id": str(uuid.uuid4()),
            "skills": skills,
            "text": cleaned_text,
            "anonymized_text": anonymized_text,
            "filename": file.filename,
            "timestamp": str(uuid.uuid4())[:8]
        }
        candidates[candidate_id]["resumes"].append(resume_entry)
        
        # Get recommendations using the LATEST resume
        recommendations = []
        for job in jobs:
            similarity = calculate_similarity(cleaned_text, job['description'])
            gap = analyze_skill_gap(skills, job['skills'])
            culture_score, trait, sentiment = calculate_culture_fit(skills, job['company'])
            salary = predict_salary(job['title'], skills)
            
            recommendations.append({
                "job_id": job['id'],
                "title": job['title'],
                "company": job['company'],
                "score": round(similarity * 100, 2),
                "gap": gap,
                "culture_score": culture_score,
                "culture_trait": trait,
                "glassdoor_sentiment": sentiment,
                "salary_range": salary['range'],
                "salary_trend": salary['trend']
            })
        
        # Sort by score
        recommendations = sorted(recommendations, key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            "candidate_id": candidate_id,
            "resumes": candidates[candidate_id]["resumes"],
            "recommendations": recommendations
        })
    except Exception as e:
        app.logger.error(f"Upload Error: {str(e)}")
        return jsonify({"error": "Internal server error during processing", "details": str(e)}), 500
@app.route('/api/rank/<int:job_id>', methods=['GET'])
def rank_candidates(job_id):
    from hr_module.scheduler import hr_scheduler
    job = next((j for j in jobs if j['id'] == job_id), None)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    # Only show candidates who have actually applied for this specific job
    job_applications = [a for a in applications if a['job_id'] == job_id]
    
    rankings = []
    for app_record in job_applications:
        c_id = app_record['candidate_id']
        cand = candidates.get(c_id)
        if not cand or not cand["resumes"]: continue
        
        # Use the latest resume for ranking
        latest_resume = cand["resumes"][-1]
        similarity = calculate_similarity(latest_resume['text'], job['description'])
        
        # Check if HR interview scheduled
        hr_interviews = hr_scheduler.get_hr_interviews(candidate_id=c_id, job_id=job_id)
        is_scheduled = any(i['status'] == 'Scheduled' for i in hr_interviews)
        
        curr_status = app_record.get('status', 'AI Screening')
        
        stages = ["Screening", "Assessment", "Interviews", "Offer", "Hired"]
        stage_index = next((i for i, s in enumerate(stages) if s.lower() in curr_status.lower()), 0)

        rankings.append({
            "candidate_id": c_id,
            "name": cand['name'],
            "score": round(similarity * 100, 2),
            "skills": latest_resume['skills'],
            "is_scheduled": is_scheduled,
            "status": curr_status,
            "stage_index": stage_index
        })
    
    rankings = sorted(rankings, key=lambda x: x['score'], reverse=True)
    return jsonify(rankings)

@app.route('/api/apply', methods=['POST'])
def apply_for_job():
    data = request.json
    candidate_id = data.get('candidate_id')
    job_id = data.get('job_id')
    
    if not candidate_id or not job_id:
        return jsonify({"error": "Missing ID"}), 400
    
    # Check if already applied
    if any(a['candidate_id'] == candidate_id and a['job_id'] == job_id for a in applications):
        return jsonify({"message": "Already applied"}), 200
        
    applications.append({
        "candidate_id": candidate_id,
        "job_id": job_id,
        "status": "AI Screening"
    })
    return jsonify({"message": "Application successful"}), 201

@app.route('/api/assessment/submit', methods=['POST'])
def submit_assessment():
    data = request.json
    c_id = data.get('candidate_id')
    j_id = data.get('job_id')
    score = data.get('score', 85)
    
    for app_record in applications:
        if app_record['candidate_id'] == c_id and app_record['job_id'] == j_id:
            app_record['status'] = "Interviews" # Auto-advance on pass
            app_record['assessment_score'] = score
            return jsonify({"message": "Assessment passed! You are now in the Interview stage."}), 200
    return jsonify({"error": "Application not found"}), 404


@app.route('/api/user/applications/<candidate_id>', methods=['GET'])
def fetch_user_applications(candidate_id):
    from hr_module.scheduler import hr_scheduler
    user_apps = [a for a in applications if a['candidate_id'] == candidate_id]
    
    results = []
    for app_record in user_apps:
        job = next((j for j in jobs if j['id'] == app_record['job_id']), None)
        if job:
            # Check for HR interviews
            hr_interviews = hr_scheduler.get_hr_interviews(candidate_id=candidate_id, job_id=job['id'])
            interview = next((i for i in hr_interviews if i['status'] == 'Scheduled'), None)
            
            stages = ["Screening", "Assessment", "Interviews", "Offer", "Hired"]
            curr_status = app_record.get('status', 'AI Screening')
            
            results.append({
                "job_id": job['id'],
                "company": job['company'],
                "title": job['title'],
                "status": curr_status,
                "interview_details": f"{interview['date']} at {interview['time']}" if interview else None,
                "has_interview": True if interview else False,
                "stage_index": next((i for i, s in enumerate(stages) if s.lower() in curr_status.lower()), 0)
            })
    return jsonify(results)

@app.route('/api/video/analyze', methods=['POST'])
def analyze_video():
    data = request.json
    c_id = data.get('candidate_id')
    if not c_id:
        return jsonify({"error": "Missing Candidate ID"}), 400
        
    # Simulate AI Analysis Delay
    # In reality, this would use AssemblyAI, AffectNet, etc.
    analysis = {
        "score": random.randint(75, 95),
        "sentiment": random.choice(["Highly Positive", "Professional & Confident", "Energetic"]),
        "confidence": random.randint(80, 98),
        "transcript": "Hello, I am a passionate developer with a strong background in Python and AI. I love building scalable applications and solving complex problems.",
        "keywords": ["Python", "AI", "Scalable", "Problem Solving"],
        "emotion_summary": {
            "Joy": "24%",
            "Composure": "68%",
            "Interest": "8%"
        }
    }
    
    if c_id in candidates:
        candidates[c_id]['video_analysis'] = analysis
        
    return jsonify(analysis)

@app.route('/api/resume/optimize', methods=['POST'])
def optimize_resume():
    data = request.json
    c_id = data.get('candidate_id')
    job_id = data.get('job_id')
    resume_id = data.get('resume_id')
    
    if not c_id or not job_id:
        return jsonify({"error": "Missing parameters"}), 400
        
    cand = candidates.get(c_id)
    if not cand:
        return jsonify({"error": "Candidate not found"}), 404
        
    # Find the source resume
    source_resume = next((r for r in cand['resumes'] if r['id'] == resume_id), cand['resumes'][-1])
    
    # Extract target job keywords
    job = next((j for j in jobs if j['id'] == int(job_id)), None)
    job_skills = job['skills'] if job else []
    
    # Simulate LLM Optimization (Rewriting sections)
    optimized_skills = list(set(source_resume['skills'] + job_skills[:2]))
    new_version = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "filename": f"Optimized_{source_resume['filename']}",
        "skills": optimized_skills,
        "is_optimized": True,
        "target_job": job['title'] if job else "Custom",
        "ats_score": random.randint(85, 98)
    }
    
    cand['resumes'].append(new_version)
    return jsonify({
        "message": "Resume optimized successfully",
        "new_version": new_version
    })

@app.route('/api/candidate/<candidate_id>', methods=['GET'])
def get_candidate_profile(candidate_id):
    cand = candidates.get(candidate_id)
    if not cand:
        return jsonify({"error": "Candidate not found"}), 404
        
    # Return full candidate data
    return jsonify(cand)

@app.route('/api/feedback/submit', methods=['POST'])
def submit_feedback():
    data = request.json
    c_id = data.get('candidate_id')
    
    if c_id not in candidates:
        return jsonify({"error": "Candidate not found"}), 404
        
    feedback = {
        "id": str(uuid.uuid4()),
        "interviewer": data.get('interviewer', 'Anonymous'),
        "ratings": data.get('ratings', {}), # e.g. {"technical": 4, "culture": 3}
        "comments": data.get('comments', ''),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    if 'interviews' not in candidates[c_id]:
        candidates[c_id]['interviews'] = []
    
    candidates[c_id]['interviews'].append(feedback)
    return jsonify({"message": "Feedback submitted", "feedback": feedback})

@app.route('/api/feedback/synthesize/<candidate_id>', methods=['GET'])
def synthesize_feedback(candidate_id):
    cand = candidates.get(candidate_id)
    if not cand or 'interviews' not in cand:
        return jsonify({"error": "No feedback found"}), 404
        
    feedbacks = cand['interviews']
    if not feedbacks:
        return jsonify({"error": "Empty feedback pool"}), 404
        
    # Aggregate ratings
    categories = ["technical", "culture", "communication"]
    aggregation = {cat: [f['ratings'].get(cat, 0) for f in feedbacks if cat in f['ratings']] for cat in categories}
    
    # Calculate Consensus & Conflict
    report = {
        "consensus": [],
        "conflicts": [],
        "overall_score": 0,
        "summary": "AI Sourced Breakdown: "
    }
    
    total_avg = 0
    cat_count = 0
    
    for cat, scores in aggregation.items():
        if not scores: continue
        avg = sum(scores) / len(scores)
        variance = max(scores) - min(scores) if len(scores) > 1 else 0
        
        if variance > 1.5:
            report["conflicts"].append({"trait": cat, "details": f"High divergence in {cat} scores. Review required."})
        elif avg >= 4:
            report["consensus"].append({"trait": cat, "sentiment": "Strong Agreement", "score": avg})
            
        total_avg += avg
        cat_count += 1
        
    report["overall_score"] = int((total_avg / cat_count) * 20) if cat_count > 0 else 0
    
    # Simulated Text Synthesis (LLM logic simulation)
    comments = " ".join([f['comments'] for f in feedbacks])
    if "Python" in comments: report["summary"] += "Candidate shows strong depth in Python ecosystem. "
    if "teamwork" in comments or "collaborative" in comments: report["summary"] += "Consensus on strong cultural alignment. "
    if "slow" in comments or "delay" in comments: report["summary"] += "Concerns noted regarding pace of technical execution. "
    
    return jsonify(report)

@app.route('/api/candidate/<candidate_id>/resume/<resume_id>', methods=['GET'])
def get_historical_resume(candidate_id, resume_id):
    cand = candidates.get(candidate_id)
    if not cand:
        return jsonify({"error": "Candidate not found"}), 404
        
    resume = next((r for r in cand["resumes"] if r['id'] == resume_id), None)
    if not resume:
        return jsonify({"error": "Resume not found"}), 404
        
    # Recalculate recommendations for this specific resume
    recommendations = []
    for job in jobs:
        similarity = calculate_similarity(resume['text'], job['description'])
        gap = analyze_skill_gap(resume['skills'], job['skills'])
        culture_score, trait, sentiment = calculate_culture_fit(resume['skills'], job['company'])
        salary = predict_salary(job['title'], resume['skills'])
        
        recommendations.append({
            "job_id": job['id'],
            "title": job['title'],
            "company": job['company'],
            "score": round(similarity * 100, 2),
            "gap": gap,
            "culture_score": culture_score,
            "culture_trait": trait,
            "glassdoor_sentiment": sentiment,
            "salary_range": salary['range'],
            "salary_trend": salary['trend']
        })
    
    recommendations = sorted(recommendations, key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        "candidate_id": candidate_id,
        "resumes": cand["resumes"],
        "recommendations": recommendations,
        "current_resume_id": resume_id
    })

@app.route('/api/schedule', methods=['POST'])
def schedule_interview():
    data = request.json
    candidate_id = data.get('candidate_id')
    job_id = data.get('job_id')
    date = data.get('date')
    
    if not candidate_id or not job_id:
        return jsonify({"error": "Missing info"}), 400
        
    interviews.append({
        "candidate_id": candidate_id,
        "job_id": job_id,
        "date": date,
        "time": data.get('time', '10:00 AM'),
        "type": data.get('type', 'Video Call (Google Meet)')
    })
    return jsonify({"message": "Interview scheduled"}), 201

@app.route('/api/career-trajectory/<candidate_id>', methods=['GET'])
def get_career_trajectory(candidate_id):
    cand = candidates.get(candidate_id)
    if not cand or not cand["resumes"]:
        return jsonify({"error": "Candidate or Resume not found"}), 404
        
    latest_resume = cand["resumes"][-1]
    skills = latest_resume['skills']
    
    # Predict based on highest matching skill in our graph
    predicted_path = []
    for skill in skills:
        if skill in CAREER_GRAPH:
            predicted_path = CAREER_GRAPH[skill]
            break
            
    if not predicted_path:
        predicted_path = ["Senior Professional", "Specialist", "Team Lead", "Manager", "Executive"]
        
    return jsonify({
        "job_title": "Career Path",
        "roadmap": predicted_path
    })

@app.route('/api/interview-prep/<candidate_id>/<int:job_id>', methods=['GET'])
def get_interview_prep(candidate_id, job_id):
    job = next((j for j in jobs if j['id'] == job_id), None)
    cand = candidates.get(candidate_id)
    if not job or not cand:
        return jsonify({"error": "Data not found"}), 404
        
    latest = cand["resumes"][-1]
    # AI Reasoning Simulation
    questions = [
        f"Based on your profile, how do you plan to use {latest['skills'][0].capitalize()} to contribute to {job['company']}?",
        f"Tell us about a time you applied {latest['skills'][1].capitalize()} in a challenging project.",
        f"The {job['title']} role requires strong problem solving. Can you walk us through your most complex implementation?",
        "How do you stay updated with rapidly evolving tech trends?",
        "What's your preferred approach to collaborating in a cross-functional team?"
    ]
    return jsonify({
        "job_title": job['title'],
        "company": job['company'],
        "questions": questions,
        "tips": ["Research the STAR method", f"Look into {job['company']}'s latest technical blogs", "Prepare questions for the interviewer"]
    })

@app.route('/api/learning-roadmap/<candidate_id>/<int:job_id>', methods=['GET'])
def get_learning_roadmap(candidate_id, job_id):
    cand = candidates.get(candidate_id)
    job = next((j for j in jobs if j['id'] == job_id), None)
    
    if not cand or not job:
        return jsonify({"error": "Data not found"}), 404
        
    latest_resume = cand["resumes"][-1]
    gap = analyze_skill_gap(latest_resume['skills'], job['skills'])
    missing = gap['missing_skills']
    
    roadmap = []
    for i, skill in enumerate(missing):
        course = COURSE_CATALOG.get(skill.lower(), {
            "title": f"Mastering {skill.capitalize()}",
            "platform": "Industry Standard",
            "url": "#"
        })
        roadmap.append({
            "week": i + 1,
            "skill": skill,
            "course": course['title'],
            "platform": course['platform'],
            "url": course['url'],
            "effort": "10-12 hours"
        })
        
    return jsonify({
        "job_title": job['title'],
        "roadmap": roadmap
    })

@app.route('/api/rank/<int:job_id>/export', methods=['GET'])
def export_rankings(job_id):
    job = next((j for j in jobs if j['id'] == job_id), None)
    if not job:
        return "Job not found", 404
        
    applicant_ids = [app['candidate_id'] for app in applications if app['job_id'] == job_id]
    
    # Collect and sort data first
    export_data = []
    for c_id in applicant_ids:
        cand = candidates.get(c_id)
        if cand and cand["resumes"]:
            latest = cand["resumes"][-1]
            score = round(calculate_similarity(latest['text'], job['description']) * 100, 2)
            gap = analyze_skill_gap(latest['skills'], job['skills'])
            export_data.append({
                "Name": cand['name'],
                "Match Score": f"{score}%",
                "Candidate Skills": ", ".join(latest['skills']),
                "Missing Skills": ", ".join(gap['missing_skills']),
                "Status": "Interview Scheduled" if any(i['candidate_id'] == c_id and i['job_id'] == job_id for i in interviews) else "Applied"
            })
    
    # Sort by score descending
    export_data.sort(key=lambda x: float(x['Match Score'].replace('%', '')), reverse=True)
    
    # Generate CSV using io.StringIO
    output = io.StringIO()
    # Add a title row
    output.write(f"Candidate Ranking Report for {job['title']} at {job['company']}\n\n")
    
    if export_data:
        writer = csv.DictWriter(output, fieldnames=["Name", "Match Score", "Candidate Skills", "Missing Skills", "Status"])
        writer.writeheader()
        writer.writerows(export_data)
    else:
        output.write("No applicants found for this position.")
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=Ranking_{job["title"].replace(" ", "_")}.csv'
    }

@app.route('/api/application/status', methods=['POST'])
def update_application_status():
    data = request.json
    c_id = data.get('candidate_id')
    j_id = data.get('job_id')
    new_status = data.get('status')
    
    for app in applications:
        if app['candidate_id'] == c_id and app['job_id'] == j_id:
            app['status'] = new_status
            return jsonify({"message": f"Status updated to {new_status}"}), 200
            
    return jsonify({"error": "Application not found"}), 404

@app.errorhandler(500)
def handle_500(e):
    app.logger.error(f"Internal Server Error: {e}")
    return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

def seed_data():
    """Seed the database with realistic candidate records for the HR portal demo"""
    global candidates, applications
    
    mock_candidates = [
        {"id": "cand-001", "name": "Arjun Mehta", "skills": ["python", "flask", "react", "sql"], "resumes": [{"id": "r1", "text": "Arjun Mehta - Senior Software Engineer with 5 years experience in Python and React...", "skills": ["python", "flask", "react", "sql"]}]},
        {"id": "cand-002", "name": "Priya Sharma", "skills": ["python", "machine learning", "nlp"], "resumes": [{"id": "r2", "text": "Priya Sharma - Data Scientist specializing in NLP and predictive modeling...", "skills": ["python", "machine learning", "nlp"]}]},
        {"id": "cand-003", "name": "Rahul Iyer", "skills": ["javascript", "html", "css", "react"], "resumes": [{"id": "r3", "text": "Rahul Iyer - Frontend Developer focused on creating stunning user experiences...", "skills": ["javascript", "html", "css", "react"]}]},
        {"id": "cand-004", "name": "Sneha Gupta", "skills": ["docker", "kubernetes", "aws", "python"], "resumes": [{"id": "r4", "text": "Sneha Gupta - DevOps Engineer with a passion for automation and cloud infrastructure...", "skills": ["docker", "kubernetes", "aws", "python"]}]}
    ]
    
    for c in mock_candidates:
        candidates[c["id"]] = c
        
    # Seed applications
    applications.extend([
        {"candidate_id": "cand-001", "job_id": 1, "status": "Assessment"},
        {"candidate_id": "cand-003", "job_id": 3, "status": "Assessment"},
        {"candidate_id": "cand-002", "job_id": 2, "status": "Screening"},
        {"candidate_id": "cand-004", "job_id": 4, "status": "Interviews"}
    ])

if __name__ == '__main__':
    seed_data()
    app.run(debug=True, port=3000)
