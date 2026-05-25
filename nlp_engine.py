import PyPDF2
import re
import io
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_text_from_bytes(file_bytes, filename):
    """Extract text from a file given its raw bytes and original filename.
    Works in serverless environments where disk I/O is not available."""
    text = ""
    extension = os.path.splitext(filename)[1].lower() if filename else ""

    try:
        if extension == ".pdf":
            pdf_stream = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            for page in pdf_reader.pages:
                content = page.extract_text()
                if content:
                    text += content + " "
        elif extension == ".txt":
            text = file_bytes.decode("utf-8", errors="ignore")
        else:
            # Try PDF first, fallback to plain text decode
            try:
                pdf_stream = io.BytesIO(file_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_stream)
                for page in pdf_reader.pages:
                    content = page.extract_text()
                    if content:
                        text += content + " "
            except Exception:
                text = file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error extracting file {filename}: {e}")

    return text.strip()


import os  # kept at bottom to avoid circular; safe here


def extract_text_from_file(file_path):
    """Legacy helper — reads from disk. Only used in local dev."""
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "rb") as f:
            return extract_text_from_bytes(f.read(), file_path)
    except Exception as e:
        print(f"Error extracting file {file_path}: {e}")
        return ""


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    return text


def extract_skills(text):
    if not text:
        return []
    skill_set = [
        "python", "javascript", "react", "node.js", "flask", "django", "html", "css",
        "sql", "mongodb", "aws", "docker", "kubernetes", "machine learning", "nlp",
        "java", "c++", "c#", "php", "ruby", "rust", "go", "swift", "kotlin", "flutter",
        "tensorflow", "pytorch", "tableau", "power bi", "excel", "git", "rest api",
        "graphql", "devops", "ci/cd", "azure", "gcp", "typescript", "vue.js", "angular"
    ]
    extracted = []
    text_lower = text.lower()
    for skill in skill_set:
        if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
            extracted.append(skill)
    return extracted


def calculate_similarity(resume_text, job_description):
    if not resume_text or not job_description:
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(similarity[0][0])
    except Exception as e:
        print(f"Similarity Error: {e}")
        return 0.0


def analyze_skill_gap(resume_skills, job_skills):
    missing_skills = [skill for skill in job_skills if skill not in resume_skills]
    match_percentage = (len(resume_skills) / len(job_skills)) * 100 if job_skills else 100
    return {
        "missing_skills": missing_skills,
        "match_percentage": match_percentage,
    }
