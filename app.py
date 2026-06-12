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


def render_pills(items: list[str], style_name: str) -> None:
    st.markdown(
        "".join(f'<span class="pill {style_name}">{item}</span>' for item in items),
        unsafe_allow_html=True,
    )


def render_score(score: int) -> None:
    if score >= 80:
        label = "Excellent"
    elif score >= 60:
        label = "Good"
    elif score >= 40:
        label = "Needs work"
    else:
        label = "Needs major improvement"
    st.metric("ATS Resume Score", f"{score}/100", label)
    st.progress(score / 100)


def main() -> None:
    configure_page()

    st.markdown(
        """
        <div class="hero">
            <h1>Resume Analyzer</h1>
            <p>Upload an English or Indian-language PDF resume, translate when needed, and analyze it for ATS readiness.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Upload Resume")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        selected_language = st.selectbox("Resume language", list(SUPPORTED_LANGUAGES.keys()))
        st.caption("Auto Detect supports English, Telugu, Hindi, Tamil, Kannada, and Malayalam.")
        st.divider()
        st.subheader("Job Description Match")
        job_description = st.text_area(
            "Paste job description",
            height=180,
            placeholder="Optional: paste a job description to calculate keyword match.",
        )
        st.divider()
        st.subheader("Scoring Weights")
        st.write("Skills: 35")
        st.write("Education: 15")
        st.write("Experience: 20")
        st.write("Projects: 15")
        st.write("Certifications: 15")

    if uploaded_file is None:
        st.info("Upload a PDF resume from the sidebar to begin analysis.")
        st.write(
            "The analyzer checks extraction, translation, word count, pages, skills, sections, ATS score, job match, and improvement areas."
        )
        return

    with st.spinner("Extracting resume text..."):
        resume_text, total_pages, error = extract_text_from_pdf(uploaded_file)
    if error:
        st.error(error)
        return

    language_code, language_error = resolve_language(resume_text, selected_language)
    if language_error:
        st.error(language_error)
        return

    language_name = LANGUAGE_NAMES_BY_CODE.get(language_code, "Unknown")
    with st.spinner("Translating resume to English for analysis..." if language_code != "en" else "Preparing analysis..."):
        analysis_text, translation_error = translate_to_english(resume_text, language_code)
    if translation_error:
        st.error(translation_error)
        return

    translated_job_description = job_description
    if job_description.strip() and language_code != "en":
        translated_job_description, jd_translation_error = translate_to_english(job_description, language_code)
        if jd_translation_error:
            st.warning("Could not translate the job description. Job match will use the text as entered.")
            translated_job_description = job_description

    total_words = count_words(analysis_text)
    skills = detect_skills(analysis_text)
    sections = detect_sections(analysis_text)
    score, breakdown = calculate_score(skills, sections)
    job_match_score, matched_keywords = calculate_job_match(analysis_text, translated_job_description)
    strengths, improvements, suggestions = build_feedback(skills, sections, total_words, job_match_score)

    overview, score_panel = st.columns([1.25, 1])
    with overview:
        st.subheader("Analysis Overview")
        cols = st.columns(4)
        cols[0].metric("Language", language_name)
        cols[1].metric("Total Words", f"{total_words:,}")
        cols[2].metric("Total Pages", total_pages)
        cols[3].metric("Skills Found", len(skills))
    with score_panel:
        render_score(score)

    if job_match_score is not None:
        st.subheader("Job Description Matching")
        match_col, keyword_col = st.columns([1, 2])
        match_col.metric("Job Match Score", f"{job_match_score}/100")
        match_col.progress(job_match_score / 100)
        with keyword_col:
            if matched_keywords:
                render_pills(matched_keywords, "skill")
            else:
                st.warning("No strong keyword overlap found with the job description.")

    st.subheader("Score Breakdown")
    for column, (label, value) in zip(st.columns(5), breakdown.items()):
        column.metric(label, value)

    st.subheader("Detected Skills")
    if skills:
        render_pills(skills, "skill")
    else:
        st.warning("No common tracked skills were detected.")

    left, right = st.columns(2)
    with left:
        st.subheader("Education Details")
        if sections["education"]:
            st.text_area(
                "Detected education-related text",
                extract_section_snippet(analysis_text, "education"),
                height=190,
            )
        else:
            st.warning("Education section was not detected.")
    with right:
        st.subheader("Experience Details")
        if sections["experience"]:
            st.text_area(
                "Detected experience-related text",
                extract_section_snippet(analysis_text, "experience"),
                height=190,
            )
        else:
            st.warning("Experience section was not detected.")

    st.subheader("Strengths")
    render_pills(strengths, "strength")

    st.subheader("Areas for Improvement")
    render_pills(improvements, "improve")

    st.subheader("Resume Improvement Suggestions")
    for suggestion in dict.fromkeys(suggestions):
        st.write(f"- {suggestion}")

    with st.expander("Extracted Resume Text"):
        st.text_area("Original extracted text", resume_text, height=360)

    if language_code != "en":
        with st.expander("Translated English Text Used for Analysis"):
            st.text_area("Translated text", analysis_text, height=360)


if __name__ == "__main__":
    main()
