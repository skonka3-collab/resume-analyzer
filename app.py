import re
from io import BytesIO

import PyPDF2
import streamlit as st
from deep_translator import GoogleTranslator
from langdetect import DetectorFactory, LangDetectException, detect


DetectorFactory.seed = 0

COMMON_SKILLS = [
    "Python",
    "Java",
    "C++",
    "SQL",
    "Machine Learning",
    "Deep Learning",
    "Data Science",
    "Artificial Intelligence",
    "HTML",
    "CSS",
    "JavaScript",
    "React",
    "Git",
    "Linux",
    "AWS",
    "Azure",
    "Docker",
    "Kubernetes",
]

SUPPORTED_LANGUAGES = {
    "Auto Detect": "auto",
    "English": "en",
    "Telugu": "te",
    "Hindi": "hi",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",
}

LANGUAGE_NAMES_BY_CODE = {code: name for name, code in SUPPORTED_LANGUAGES.items() if code != "auto"}
SUPPORTED_LANGUAGE_CODES = set(LANGUAGE_NAMES_BY_CODE)

SECTION_PATTERNS = {
    "skills": r"\b(skills|technical skills|core competencies|technologies|tools|programming languages)\b",
    "education": r"\b(education|academic background|qualification|qualifications|degree|university|college|bachelor|master|b\.tech|m\.tech|bsc|msc|mba)\b",
    "experience": r"\b(experience|work experience|employment|internship|professional experience|responsibilities|company|role)\b",
    "projects": r"\b(projects|project experience|portfolio|built|developed|implemented)\b",
    "certifications": r"\b(certifications|certification|certified|courses|licenses|licences|training)\b",
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}

UI_LANGUAGES = {
    "English": "en",
    "తెలుగు": "te",
}

UI_TEXT = {
    "en": {
        "app_title": "Resume Analyzer",
        "hero": "Upload an English or Indian-language PDF resume, translate when needed, and analyze it for ATS readiness.",
        "interface_language": "Website language",
        "upload_resume": "Upload Resume",
        "choose_pdf": "Choose a PDF file",
        "resume_language": "Resume language",
        "language_caption": "Auto Detect supports English, Telugu, Hindi, Tamil, Kannada, and Malayalam.",
        "job_match": "Job Description Match",
        "paste_jd": "Paste job description",
        "jd_placeholder": "Optional: paste a job description to calculate keyword match.",
        "scoring_weights": "Scoring Weights",
        "upload_info": "Upload a PDF resume from the sidebar to begin analysis.",
        "checks_info": "The analyzer checks extraction, translation, word count, pages, skills, sections, ATS score, job match, and improvement areas.",
        "extracting": "Extracting resume text...",
        "translating": "Translating resume to English for analysis...",
        "preparing": "Preparing analysis...",
        "analysis_overview": "Analysis Overview",
        "language": "Language",
        "total_words": "Total Words",
        "total_pages": "Total Pages",
        "skills_found": "Skills Found",
        "ats_score": "ATS Resume Score",
        "excellent": "Excellent",
        "good": "Good",
        "needs_work": "Needs work",
        "major_improvement": "Needs major improvement",
        "job_match_score": "Job Match Score",
        "no_keyword_overlap": "No strong keyword overlap found with the job description.",
        "score_breakdown": "Score Breakdown",
        "detected_skills": "Detected Skills",
        "no_skills": "No common tracked skills were detected.",
        "education_details": "Education Details",
        "experience_details": "Experience Details",
        "education_text": "Detected education-related text",
        "experience_text": "Detected experience-related text",
        "education_missing": "Education section was not detected.",
        "experience_missing": "Experience section was not detected.",
        "strengths": "Strengths",
        "improvements": "Areas for Improvement",
        "suggestions": "Resume Improvement Suggestions",
        "extracted_text": "Extracted Resume Text",
        "original_text": "Original extracted text",
        "translated_text_expander": "Translated English Text Used for Analysis",
        "translated_text": "Translated text",
        "jd_translation_warning": "Could not translate the job description. Job match will use the text as entered.",
        "breakdown_skills": "Skills",
        "breakdown_education": "Education",
        "breakdown_experience": "Experience",
        "breakdown_projects": "Projects",
        "breakdown_certifications": "Certifications",
    },
    "te": {
        "app_title": "రెజ్యూమ్ విశ్లేషణ",
        "hero": "ఇంగ్లీష్ లేదా భారతీయ భాషలో ఉన్న PDF రెజ్యూమ్‌ను అప్లోడ్ చేసి, అవసరమైతే అనువదించి, ATS సిద్ధతను విశ్లేషించండి.",
        "interface_language": "వెబ్‌సైట్ భాష",
        "upload_resume": "రెజ్యూమ్ అప్లోడ్ చేయండి",
        "choose_pdf": "PDF ఫైల్ ఎంచుకోండి",
        "resume_language": "రెజ్యూమ్ భాష",
        "language_caption": "Auto Detect ఇంగ్లీష్, తెలుగు, హిందీ, తమిళం, కన్నడ, మలయాళం భాషలను సపోర్ట్ చేస్తుంది.",
        "job_match": "ఉద్యోగ వివరణ సరిపోలిక",
        "paste_jd": "ఉద్యోగ వివరణను పేస్ట్ చేయండి",
        "jd_placeholder": "ఐచ్చికం: కీవర్డ్ సరిపోలిక కోసం ఉద్యోగ వివరణను పేస్ట్ చేయండి.",
        "scoring_weights": "స్కోరింగ్ వెయిట్స్",
        "upload_info": "విశ్లేషణ ప్రారంభించడానికి సైడ్‌బార్ నుంచి PDF రెజ్యూమ్‌ను అప్లోడ్ చేయండి.",
        "checks_info": "ఈ యాప్ టెక్స్ట్ ఎక్స్‌ట్రాక్షన్, అనువాదం, పదాల సంఖ్య, పేజీలు, నైపుణ్యాలు, సెక్షన్లు, ATS స్కోర్, ఉద్యోగ సరిపోలిక మరియు మెరుగుదల అంశాలను చెక్ చేస్తుంది.",
        "extracting": "రెజ్యూమ్ టెక్స్ట్ తీసుకుంటోంది...",
        "translating": "విశ్లేషణ కోసం రెజ్యూమ్‌ను ఇంగ్లీష్‌కు అనువదిస్తోంది...",
        "preparing": "విశ్లేషణ సిద్ధం చేస్తోంది...",
        "analysis_overview": "విశ్లేషణ సారాంశం",
        "language": "భాష",
        "total_words": "మొత్తం పదాలు",
        "total_pages": "మొత్తం పేజీలు",
        "skills_found": "గుర్తించిన నైపుణ్యాలు",
        "ats_score": "ATS రెజ్యూమ్ స్కోర్",
        "excellent": "అద్భుతం",
        "good": "బాగుంది",
        "needs_work": "మెరుగుదల అవసరం",
        "major_improvement": "చాలా మెరుగుదల అవసరం",
        "job_match_score": "ఉద్యోగ సరిపోలిక స్కోర్",
        "no_keyword_overlap": "ఉద్యోగ వివరణతో బలమైన కీవర్డ్ సరిపోలిక కనిపించలేదు.",
        "score_breakdown": "స్కోర్ వివరాలు",
        "detected_skills": "గుర్తించిన నైపుణ్యాలు",
        "no_skills": "సాధారణంగా ట్రాక్ చేసే నైపుణ్యాలు కనిపించలేదు.",
        "education_details": "విద్య వివరాలు",
        "experience_details": "అనుభవం వివరాలు",
        "education_text": "గుర్తించిన విద్య సంబంధిత టెక్స్ట్",
        "experience_text": "గుర్తించిన అనుభవ సంబంధిత టెక్స్ట్",
        "education_missing": "విద్య సెక్షన్ కనిపించలేదు.",
        "experience_missing": "అనుభవం సెక్షన్ కనిపించలేదు.",
        "strengths": "బలాలు",
        "improvements": "మెరుగుపరచాల్సిన అంశాలు",
        "suggestions": "రెజ్యూమ్ మెరుగుదల సూచనలు",
        "extracted_text": "తీసుకున్న రెజ్యూమ్ టెక్స్ట్",
        "original_text": "అసలు తీసుకున్న టెక్స్ట్",
        "translated_text_expander": "విశ్లేషణకు ఉపయోగించిన ఇంగ్లీష్ అనువాదం",
        "translated_text": "అనువదించిన టెక్స్ట్",
        "jd_translation_warning": "ఉద్యోగ వివరణను అనువదించలేకపోయింది. ఉద్యోగ సరిపోలిక మీరు ఇచ్చిన టెక్స్ట్‌తోనే చేస్తుంది.",
        "breakdown_skills": "నైపుణ్యాలు",
        "breakdown_education": "విద్య",
        "breakdown_experience": "అనుభవం",
        "breakdown_projects": "ప్రాజెక్టులు",
        "breakdown_certifications": "సర్టిఫికేషన్లు",
    },
}


def t(ui_language: str, key: str) -> str:
    return UI_TEXT[ui_language].get(key, UI_TEXT["en"][key])


def configure_page() -> None:
    st.set_page_config(page_title="Resume Analyzer", page_icon="Resume", layout="wide")
    st.markdown(
        """
        <style>
            .main .block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}
            .hero {
                border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem;
                background: linear-gradient(135deg, #eff6ff 0%, #ffffff 55%, #f8fafc 100%);
                margin-bottom: 1.25rem;
            }
            .hero h1 {margin: 0 0 .35rem 0; color: #0f172a; letter-spacing: 0;}
            .hero p {margin: 0; color: #475569;}
            div[data-testid="stMetric"] {
                border: 1px solid #e2e8f0; border-radius: 8px; padding: .85rem 1rem;
                background: #f8fafc;
            }
            .pill {
                display: inline-block; border-radius: 999px; padding: .3rem .7rem;
                margin: .18rem .16rem; font-size: .9rem; font-weight: 600;
            }
            .skill {border: 1px solid #bfdbfe; background: #eff6ff; color: #1e40af;}
            .strength {border: 1px solid #bbf7d0; background: #f0fdf4; color: #166534;}
            .improve {border: 1px solid #fed7aa; background: #fff7ed; color: #9a3412;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def extract_text_from_pdf(uploaded_file) -> tuple[str, int, str | None]:
    try:
        reader = PyPDF2.PdfReader(BytesIO(uploaded_file.getvalue()))
        pages = len(reader.pages)
        text = "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)
        text = text.strip()
        if not text:
            return "", pages, "No readable text was found. This may be a scanned or image-based PDF."
        return text, pages, None
    except PyPDF2.errors.PdfReadError:
        return "", 0, "This PDF could not be read. Please upload a valid, unencrypted PDF."
    except Exception as exc:
        return "", 0, f"Unable to process this PDF: {exc}"


def detect_resume_language(text: str) -> str | None:
    """Detect resume language and return a supported language code when possible."""
    compact_text = re.sub(r"\s+", " ", text).strip()
    if len(compact_text) < 20:
        return None

    try:
        detected_code = detect(compact_text[:5000])
    except LangDetectException:
        return None

    return detected_code if detected_code in SUPPORTED_LANGUAGE_CODES else None


def resolve_language(text: str, selected_language: str) -> tuple[str | None, str | None]:
    selected_code = SUPPORTED_LANGUAGES[selected_language]
    detected_code = detect_resume_language(text)

    if selected_code == "auto":
        if detected_code is None:
            return None, "Could not detect a supported resume language. Please select the language manually."
        return detected_code, None

    if selected_code not in SUPPORTED_LANGUAGE_CODES:
        return None, f"{selected_language} is not supported."

    return selected_code, None


def translate_to_english(text: str, source_language: str) -> tuple[str, str | None]:
    """Translate supported non-English resumes to English before the analysis pipeline runs."""
    if source_language == "en":
        return text, None

    if source_language not in SUPPORTED_LANGUAGE_CODES:
        return "", "Unsupported language selected."

    try:
        translated_text = "\n\n".join(
            GoogleTranslator(source=source_language, target="en").translate(chunk)
            for chunk in split_text_for_translation(text)
        )
    except Exception as exc:
        return "", f"Translation failed. Check your internet connection and try again. Details: {exc}"

    if not translated_text or not translated_text.strip():
        return "", "Translation returned empty text. Please try another PDF or select the correct language."

    return translated_text.strip(), None


def split_text_for_translation(text: str, max_chars: int = 4500) -> list[str]:
    """Split long resume text so translation APIs do not reject oversized requests."""
    paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            chunks.extend(paragraph[index : index + max_chars] for index in range(0, len(paragraph), max_chars))
            continue

        candidate = f"{current_chunk}\n{paragraph}".strip()
        if len(candidate) <= max_chars:
            current_chunk = candidate
        else:
            chunks.append(current_chunk)
            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks or [text[:max_chars]]


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w+#.]+\b", text))


def detect_skills(text: str) -> list[str]:
    lowered = re.sub(r"\s+", " ", text).lower()
    found = []
    for skill in COMMON_SKILLS:
        pattern = rf"(?<![a-z0-9+#]){re.escape(skill.lower())}(?![a-z0-9+#])"
        if re.search(pattern, lowered):
            found.append(skill)
    return found


def detect_sections(text: str) -> dict[str, bool]:
    return {
        name: bool(re.search(pattern, text, flags=re.IGNORECASE))
        for name, pattern in SECTION_PATTERNS.items()
    }


def extract_section_snippet(text: str, section: str, max_chars: int = 650) -> str:
    aliases = {
        "education": ["education", "academic background", "qualification", "qualifications"],
        "experience": ["experience", "work experience", "employment", "internship", "professional experience"],
    }
    stop_words = list(SECTION_PATTERNS)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    start = None

    for index, line in enumerate(lines):
        clean = re.sub(r"[^a-zA-Z ]", " ", line).lower()
        if any(alias in clean for alias in aliases.get(section, [section])):
            start = index
            break

    if start is None:
        return "Related keywords were found, but a clean standalone section could not be isolated."

    selected = []
    for line in lines[start : start + 18]:
        clean = re.sub(r"[^a-zA-Z ]", " ", line).lower().strip()
        if selected and len(clean.split()) <= 4 and any(word in clean for word in stop_words):
            break
        selected.append(line)

    snippet = "\n".join(selected)
    return snippet[:max_chars] + ("..." if len(snippet) > max_chars else "")


def calculate_score(skills: list[str], sections: dict[str, bool]) -> tuple[int, dict[str, int]]:
    points = {
        "Skills": round(min(len(skills) / 8, 1) * 35),
        "Education": 15 if sections["education"] else 0,
        "Experience": 20 if sections["experience"] else 0,
        "Projects": 15 if sections["projects"] else 0,
        "Certifications": 15 if sections["certifications"] else 0,
    }
    return min(sum(points.values()), 100), points


def keyword_set(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z][a-zA-Z+#.]{2,}\b", text.lower())
    return {word for word in words if word not in STOP_WORDS}


def calculate_job_match(resume_text: str, job_description: str) -> tuple[int | None, list[str]]:
    if not job_description.strip():
        return None, []

    resume_keywords = keyword_set(resume_text)
    jd_keywords = keyword_set(job_description)
    if not jd_keywords:
        return 0, []

    matched_keywords = sorted(resume_keywords.intersection(jd_keywords))
    match_score = round((len(matched_keywords) / len(jd_keywords)) * 100)
    return min(match_score, 100), matched_keywords[:30]


def build_feedback(
    skills: list[str],
    sections: dict[str, bool],
    words: int,
    job_match_score: int | None,
) -> tuple[list[str], list[str], list[str]]:
    strengths = []
    improvements = []
    suggestions = []
    missing_skills = [skill for skill in COMMON_SKILLS if skill not in skills]

    if skills:
        strengths.append(f"Includes {len(skills)} detected technical skill(s).")
    if sections["education"]:
        strengths.append("Education details are present.")
    if sections["experience"]:
        strengths.append("Experience details are present.")
    if sections["projects"]:
        strengths.append("Project work is mentioned.")
    if sections["certifications"]:
        strengths.append("Certifications or training are mentioned.")
    if 350 <= words <= 900:
        strengths.append("Resume length looks focused and recruiter-friendly.")
    if job_match_score is not None and job_match_score >= 70:
        strengths.append("Resume has a strong keyword match with the job description.")

    if not skills:
        improvements.append("No tracked technical skills were detected.")
        suggestions.append("Add a dedicated Skills section with relevant tools, languages, and frameworks.")
    elif len(skills) < 5:
        improvements.append("Only a limited number of tracked technical skills were detected.")
        suggestions.append("Consider adding relevant skills such as " + ", ".join(missing_skills[:6]) + ".")

    section_suggestions = {
        "skills": "Add a clearly labeled Skills section so screening tools can identify your competencies.",
        "education": "Add an Education section with degree, institution, dates, and relevant coursework.",
        "experience": "Add an Experience section with roles, companies, dates, and measurable achievements.",
        "projects": "Add a Projects section with problem statements, technologies used, and outcomes.",
        "certifications": "Add a Certifications section for verified courses, licenses, or cloud credentials.",
    }
    for section, present in sections.items():
        if not present:
            improvements.append(f"{section.title()} section appears to be missing.")
            suggestions.append(section_suggestions[section])

    if words < 250:
        improvements.append("The resume text appears short.")
        suggestions.append("Expand achievements, project impact, responsibilities, and measurable outcomes.")
    elif words > 1000:
        improvements.append("The resume may be too long for quick screening.")
        suggestions.append("Trim older or less relevant details and prioritize recent measurable impact.")

    if job_match_score is not None and job_match_score < 50:
        improvements.append("Job description keyword match is low.")
        suggestions.append("Mirror important job-description keywords where they honestly match your experience.")

    if not strengths:
        strengths.append("The resume was uploaded successfully and is ready for improvement.")
    if not suggestions:
        suggestions.append("Tailor the top skills and achievements to the role you are applying for.")

    return strengths, improvements, suggestions


def localize_feedback(items: list[str], ui_language: str) -> list[str]:
    if ui_language == "en":
        return items

    localized = []
    for item in items:
        if item.startswith("Includes ") and "detected technical skill" in item:
            count = re.search(r"\d+", item)
            localized.append(f"{count.group(0) if count else ''} సాంకేతిక నైపుణ్యాలు గుర్తించబడ్డాయి.")
        elif item == "Education details are present.":
            localized.append("విద్య వివరాలు ఉన్నాయి.")
        elif item == "Experience details are present.":
            localized.append("అనుభవ వివరాలు ఉన్నాయి.")
        elif item == "Project work is mentioned.":
            localized.append("ప్రాజెక్ట్ పని ప్రస్తావించబడింది.")
        elif item == "Certifications or training are mentioned.":
            localized.append("సర్టిఫికేషన్లు లేదా శిక్షణ ప్రస్తావించబడింది.")
        elif item == "Resume length looks focused and recruiter-friendly.":
            localized.append("రెజ్యూమ్ పరిమాణం రిక్రూటర్‌కు అనుకూలంగా ఉంది.")
        elif item == "Resume has a strong keyword match with the job description.":
            localized.append("ఉద్యోగ వివరణతో బలమైన కీవర్డ్ సరిపోలిక ఉంది.")
        elif item == "No tracked technical skills were detected.":
            localized.append("ట్రాక్ చేసే సాంకేతిక నైపుణ్యాలు గుర్తించబడలేదు.")
        elif item == "Only a limited number of tracked technical skills were detected.":
            localized.append("కొన్ని మాత్రమే సాంకేతిక నైపుణ్యాలు గుర్తించబడ్డాయి.")
        elif item.endswith("section appears to be missing."):
            section = item.replace(" section appears to be missing.", "")
            section_names = {
                "Skills": "నైపుణ్యాలు",
                "Education": "విద్య",
                "Experience": "అనుభవం",
                "Projects": "ప్రాజెక్టులు",
                "Certifications": "సర్టిఫికేషన్లు",
            }
            localized.append(f"{section_names.get(section, section)} సెక్షన్ కనిపించడం లేదు.")
        elif item == "The resume text appears short.":
            localized.append("రెజ్యూమ్ టెక్స్ట్ తక్కువగా ఉంది.")
        elif item == "The resume may be too long for quick screening.":
            localized.append("త్వరిత స్క్రీనింగ్ కోసం రెజ్యూమ్ చాలా పొడవుగా ఉండవచ్చు.")
        elif item == "Job description keyword match is low.":
            localized.append("ఉద్యోగ వివరణ కీవర్డ్ సరిపోలిక తక్కువగా ఉంది.")
        elif item == "The resume was uploaded successfully and is ready for improvement.":
            localized.append("రెజ్యూమ్ విజయవంతంగా అప్లోడ్ అయింది మరియు మెరుగుదలకు సిద్ధంగా ఉంది.")
        elif item.startswith("Consider adding relevant skills such as "):
            skills = item.replace("Consider adding relevant skills such as ", "")
            localized.append(f"సంబంధిత నైపుణ్యాలను చేర్చండి: {skills}")
        elif item == "Add a dedicated Skills section with relevant tools, languages, and frameworks.":
            localized.append("సంబంధిత టూల్స్, భాషలు, ఫ్రేమ్‌వర్క్స్‌తో ప్రత్యేక నైపుణ్యాల సెక్షన్ చేర్చండి.")
        elif item == "Add a clearly labeled Skills section so screening tools can identify your competencies.":
            localized.append("స్క్రీనింగ్ టూల్స్ సులభంగా గుర్తించేలా స్పష్టమైన నైపుణ్యాల సెక్షన్ చేర్చండి.")
        elif item == "Add an Education section with degree, institution, dates, and relevant coursework.":
            localized.append("డిగ్రీ, సంస్థ, తేదీలు మరియు సంబంధిత కోర్సులతో విద్య సెక్షన్ చేర్చండి.")
        elif item == "Add an Experience section with roles, companies, dates, and measurable achievements.":
            localized.append("పాత్రలు, కంపెనీలు, తేదీలు మరియు కొలవగల విజయాలతో అనుభవం సెక్షన్ చేర్చండి.")
        elif item == "Add a Projects section with problem statements, technologies used, and outcomes.":
            localized.append("సమస్య, ఉపయోగించిన టెక్నాలజీలు మరియు ఫలితాలతో ప్రాజెక్టుల సెక్షన్ చేర్చండి.")
        elif item == "Add a Certifications section for verified courses, licenses, or cloud credentials.":
            localized.append("కోర్సులు, లైసెన్సులు లేదా క్లౌడ్ క్రెడెన్షియల్స్ కోసం సర్టిఫికేషన్ల సెక్షన్ చేర్చండి.")
        elif item == "Expand achievements, project impact, responsibilities, and measurable outcomes.":
            localized.append("విజయాలు, ప్రాజెక్ట్ ప్రభావం, బాధ్యతలు మరియు కొలవగల ఫలితాలను విస్తరించండి.")
        elif item == "Trim older or less relevant details and prioritize recent measurable impact.":
            localized.append("పాత లేదా తక్కువ సంబంధిత వివరాలను తగ్గించి, తాజా కొలవగల ప్రభావాన్ని ముందుకు పెట్టండి.")
        elif item == "Mirror important job-description keywords where they honestly match your experience.":
            localized.append("మీ అనుభవానికి నిజంగా సరిపోయే ఉద్యోగ వివరణ కీవర్డ్స్‌ను రెజ్యూమ్‌లో చేర్చండి.")
        elif item == "Tailor the top skills and achievements to the role you are applying for.":
            localized.append("మీరు అప్లై చేస్తున్న పాత్రకు సరిపోయేలా ముఖ్య నైపుణ్యాలు మరియు విజయాలను మార్చండి.")
        else:
            localized.append(item)

    return localized


def render_pills(items: list[str], style_name: str) -> None:
    st.markdown(
        "".join(f'<span class="pill {style_name}">{item}</span>' for item in items),
        unsafe_allow_html=True,
    )


def render_score(score: int, ui_language: str) -> None:
    if score >= 80:
        label = t(ui_language, "excellent")
    elif score >= 60:
        label = t(ui_language, "good")
    elif score >= 40:
        label = t(ui_language, "needs_work")
    else:
        label = t(ui_language, "major_improvement")
    st.metric(t(ui_language, "ats_score"), f"{score}/100", label)
    st.progress(score / 100)


def main() -> None:
    configure_page()
    selected_ui_label = st.sidebar.selectbox("Website language / వెబ్‌సైట్ భాష", list(UI_LANGUAGES.keys()))
    ui_language = UI_LANGUAGES[selected_ui_label]

    st.markdown(
        f"""
        <div class="hero">
            <h1>{t(ui_language, "app_title")}</h1>
            <p>{t(ui_language, "hero")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header(t(ui_language, "upload_resume"))
        uploaded_file = st.file_uploader(t(ui_language, "choose_pdf"), type=["pdf"])
        selected_language = st.selectbox(t(ui_language, "resume_language"), list(SUPPORTED_LANGUAGES.keys()))
        st.caption(t(ui_language, "language_caption"))
        st.divider()
        st.subheader(t(ui_language, "job_match"))
        job_description = st.text_area(
            t(ui_language, "paste_jd"),
            height=180,
            placeholder=t(ui_language, "jd_placeholder"),
        )
        st.divider()
        st.subheader(t(ui_language, "scoring_weights"))
        st.write(f'{t(ui_language, "breakdown_skills")}: 35')
        st.write(f'{t(ui_language, "breakdown_education")}: 15')
        st.write(f'{t(ui_language, "breakdown_experience")}: 20')
        st.write(f'{t(ui_language, "breakdown_projects")}: 15')
        st.write(f'{t(ui_language, "breakdown_certifications")}: 15')

    if uploaded_file is None:
        st.info(t(ui_language, "upload_info"))
        st.write(t(ui_language, "checks_info"))
        return

    with st.spinner(t(ui_language, "extracting")):
        resume_text, total_pages, error = extract_text_from_pdf(uploaded_file)
    if error:
        st.error(error)
        return

    language_code, language_error = resolve_language(resume_text, selected_language)
    if language_error:
        st.error(language_error)
        return

    language_name = LANGUAGE_NAMES_BY_CODE.get(language_code, "Unknown")
    spinner_text = t(ui_language, "translating") if language_code != "en" else t(ui_language, "preparing")
    with st.spinner(spinner_text):
        analysis_text, translation_error = translate_to_english(resume_text, language_code)
    if translation_error:
        st.error(translation_error)
        return

    translated_job_description = job_description
    if job_description.strip() and language_code != "en":
        translated_job_description, jd_translation_error = translate_to_english(job_description, language_code)
        if jd_translation_error:
            st.warning(t(ui_language, "jd_translation_warning"))
            translated_job_description = job_description

    total_words = count_words(analysis_text)
    skills = detect_skills(analysis_text)
    sections = detect_sections(analysis_text)
    score, breakdown = calculate_score(skills, sections)
    job_match_score, matched_keywords = calculate_job_match(analysis_text, translated_job_description)
    strengths, improvements, suggestions = build_feedback(skills, sections, total_words, job_match_score)
    strengths = localize_feedback(strengths, ui_language)
    improvements = localize_feedback(improvements, ui_language)
    suggestions = localize_feedback(suggestions, ui_language)

    overview, score_panel = st.columns([1.25, 1])
    with overview:
        st.subheader(t(ui_language, "analysis_overview"))
        cols = st.columns(4)
        cols[0].metric(t(ui_language, "language"), language_name)
        cols[1].metric(t(ui_language, "total_words"), f"{total_words:,}")
        cols[2].metric(t(ui_language, "total_pages"), total_pages)
        cols[3].metric(t(ui_language, "skills_found"), len(skills))
    with score_panel:
        render_score(score, ui_language)

    if job_match_score is not None:
        st.subheader(t(ui_language, "job_match"))
        match_col, keyword_col = st.columns([1, 2])
        match_col.metric(t(ui_language, "job_match_score"), f"{job_match_score}/100")
        match_col.progress(job_match_score / 100)
        with keyword_col:
            if matched_keywords:
                render_pills(matched_keywords, "skill")
            else:
                st.warning(t(ui_language, "no_keyword_overlap"))

    st.subheader(t(ui_language, "score_breakdown"))
    breakdown_labels = {
        "Skills": t(ui_language, "breakdown_skills"),
        "Education": t(ui_language, "breakdown_education"),
        "Experience": t(ui_language, "breakdown_experience"),
        "Projects": t(ui_language, "breakdown_projects"),
        "Certifications": t(ui_language, "breakdown_certifications"),
    }
    for column, (label, value) in zip(st.columns(5), breakdown.items()):
        column.metric(breakdown_labels[label], value)

    st.subheader(t(ui_language, "detected_skills"))
    if skills:
        render_pills(skills, "skill")
    else:
        st.warning(t(ui_language, "no_skills"))

    left, right = st.columns(2)
    with left:
        st.subheader(t(ui_language, "education_details"))
        if sections["education"]:
            st.text_area(
                t(ui_language, "education_text"),
                extract_section_snippet(analysis_text, "education"),
                height=190,
            )
        else:
            st.warning(t(ui_language, "education_missing"))
    with right:
        st.subheader(t(ui_language, "experience_details"))
        if sections["experience"]:
            st.text_area(
                t(ui_language, "experience_text"),
                extract_section_snippet(analysis_text, "experience"),
                height=190,
            )
        else:
            st.warning(t(ui_language, "experience_missing"))

    st.subheader(t(ui_language, "strengths"))
    render_pills(strengths, "strength")

    st.subheader(t(ui_language, "improvements"))
    render_pills(improvements, "improve")

    st.subheader(t(ui_language, "suggestions"))
    for suggestion in dict.fromkeys(suggestions):
        st.write(f"- {suggestion}")

    with st.expander(t(ui_language, "extracted_text")):
        st.text_area(t(ui_language, "original_text"), resume_text, height=360)

    if language_code != "en":
        with st.expander(t(ui_language, "translated_text_expander")):
            st.text_area(t(ui_language, "translated_text"), analysis_text, height=360)


if __name__ == "__main__":
    main()
