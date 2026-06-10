# Resume Analyzer

A complete Streamlit web application that analyzes PDF resumes, extracts text, detects common skills, scores important sections, and provides practical improvement suggestions.

## Features

- Upload PDF resumes
- Extract resume text using PyPDF2
- Count total words and PDF pages
- Detect common technical skills
- Identify Education, Experience, Projects, Certifications, and Skills sections
- Generate a resume score out of 100
- Show strengths, areas for improvement, and resume improvement suggestions
- Clean Streamlit interface with metrics, score progress bar, and styled result sections
- Graceful error handling for unreadable or scanned PDFs

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

The resume score is calculated from:

- Skills presence: 35 points
- Education section: 15 points
- Experience section: 20 points
- Projects section: 15 points
- Certifications section: 15 points

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

Then open the local URL shown by Streamlit in your browser.

## Notes

This app works best with text-based PDF resumes. Scanned image-only PDFs may not contain extractable text and can require OCR before analysis.
