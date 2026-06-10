import re
from io import BytesIO

import PyPDF2
import streamlit as st


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

SECTION_PATTERNS = {
    "skills": r"\b(skills|technical skills|core competencies|technologies|tools|programming languages)\b",
    "education": r"\b(education|academic background|qualification|qualifications|degree|university|college|bachelor|master|b\.tech|m\.tech|bsc|msc|mba)\b",
    "experience": r"\b(experience|work experience|employment|internship|professional experience|responsibilities|company|role)\b",
    "projects": r"\b(projects|project experience|portfolio|built|developed|implemented)\b",
    "certifications": r"\b(certifications|certification|certified|courses|licenses|licences|training)\b",
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


def build_feedback(skills: list[str], sections: dict[str, bool], words: int) -> tuple[list[str], list[str], list[str]]:
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
    st.metric("Resume Score", f"{score}/100", label)
    st.progress(score / 100)


def main() -> None:
    configure_page()

    st.markdown(
        """
        <div class="hero">
            <h1>Resume Analyzer</h1>
            <p>Upload a PDF resume to extract text, detect skills, score key sections, and receive practical improvement suggestions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Upload Resume")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        st.divider()
        st.subheader("Scoring Weights")
        st.write("Skills: 35")
        st.write("Education: 15")
        st.write("Experience: 20")
        st.write("Projects: 15")
        st.write("Certifications: 15")

    if uploaded_file is None:
        st.info("Upload a PDF resume from the sidebar to begin analysis.")
        st.write("The analyzer checks text extraction, word count, pages, skills, resume sections, strengths, and improvement areas.")
        return

    with st.spinner("Extracting resume text..."):
        resume_text, total_pages, error = extract_text_from_pdf(uploaded_file)
    if error:
        st.error(error)
        return

    total_words = count_words(resume_text)
    skills = detect_skills(resume_text)
    sections = detect_sections(resume_text)
    score, breakdown = calculate_score(skills, sections)
    strengths, improvements, suggestions = build_feedback(skills, sections, total_words)

    overview, score_panel = st.columns([1.25, 1])
    with overview:
        st.subheader("Analysis Overview")
        cols = st.columns(3)
        cols[0].metric("Total Words", f"{total_words:,}")
        cols[1].metric("Total Pages", total_pages)
        cols[2].metric("Skills Found", len(skills))
    with score_panel:
        render_score(score)

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
            st.text_area("Detected education-related text", extract_section_snippet(resume_text, "education"), height=190)
        else:
            st.warning("Education section was not detected.")
    with right:
        st.subheader("Experience Details")
        if sections["experience"]:
            st.text_area("Detected experience-related text", extract_section_snippet(resume_text, "experience"), height=190)
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
        st.text_area("Full extracted text", resume_text, height=420)


if __name__ == "__main__":
    main()
