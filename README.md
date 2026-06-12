# Resume Analyzer

A Streamlit web application that analyzes PDF resumes, extracts text, supports multiple Indian languages, translates non-English resumes to English, calculates ATS readiness, and provides improvement suggestions.

## Features

- Upload PDF resumes
- Extract text from PDF files using PyPDF2
- Auto-detect supported resume languages
- Manually select resume language when auto-detection is uncertain
- Translate non-English resumes to English before analysis
- Keep the English analysis pipeline working for English resumes
- Count total words and PDF pages
- Detect common technical skills
- Identify Skills, Education, Experience, Projects, and Certifications sections
- Calculate ATS resume score out of 100
- Match resume content against an optional job description
- Show strengths, areas for improvement, and resume improvement suggestions
- Handle unreadable PDFs, unsupported languages, and translation errors gracefully

## Supported Languages

- English
- Telugu
- Hindi
- Tamil
- Kannada
- Malayalam

## Skill Detection

The analyzer checks for:

- Python
- Java
- C++
- SQL
- Machine Learning
- Deep Learning
- Data Science
- Artificial Intelligence
- HTML
- CSS
- JavaScript
- React
- Git
- Linux
- AWS
- Azure
- Docker
- Kubernetes

## Scoring

The ATS resume score is calculated from:

- Skills presence: 35 points
- Education section: 15 points
- Experience section: 20 points
- Projects section: 15 points
- Certifications section: 15 points

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
streamlit run app.py
```

Open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

Then:

1. Upload a PDF resume.
2. Select **Auto Detect** or choose the resume language manually.
3. Optionally paste a job description for keyword matching.
4. Review ATS score, detected skills, section analysis, strengths, and improvement suggestions.

## Notes

- Translation uses `deep-translator`, which requires an active internet connection.
- The app works best with text-based PDFs.
- Scanned image-only PDFs may not contain extractable text and may require OCR before analysis.
- Non-English resumes are translated to English first, then the same analysis pipeline is used for consistent scoring.
