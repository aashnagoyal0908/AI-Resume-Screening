# Smart AI Resume Analyzer 🚀

A streamlined, modern AI-powered resume analyzer built with **Streamlit** and **Google Gemini AI**. This application helps job seekers, recruiters, and career coaches critically analyze resumes, evaluate Applicant Tracking System (ATS) compatibility, benchmark against specific job descriptions, and generate comprehensive, downloadable PDF reports.

---

## 🌟 Key Features

- **🤖 AI-Powered Deep Analysis**: Powered by Google's Gemini models to provide comprehensive assessments of candidate profiles, experience narratives, educational relevance, and action verbs.
- **🎯 Role Alignment & Custom Job Description Match**: Compare resumes directly against preset industry job roles or paste a specific target job description to pinpoint matching competencies and unmet requirements.
- **📊 ATS Compatibility Scoring**: Real-time gauge metrics evaluating ATS readability, keyword distribution, and formatting optimizations.
- **💡 Actionable Feedback & Skills Gap**: Highlights key resume strengths, areas for improvement, identified skills, and missing skills needed for the role.
- **📄 Professional PDF Export**: Download a styled multi-page analysis report complete with score gauges and structured recommendations.
- **📈 Real-time Analytics Dashboard**: Session-based metrics tracking analysis trends, score distribution, and model activity.

---

## 🏗️ Architecture & Project Structure

The project has been refactored for simplicity, eliminating unnecessary background services and heavy dependencies while preserving a clean, responsive UI:

```text
Smart-AI-Resume-Analyzer/
├── app.py                     # Main Streamlit application and routing logic
├── config/
│   └── job_roles.py           # Predefined job categories, roles, and required skill profiles
├── utils/
│   ├── __init__.py            # Clean package exports
│   └── ai_resume_analyzer.py  # Text extraction (PDF/DOCX), Gemini API logic, and PDF generator
├── ui_components.py           # Reusable UI card components and CSS hooks
├── style/
│   └── style.css              # Custom styling, dark mode theme, and UI responsiveness
├── requirements.txt           # Minimal runtime dependencies (12 essential libraries)
├── .env.example               # Environment variables configuration template
├── LICENSE                    # MIT License
└── README.md                  # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: Version `3.10` or higher
- **Google Gemini API Key**: A free API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd Smart-AI-Resume-Analyzer
   ```

2. **Create and activate a virtual environment (recommended)**:
   - **Windows**:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configure API Key

Create a `.env` file in the root directory by copying the example:
```bash
cp .env.example .env
```

Open `.env` in your text editor and insert your Gemini API Key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 4. Run the Application

Launch the Streamlit app:
```bash
streamlit run app.py
```

The app will open automatically in your browser at:
`http://localhost:8501`

---

## 🖥️ How to Use

1. **Navigate to Resume Analyzer**:
   - Select **🔍 RESUME ANALYZER** from the sidebar navigation.
2. **Choose Mode**:
   - **Standard Analyzer**: Rule-based skill matching against target roles.
   - **AI Analyzer** *(Recommended)*: Deep AI contextual feedback using Google Gemini.
3. **Select Role or Paste Job Description**:
   - Choose a preset **Job Category** and **Role** from the dropdowns.
   - *(Optional)* Check **"Use custom job description"** and paste a job posting to perform job-matching analysis.
4. **Upload Resume**:
   - Upload your resume file in `.pdf` or `.docx` format.
5. **Analyze & Review**:
   - Click **"🤖 Analyze with AI"** to generate instant score gauges, profile summaries, strengths, weaknesses, and skill gap analyses.
6. **Export Report**:
   - Click **"📊 Download PDF Report"** to export the structured results as a PDF.
7. **View Dashboard**:
   - Switch to **📊 DASHBOARD** in the sidebar to review overall statistics, average scores, and analysis activity.

---

## 📦 Tech Stack

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/)
- **Large Language Model**: [Google Gemini](https://ai.google.dev/) via `google-generativeai`
- **Document Processing**: `pdfplumber`, `python-docx`
- **Data & Visualizations**: `pandas`, `numpy`, `plotly`
- **PDF Generation**: `reportlab`
- **Styling**: Custom CSS and `streamlit-lottie` animations

---

## 🔒 Privacy & Security

- **Local Execution**: All document text extraction and score calculations run locally on your system.
- **Direct API Communication**: Resume text is sent directly to Google's Gemini API over secure HTTPS and is not stored or shared with third-party tracking services.
- **Environment Safety**: API keys are loaded via `python-dotenv` from `.env`, keeping credentials isolated from version control.

---

## 📄 License

This project is open-source and distributed under the [MIT License](LICENSE).
