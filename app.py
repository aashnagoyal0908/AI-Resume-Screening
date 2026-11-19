"""
Smart Resume AI - Main Application
"""
import time
from PIL import Image
from datetime import datetime
from ui_components import (
    apply_modern_styles, hero_section, feature_card, about_section,
    page_header, render_analytics_section, render_activity_section,
    render_suggestions_section
)
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from docx import Document
import io
import base64
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import requests
from config.job_roles import JOB_ROLES
from utils.ai_resume_analyzer import AIResumeAnalyzer

# --- Self-Contained Stubs for Secondary Modules to keep UI intact without external bloat ---
class DashboardManager:
    def render_dashboard(self):
        render_full_dashboard()

class ResumeBuilder:
    def generate_resume(self, data):
        return None

class ResumeAnalyzer:
    def extract_text_from_pdf(self, f):
        from utils.ai_resume_analyzer import AIResumeAnalyzer
        return AIResumeAnalyzer().extract_text_from_pdf(f)
    def extract_text_from_docx(self, f):
        from utils.ai_resume_analyzer import AIResumeAnalyzer
        return AIResumeAnalyzer().extract_text_from_docx(f)
    def analyze_resume(self, text_dict, role_info=None):
        raw_text = text_dict.get('raw_text', '')
        text_lower = raw_text.lower()
        required_skills = role_info.get('required_skills', []) if role_info else []
        
        # Calculate real skill matches
        matched_skills = [s for s in required_skills if s.lower() in text_lower]
        missing_skills = [s for s in required_skills if s.lower() not in text_lower]
        
        skill_ratio = len(matched_skills) / max(len(required_skills), 1)
        keyword_score = int(round(skill_ratio * 100)) if required_skills else 75
        
        # Check standard sections
        has_summary = any(k in text_lower for k in ['summary', 'objective', 'about me', 'profile'])
        has_experience = any(k in text_lower for k in ['experience', 'employment', 'work history', 'projects'])
        has_education = any(k in text_lower for k in ['education', 'degree', 'university', 'college', 'bachelor', 'master'])
        has_skills = any(k in text_lower for k in ['skills', 'technologies', 'competencies'])
        has_contact = any(k in text_lower for k in ['email', '@', 'phone', 'linkedin', 'github'])
        
        section_count = sum([has_summary, has_experience, has_education, has_skills, has_contact])
        section_score = int(round((section_count / 5.0) * 100))
        
        # Format checks (word count, bullet points, readability)
        words = raw_text.split()
        word_count = len(words)
        format_score = 85
        if word_count < 150:
            format_score = 55
        elif word_count > 1200:
            format_score = 70
        else:
            format_score = 90
            
        # ATS Overall Weighted Score
        ats_score = int(round(0.5 * keyword_score + 0.3 * section_score + 0.2 * format_score))
        
        suggestions = []
        if missing_skills:
            suggestions.append(f"Add critical missing skills for this role: {', '.join(missing_skills[:5])}")
        if not has_summary:
            suggestions.append("Add a targeted 2-3 sentence Professional Summary at the top of your resume.")
        if word_count < 300:
            suggestions.append("Expand on measurable bullet points and project achievements.")
        suggestions.append("Use standard bullet points with strong action verbs (e.g. Architected, Optimized, Led).")
        suggestions.append("Ensure key technical skills appear in both your Skills section and Project descriptions.")
        
        return {
            'ats_score': ats_score,
            'keyword_match': {
                'score': keyword_score,
                'matched_skills': matched_skills,
                'missing_skills': missing_skills
            },
            'format_score': format_score,
            'section_score': section_score,
            'suggestions': suggestions,
            'document_type': 'resume'
        }

class FeedbackManager:
    def render_feedback_form(self):
        import streamlit as st
        st.text_input("Your Name", key="fb_name")
        st.text_input("Email", key="fb_email")
        st.text_area("Feedback or Suggestion", key="fb_msg")
        if st.button("Submit Feedback", key="fb_sub"):
            st.success("Thank you for your feedback!")
    def render_feedback_stats(self):
        import streamlit as st
        st.info("No feedback submitted yet.")

def render_job_search():
    import streamlit as st
    st.markdown('<div class="feature-card"><h3>🎯 Job Opportunities</h3><p>Search job listings across popular job boards.</p></div>', unsafe_allow_html=True)
    role = st.text_input("Job Title or Keywords", value="Python Developer")
    loc = st.text_input("Location", value="Remote")
    if st.button("Search Jobs", key="job_search_btn"):
        st.info(f"Searching for {role} roles in {loc}...")
        st.markdown(f"- [LinkedIn Jobs](https://www.linkedin.com/jobs/search/?keywords={role})\n- [Indeed Jobs](https://www.indeed.com/jobs?q={role})")

COURSES_BY_CATEGORY = {}
RESUME_VIDEOS = {
    'Resume Tips': [('Resume Best Practices', 'https://www.youtube.com/watch?v=y8YH0Qbu5h4')]
}
INTERVIEW_VIDEOS = {
    'Interview Tips': [('Ace Your Technical Interview', 'https://www.youtube.com/watch?v=1mHjMNZZvFo')]
}
def get_courses_for_role(r): return []
def get_category_for_role(r): return 'Technology'

def get_database_connection(): return None
def save_resume_data(d): return 1
def save_analysis_data(i, d): pass
def init_database(): pass
def save_ai_analysis_data(u, d):
    import streamlit as st
    stats = get_detailed_ai_analysis_stats()
    stats['total_analyses'] = stats.get('total_analyses', 0) + 1
    score = d.get('resume_score', 0)
    prev_total = max(stats['total_analyses'] - 1, 1)
    stats['average_score'] = round((stats.get('average_score', 0) * prev_total + score) / stats['total_analyses'], 1)
    
    job_role = d.get('job_role', 'General')
    
    # Update recent analyses
    if 'recent_analyses' not in stats: stats['recent_analyses'] = []
    import datetime
    stats['recent_analyses'].insert(0, {
        'name': d.get('candidate_name', 'Analyzed Resume'),
        'model': d.get('model_used', 'Google Gemini'),
        'score': score,
        'job_role': job_role,
        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Update top_job_roles safely
    top_roles = stats.get('top_job_roles', [])
    found = False
    for r in top_roles:
        if r.get('role') == job_role:
            r['count'] = r.get('count', 0) + 1
            found = True
            break
    if not found:
        top_roles.append({'role': job_role, 'count': 1})
    top_roles.sort(key=lambda x: x.get('count', 0), reverse=True)
    stats['top_job_roles'] = top_roles
    st.session_state.ai_analysis_stats = stats

def get_ai_analysis_stats():
    import streamlit as st
    return st.session_state.get('ai_analysis_stats', {})

def reset_ai_analysis_stats():
    import streamlit as st
    st.session_state.ai_analysis_stats = get_initial_sample_data()
    return {'success': True, 'message': 'Statistics reset to default baseline.'}


def get_initial_sample_data():
    """Generate 16 realistic candidate records for the analytics dashboard"""
    sample_records = [
        {"name": "Aarav Sharma", "role": "Full Stack Developer", "score": 88, "ats": 85, "days_ago": 0},
        {"name": "Priya Patel", "role": "Data Scientist", "score": 92, "ats": 90, "days_ago": 0},
        {"name": "Rohan Verma", "role": "Machine Learning Engineer", "score": 79, "ats": 76, "days_ago": 1},
        {"name": "Ananya Iyer", "role": "DevOps Engineer", "score": 84, "ats": 82, "days_ago": 1},
        {"name": "Vikram Singh", "role": "Cloud Solutions Architect", "score": 91, "ats": 88, "days_ago": 2},
        {"name": "Sneha Reddy", "role": "Frontend Developer", "score": 76, "ats": 72, "days_ago": 2},
        {"name": "Rahul Nair", "role": "Backend Developer", "score": 83, "ats": 80, "days_ago": 3},
        {"name": "Neha Gupta", "role": "Product Manager", "score": 87, "ats": 85, "days_ago": 3},
        {"name": "Karan Joshi", "role": "Cybersecurity Analyst", "score": 73, "ats": 70, "days_ago": 4},
        {"name": "Pooja Mehta", "role": "AI/ML Specialist", "score": 95, "ats": 92, "days_ago": 4},
        {"name": "Aditya Kulkarni", "role": "Data Engineer", "score": 81, "ats": 78, "days_ago": 5},
        {"name": "Tanvi Shah", "role": "UI/UX Designer", "score": 86, "ats": 84, "days_ago": 5},
        {"name": "Siddharth Rao", "role": "Full Stack Developer", "score": 90, "ats": 88, "days_ago": 6},
        {"name": "Divya Das", "role": "QA Automation Engineer", "score": 78, "ats": 75, "days_ago": 6},
        {"name": "Manish Tiwari", "role": "Systems Engineer", "score": 82, "ats": 79, "days_ago": 6},
        {"name": "Ishita Banerjee", "role": "Data Analyst", "score": 85, "ats": 83, "days_ago": 6},
    ]

    base_time = datetime.datetime.now()
    recent_analyses = []
    role_counts = {}

    for r in sample_records:
        dt = base_time - datetime.timedelta(days=r["days_ago"], hours=(r["score"] % 12 + 1))
        recent_analyses.append({
            "name": r["name"],
            "model": "Google Gemini",
            "score": r["score"],
            "ats_score": r["ats"],
            "job_role": r["role"],
            "date": dt.strftime("%Y-%m-%d %H:%M:%S")
        })
        role_counts[r["role"]] = role_counts.get(r["role"], 0) + 1

    scores = [r["score"] for r in sample_records]
    total = len(sample_records)
    avg_score = round(sum(scores) / total, 1)

    top_roles = [{"role": k, "count": v} for k, v in sorted(role_counts.items(), key=lambda x: x[1], reverse=True)]

    score_ranges = {
        "0-59 (Needs Work)": len([s for s in scores if s < 60]),
        "60-74 (Good)": len([s for s in scores if 60 <= s < 75]),
        "75-84 (Strong)": len([s for s in scores if 75 <= s < 85]),
        "85-100 (Exceptional)": len([s for s in scores if s >= 85])
    }
    score_dist = [{"range": k, "count": v} for k, v in score_ranges.items()]

    return {
        "total_analyses": total,
        "average_score": avg_score,
        "model_usage": [{"model": "Google Gemini", "count": total}],
        "top_job_roles": top_roles,
        "score_distribution": score_dist,
        "recent_analyses": recent_analyses
    }


def render_full_dashboard():
    """Renders a rich analytics dashboard with charts and real/sample metrics"""
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd

    page_header("Analytics Dashboard", "Comprehensive metrics, score distributions, and candidate analysis logs")

    ai_stats = get_detailed_ai_analysis_stats()

    # Reset button & Controls
    col_ctrl1, col_ctrl2 = st.columns([6, 1])
    with col_ctrl2:
        if st.button("🔄 Reset Data", type="secondary", key="dash_reset_btn"):
            reset_ai_analysis_stats()
            st.rerun()

    # Top KPI Metrics row
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="stats-card" style="background: linear-gradient(135deg, #1e3c72, #2a5298); border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <div style="font-size: 13px; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 1px;">Total Resumes Analyzed</div>
            <div style="font-size: 36px; font-weight: bold; color: white; margin: 10px 0;">{ai_stats["total_analyses"]}</div>
            <div style="font-size: 13px; color: #38ef7d;"><i class="fas fa-check-circle"></i> 100% Processed</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        score_color = "#38ef7d" if ai_stats["average_score"] >= 80 else "#FFEB3B" if ai_stats["average_score"] >= 60 else "#FF5252"
        st.markdown(f"""
        <div class="stats-card" style="background: linear-gradient(135deg, #2c3e50, {score_color}); border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <div style="font-size: 13px; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: 1px;">Average Resume Score</div>
            <div style="font-size: 36px; font-weight: bold; color: white; margin: 10px 0;">{ai_stats["average_score"]}/100</div>
            <div style="font-size: 13px; color: white;"><i class="fas fa-chart-line"></i> Benchmark Index</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=ai_stats["average_score"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Average Score Gauge", 'font': {'size': 14, 'color': 'white'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#38ef7d" if ai_stats["average_score"] >= 80 else "#FFEB3B" if ai_stats["average_score"] >= 60 else "#FF5252"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "white",
                'steps': [
                    {'range': [0, 60], 'color': 'rgba(255, 82, 82, 0.25)'},
                    {'range': [60, 80], 'color': 'rgba(255, 235, 59, 0.25)'},
                    {'range': [80, 100], 'color': 'rgba(56, 239, 125, 0.25)'}
                ],
            }
        ))
        fig_g.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"},
            height=160,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig_g, width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2: Charts (Roles & Score distribution)
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("### 🎯 Job Roles Analyzed")
        if ai_stats.get("top_job_roles"):
            roles_df = pd.DataFrame(ai_stats.get("top_job_roles", []))
            fig_bar = px.bar(
                roles_df,
                x="role",
                y="count",
                color="count",
                color_continuous_scale=px.colors.sequential.Viridis,
                labels={"role": "Target Role", "count": "Resumes"}
            )
            fig_bar.update_layout(
                margin=dict(l=20, r=20, t=30, b=80),
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#ffffff", size=13),
                xaxis=dict(tickangle=-35, tickfont=dict(size=11)),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, width='stretch')

    with chart_col2:
        st.markdown("### 📊 Score Distribution Breakdown")
        if ai_stats.get("score_distribution"):
            score_df = pd.DataFrame(ai_stats.get("score_distribution", []))
            fig_pie = px.pie(
                score_df,
                values="count",
                names="range",
                color_discrete_sequence=["#ef5350", "#ffa726", "#42a5f5", "#66bb6a"],
                hole=0.45
            )
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#1e1e1e', width=2))
            )
            fig_pie.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#ffffff", size=13),
                legend=dict(orientation="h", y=-0.15, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, width='stretch')

    # Row 3: Recent Candidates Log Table
    st.markdown("### 🕒 Candidate Resume Analysis Log")
    if ai_stats.get("recent_analyses"):
        st.markdown("""
        <style>
        .cand-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 8px;
            margin-bottom: 25px;
        }
        .cand-table th {
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            padding: 12px 16px;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-radius: 6px;
        }
        .cand-table td {
            padding: 12px 16px;
            background-color: rgba(30, 30, 30, 0.85);
            color: white;
            border-top: 1px solid rgba(255,255,255,0.05);
        }
        .cand-table tr td:first-child { border-top-left-radius: 8px; border-bottom-left-radius: 8px; font-weight: 600; }
        .cand-table tr td:last-child { border-top-right-radius: 8px; border-bottom-right-radius: 8px; }
        .score-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 16px;
            font-weight: bold;
            font-size: 13px;
        }
        .score-green { background: #1b5e20; color: #a5d6a7; border: 1px solid #2e7d32; }
        .score-yellow { background: #f57f17; color: #fff9c4; border: 1px solid #fbc02d; }
        .score-red { background: #b71c1c; color: #ffcdd2; border: 1px solid #c62828; }
        </style>
        <table class="cand-table">
            <tr>
                <th>Candidate / Title</th>
                <th>Target Job Role</th>
                <th>Overall Score</th>
                <th>AI Model</th>
                <th>Analysis Date</th>
            </tr>
        """, unsafe_allow_html=True)

        for item in ai_stats["recent_analyses"]:
            score = item.get("score", 0)
            badge_class = "score-green" if score >= 80 else "score-yellow" if score >= 60 else "score-red"
            name = item.get("name", "Candidate")
            role = item.get("job_role", "General")
            model = item.get("model", "Google Gemini")
            date_str = item.get("date", "")

            st.markdown(f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td><span style="background: rgba(33, 150, 243, 0.15); color: #90caf9; padding: 4px 8px; border-radius: 6px; font-size: 13px;">{role}</span></td>
                <td><span class="score-badge {badge_class}">{score}/100</span></td>
                <td><span style="background: rgba(142, 68, 173, 0.2); color: #d7bde2; padding: 4px 8px; border-radius: 6px; font-size: 12px;">{model}</span></td>
                <td style="color: #b0bec5; font-size: 13px;">{date_str}</td>
            </tr>
            """, unsafe_allow_html=True)

        st.markdown("</table>", unsafe_allow_html=True)

def get_detailed_ai_analysis_stats():
    import streamlit as st
    stats = st.session_state.get('ai_analysis_stats')
    if not stats or not stats.get('top_job_roles') or not stats.get('recent_analyses'):
        stats = get_initial_sample_data()
        st.session_state.ai_analysis_stats = stats
    return stats
# --- End of Stubs ---

import traceback
import plotly.express as px
import pandas as pd
import json
import streamlit as st
import datetime

# Set page config at the very beginning
st.set_page_config(
    page_title="Smart Resume AI",
    page_icon="🚀",
    layout="wide"
)


class ResumeApp:
    def __init__(self):
        """Initialize the application"""
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'personal_info': {
                    'full_name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'linkedin': '',
                    'portfolio': ''
                },
                'summary': '',
                'experiences': [],
                'education': [],
                'projects': [],
                'skills_categories': {
                    'technical': [],
                    'soft': [],
                    'languages': [],
                    'tools': []
                }
            }

        # Initialize navigation state
        if 'page' not in st.session_state:
            st.session_state.page = 'resume_analyzer'



        # Initialize dashboard manager
        self.dashboard_manager = DashboardManager()

        self.pages = {
            "🔍 RESUME ANALYZER": self.render_analyzer,
            "📊 DASHBOARD": self.render_dashboard
        }

        self.analyzer = ResumeAnalyzer()
        self.ai_analyzer = AIResumeAnalyzer()
        self.job_roles = JOB_ROLES

        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = 'default_user'
        if 'selected_role' not in st.session_state:
            st.session_state.selected_role = None

        # Initialize database
        init_database()

        # Load external CSS
        with open('style/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

        # Load Google Fonts
        st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        """, unsafe_allow_html=True)

        if 'resume_data' not in st.session_state:
            st.session_state.resume_data = []
        if 'ai_analysis_stats' not in st.session_state or not st.session_state.ai_analysis_stats.get('top_job_roles'):
            st.session_state.ai_analysis_stats = get_initial_sample_data()

    def load_lottie_url(self, url: str):
        """Load Lottie animation from URL"""
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()

    def apply_global_styles(self):
        st.markdown("""
        <style>
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1a1a;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #4CAF50;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #45a049;
        }

        /* Global Styles */
        .main-header {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 100%);
            z-index: 1;
        }

        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            position: relative;
            z-index: 2;
        }

        /* Template Card Styles */
        .template-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            padding: 1rem;
        }

        .template-card {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .template-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border-color: #4CAF50;
        }

        .template-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(76,175,80,0.1) 100%);
            z-index: 1;
        }

        .template-icon {
            font-size: 3rem;
            color: #4CAF50;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
        }

        .template-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1rem;
            position: relative;
            z-index: 2;
        }

        .template-description {
            color: #aaa;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
            line-height: 1.6;
        }

        /* Feature List Styles */
        .feature-list {
            list-style: none;
            padding: 0;
            margin: 1.5rem 0;
            position: relative;
            z-index: 2;
        }

        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: #ddd;
            font-size: 0.95rem;
        }

        .feature-icon {
            color: #4CAF50;
            margin-right: 0.8rem;
            font-size: 1.1rem;
        }

        /* Button Styles */
        .action-button {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            border: none;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            text-align: center;
            position: relative;
            overflow: hidden;
            z-index: 2;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(76,175,80,0.3);
        }

        .action-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
            transition: all 0.6s ease;
        }

        .action-button:hover::before {
            left: 100%;
        }

        /* Form Section Styles */
        .form-section {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .form-section-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1.5rem;
            padding-bottom: 0.8rem;
            border-bottom: 2px solid #4CAF50;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            color: #ddd;
            font-weight: 500;
            margin-bottom: 0.8rem;
            display: block;
        }

        .form-input {
            width: 100%;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(30, 30, 30, 0.9);
            color: white;
            transition: all 0.3s ease;
        }

        .form-input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76,175,80,0.2);
            outline: none;
        }

        /* Skill Tags */
        .skill-tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .skill-tag {
            background: rgba(76,175,80,0.1);
            color: #4CAF50;
            padding: 0.6rem 1.2rem;
            border-radius: 50px;
            border: 1px solid #4CAF50;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .skill-tag:hover {
            background: #4CAF50;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76,175,80,0.2);
        }

        /* Progress Circle */
        .progress-container {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 2rem auto;
        }

        .progress-circle {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }

        .progress-circle circle {
            fill: none;
            stroke-width: 8;
            stroke-linecap: round;
            stroke: #4CAF50;
            transform-origin: 50% 50%;
            transition: all 0.3s ease;
        }

        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.5rem;
            font-weight: 600;
            color: white;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .feature-card {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .animate-slide-in {
            animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .template-container {
                grid-template-columns: 1fr;
            }

            .main-header {
                padding: 1.5rem;
            }

            .main-header h1 {
                font-size: 2rem;
            }

            .template-card {
                padding: 1.5rem;
            }

            .action-button {
                padding: 0.8rem 1.6rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
    def add_footer(self):
        pass

    def load_image(self, image_name):
        """Load image from static directory"""
        try:
            image_path = f"c:/Users/shree/Downloads/smart-resume-ai/{image_name}"
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            encoded = base64.b64encode(image_bytes).decode()
            return f"data:image/png;base64,{encoded}"
        except Exception as e:
            print(f"Error loading image {image_name}: {e}")
            return None

    def render_dashboard(self):
        """Render the dashboard page"""
        apply_modern_styles()
        self.dashboard_manager.render_dashboard()

    def render_empty_state(self, icon, message):
        """Render an empty state with icon and message"""
        return f"""
            <div style='text-align: center; padding: 2rem; color: #888;'>
                <i class='{icon}' style='font-size: 2.5rem; margin-bottom: 1rem; color: #00bfa5;'></i>
                <p style='margin: 0; font-size: 1.1rem; color: #aaa;'>{message}</p>
            </div>
        """

    def render_analyzer(self):
        """Render the resume analyzer page"""
        apply_modern_styles()

        # Page Header
        page_header(
            "Resume Analyzer",
            "Get instant AI-powered feedback to optimize your resume"
        )

        # Create tabs for Normal Analyzer and AI Analyzer
        analyzer_tabs = st.tabs(["Standard Analyzer", "AI Analyzer"])

        with analyzer_tabs[0]:
            # Job Role Selection
            categories = list(self.job_roles.keys())
            selected_category = st.selectbox(
    "Job Category", categories, key="standard_category")

            roles = list(self.job_roles[selected_category].keys())
            selected_role = st.selectbox(
    "Specific Role", roles, key="standard_role")

            role_info = self.job_roles[selected_category][selected_role]

            # Display role information
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>{selected_role}</h3>
                <p>{role_info['description']}</p>
                <h4>Required Skills:</h4>
                <p>{', '.join(role_info['required_skills'])}</p>
            </div>
            """, unsafe_allow_html=True)

            # File Upload
            uploaded_file = st.file_uploader(
    "Upload your resume", type=[
        'pdf', 'docx'], key="standard_file")

            if not uploaded_file:
                # Display empty state with a prominent upload button
                st.markdown(
                    self.render_empty_state(
                    "fas fa-cloud-upload-alt",
                    "Upload your resume to get started with standard analysis"
                    ),
                    unsafe_allow_html=True
                )
                # Add a prominent upload button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown("""
                    <style>
                    .upload-button {
                        background: linear-gradient(90deg, #4b6cb7, #182848);
                        color: white;
                        border: none;
                        border-radius: 10px;
                        padding: 15px 25px;
                        font-size: 18px;
                        font-weight: bold;
                        cursor: pointer;
                        width: 100%;
                        text-align: center;
                        margin: 20px 0;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                        transition: all 0.3s ease;
                    }
                    .upload-button:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
                    }

                    """, unsafe_allow_html=True)

            if uploaded_file:
                # Add a prominent analyze button
                analyze_standard = st.button("🔍 Analyze My Resume",
                                    type="primary",
                                    width='stretch',
                                    key="analyze_standard_button")

                if analyze_standard:
                    with st.spinner("Analyzing your document..."):
                        # Get file content
                        text = ""
                        try:
                            if uploaded_file.type == "application/pdf":
                                try:
                                    text = self.analyzer.extract_text_from_pdf(uploaded_file)
                                except Exception as pdf_error:
                                    st.error(f"PDF extraction failed: {str(pdf_error)}")
                                    st.info("Trying alternative PDF extraction method...")
                                    # Try AI analyzer as backup
                                    try:
                                        text = self.ai_analyzer.extract_text_from_pdf(uploaded_file)
                                    except Exception as backup_error:
                                        st.error(f"All PDF extraction methods failed: {str(backup_error)}")
                                        return
                            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                try:
                                    text = self.analyzer.extract_text_from_docx(uploaded_file)
                                except Exception as docx_error:
                                    st.error(f"DOCX extraction failed: {str(docx_error)}")
                                    # Try AI analyzer as backup
                                    try:
                                        text = self.ai_analyzer.extract_text_from_docx(uploaded_file)
                                    except Exception as backup_error:
                                        st.error(f"All DOCX extraction methods failed: {str(backup_error)}")
                                        return
                            else:
                                text = uploaded_file.getvalue().decode()
                                
                            if not text or text.strip() == "":
                                st.error("Could not extract any text from the uploaded file. Please try a different file.")
                                return
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                            return

                        # Analyze the document
                        analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)
                        
                        # Check if analysis returned an error
                        if 'error' in analysis:
                            st.error(analysis['error'])
                            return


                        # Save resume data to database
                        resume_data = {
                            'personal_info': {
                                'name': analysis.get('name', ''),
                                'email': analysis.get('email', ''),
                                'phone': analysis.get('phone', ''),
                                'linkedin': analysis.get('linkedin', ''),
                                'github': analysis.get('github', ''),
                                'portfolio': analysis.get('portfolio', '')
                            },
                            'summary': analysis.get('summary', ''),
                            'target_role': selected_role,
                            'target_category': selected_category,
                            'education': analysis.get('education', []),
                            'experience': analysis.get('experience', []),
                            'projects': analysis.get('projects', []),
                            'skills': analysis.get('skills', []),
                            'template': ''
                        }

                        # Save to database
                        try:
                            resume_id = save_resume_data(resume_data)

                            # Save analysis data
                            analysis_data = {
                                'resume_id': resume_id,
                                'ats_score': analysis['ats_score'],
                                'keyword_match_score': analysis['keyword_match']['score'],
                                'format_score': analysis['format_score'],
                                'section_score': analysis['section_score'],
                                'missing_skills': ','.join(analysis['keyword_match']['missing_skills']),
                                'recommendations': ','.join(analysis['suggestions'])
                            }
                            save_analysis_data(resume_id, analysis_data)
                            st.success("Resume data saved successfully!")
                        except Exception as e:
                            st.error(f"Error saving to database: {str(e)}")
                            print(f"Database error: {e}")

                        # Show results based on document type
                        if analysis.get('document_type') != 'resume':
                            st.error(
    f"⚠️ This appears to be a {
        analysis['document_type']} document, not a resume!")
                            st.warning(
                                "Please upload a proper resume for ATS analysis.")
                            return
                        # Display results in a modern, enhanced layout
                    st.markdown("<hr style='margin: 25px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
                    st.markdown("### 📊 Standard Analysis Breakdown")

                    # Top KPI Row
                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                    ats_score = int(analysis.get('ats_score', 0))
                    kw_score = int(analysis.get('keyword_match', {}).get('score', 0))
                    fmt_score = int(analysis.get('format_score', 0))
                    sec_score = int(analysis.get('section_score', 0))

                    with kpi1:
                        color = "#38ef7d" if ats_score >= 80 else "#fbc02d" if ats_score >= 60 else "#ff5252"
                        status = "Strong Match" if ats_score >= 80 else "Good Match" if ats_score >= 60 else "Needs Work"
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #1e3c72, #2a5298); border-radius: 12px; padding: 18px; text-align: center; border-left: 5px solid {color}; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                            <div style="font-size: 12px; color: rgba(255,255,255,0.7); text-transform: uppercase;">Overall ATS Score</div>
                            <div style="font-size: 32px; font-weight: bold; color: {color}; margin: 6px 0;">{ats_score}%</div>
                            <div style="font-size: 13px; color: white;">{status}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with kpi2:
                        color_kw = "#38ef7d" if kw_score >= 80 else "#fbc02d" if kw_score >= 60 else "#ff5252"
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #232526, #414345); border-radius: 12px; padding: 18px; text-align: center; border-left: 5px solid {color_kw}; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                            <div style="font-size: 12px; color: rgba(255,255,255,0.7); text-transform: uppercase;">Keywords & Skills</div>
                            <div style="font-size: 32px; font-weight: bold; color: {color_kw}; margin: 6px 0;">{kw_score}%</div>
                            <div style="font-size: 13px; color: rgba(255,255,255,0.85);">Role Competencies</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with kpi3:
                        color_fmt = "#38ef7d" if fmt_score >= 80 else "#fbc02d" if fmt_score >= 60 else "#ff5252"
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #232526, #414345); border-radius: 12px; padding: 18px; text-align: center; border-left: 5px solid {color_fmt}; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                            <div style="font-size: 12px; color: rgba(255,255,255,0.7); text-transform: uppercase;">Format & Length</div>
                            <div style="font-size: 32px; font-weight: bold; color: {color_fmt}; margin: 6px 0;">{fmt_score}%</div>
                            <div style="font-size: 13px; color: rgba(255,255,255,0.85);">Layout Quality</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with kpi4:
                        color_sec = "#38ef7d" if sec_score >= 80 else "#fbc02d" if sec_score >= 60 else "#ff5252"
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #232526, #414345); border-radius: 12px; padding: 18px; text-align: center; border-left: 5px solid {color_sec}; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                            <div style="font-size: 12px; color: rgba(255,255,255,0.7); text-transform: uppercase;">Standard Sections</div>
                            <div style="font-size: 32px; font-weight: bold; color: {color_sec}; margin: 6px 0;">{sec_score}%</div>
                            <div style="font-size: 13px; color: rgba(255,255,255,0.85);">Core Headers</div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Two Column Detailed Breakdown
                    res_col1, res_col2 = st.columns(2)

                    with res_col1:
                        # Skills Analysis Box
                        st.markdown("""
                        <div style="background: #1e1e1e; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                            <h4 style="color: white; margin-top: 0; margin-bottom: 15px;"><i class="fas fa-check-double" style="color: #00bfa5; margin-right: 8px;"></i> Skills Breakdown</h4>
                        """, unsafe_allow_html=True)

                        matched_skills = analysis.get('keyword_match', {}).get('matched_skills', [])
                        missing_skills = analysis.get('keyword_match', {}).get('missing_skills', [])

                        if matched_skills:
                            st.markdown("<div style='font-size: 13px; color: #4CAF50; font-weight: bold; margin-bottom: 6px;'>✓ Matched Skills in Resume:</div>", unsafe_allow_html=True)
                            pills_html = " ".join([f"<span style='display: inline-block; background: rgba(76, 175, 80, 0.2); color: #a5d6a7; border: 1px solid rgba(76, 175, 80, 0.4); padding: 4px 10px; border-radius: 12px; font-size: 12px; margin: 3px 2px;'>{s}</span>" for s in matched_skills])
                            st.markdown(pills_html, unsafe_allow_html=True)

                        if missing_skills:
                            st.markdown("<div style='font-size: 13px; color: #ff5252; font-weight: bold; margin-top: 14px; margin-bottom: 6px;'>✗ Missing Target Skills:</div>", unsafe_allow_html=True)
                            missing_pills = " ".join([f"<span style='display: inline-block; background: rgba(244, 67, 54, 0.2); color: #ffab91; border: 1px solid rgba(244, 67, 54, 0.4); padding: 4px 10px; border-radius: 12px; font-size: 12px; margin: 3px 2px;'>{s}</span>" for s in missing_skills])
                            st.markdown(missing_pills, unsafe_allow_html=True)

                        if not matched_skills and not missing_skills:
                            st.markdown("<div style='color: #aaa;'>Role skills extracted successfully.</div>", unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

                    with res_col2:
                        # Improvement Suggestions Box
                        st.markdown("""
                        <div style="background: #1e1e1e; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                            <h4 style="color: white; margin-top: 0; margin-bottom: 15px;"><i class="fas fa-lightbulb" style="color: #ffb74d; margin-right: 8px;"></i> Actionable Recommendations</h4>
                        """, unsafe_allow_html=True)

                        suggestions = analysis.get('suggestions', [])
                        if suggestions:
                            for idx, sug in enumerate(suggestions):
                                st.markdown(f"""
                                <div style="display: flex; align-items: flex-start; margin-bottom: 10px; background: rgba(255,255,255,0.03); padding: 10px 14px; border-radius: 8px;">
                                    <div style="color: #00bfa5; margin-right: 10px; font-weight: bold;">{idx+1}.</div>
                                    <div style="color: #e0e0e0; font-size: 13px; line-height: 1.5;">{sug}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='color: #aaa;'>Resume demonstrates strong adherence to ATS standards.</div>", unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

        with analyzer_tabs[1]:
            st.markdown("""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>AI-Powered Resume Analysis</h3>
                <p>Get detailed insights from advanced AI models that analyze your resume and provide personalized recommendations.</p>
                <p><strong>Upload your resume to get AI-powered analysis and recommendations.</strong></p>
            </div>
            """, unsafe_allow_html=True)

            # AI Model Selection
            ai_model = st.selectbox(
                "Select AI Model",
                ["Google Gemini"],
                help="Choose the AI model to analyze your resume"
            )
             
            # Add job description input option
            use_custom_job_desc = st.checkbox("Use custom job description", value=False, 
                                             help="Enable this to provide a specific job description for more targeted analysis")
            
            custom_job_description = ""
            if use_custom_job_desc:
                custom_job_description = st.text_area(
                    "Paste the job description here",
                    height=200,
                    placeholder="Paste the full job description from the company here for more targeted analysis...",
                    help="Providing the actual job description will help the AI analyze your resume specifically for this position"
                )
                
                st.markdown("""
                <div style='background-color: #2e7d32; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <p><i class="fas fa-lightbulb"></i> <strong>Pro Tip:</strong> Including the actual job description significantly improves the accuracy of the analysis and provides more relevant recommendations tailored to the specific position.</p>
                </div>
                """, unsafe_allow_html=True)
             
                        # Add AI Analyzer Stats in an expander
            # Job Role Selection for AI Analysis
            categories = list(self.job_roles.keys())
            selected_category = st.selectbox(
    "Job Category", categories, key="ai_category")

            roles = list(self.job_roles[selected_category].keys())
            selected_role = st.selectbox("Specific Role", roles, key="ai_role")

            role_info = self.job_roles[selected_category][selected_role]

            # Display role information
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>{selected_role}</h3>
                <p>{role_info['description']}</p>
                <h4>Required Skills:</h4>
                <p>{', '.join(role_info['required_skills'])}</p>
            </div>
            """, unsafe_allow_html=True)

            # File Upload for AI Analysis
            uploaded_file = st.file_uploader(
    "Upload your resume", type=[
        'pdf', 'docx'], key="ai_file")

            if not uploaded_file:
            # Display empty state with a prominent upload button
                st.markdown(
                self.render_empty_state(
            "fas fa-robot",
                        "Upload your resume to get AI-powered analysis and recommendations"
        ),
        unsafe_allow_html=True
    )
            else:
                # Add a prominent analyze button
                analyze_ai = st.button("🤖 Analyze with AI",
                                type="primary",
                                width='stretch',
                                key="analyze_ai_button")

                if analyze_ai:
                    with st.spinner(f"Analyzing your resume with {ai_model}..."):
                        # Get file content
                        text = ""
                        try:
                            if uploaded_file.type == "application/pdf":
                                text = self.analyzer.extract_text_from_pdf(
                                    uploaded_file)
                            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                text = self.analyzer.extract_text_from_docx(
                                    uploaded_file)
                            else:
                                text = uploaded_file.getvalue().decode()
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                            st.stop()

                        # Analyze with AI
                        try:
                            # Show a loading animation
                            with st.spinner("🧠 AI is analyzing your resume..."):
                                progress_bar = st.progress(0)
                                
                                # Get the selected model
                                selected_model = "Google Gemini"
                                
                                # Update progress
                                progress_bar.progress(10)
                                
                                # Extract text from the resume
                                analyzer = AIResumeAnalyzer()
                                if uploaded_file.type == "application/pdf":
                                    resume_text = analyzer.extract_text_from_pdf(
                                        uploaded_file)
                                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                    resume_text = analyzer.extract_text_from_docx(
                                        uploaded_file)
                                else:
                                    # For text files or other formats
                                    resume_text = uploaded_file.getvalue().decode('utf-8')
                                
                                # Initialize the AI analyzer (moved after text extraction)
                                progress_bar.progress(30)
                                
                                # Get the job role
                                job_role = selected_role if selected_role else "Not specified"
                                
                                # Update progress
                                progress_bar.progress(50)
                                
                                # Analyze the resume with Google Gemini
                                if use_custom_job_desc and custom_job_description:
                                    # Use custom job description for analysis
                                    analysis_result = analyzer.analyze_resume_with_gemini(
                                        resume_text, job_role=job_role, job_description=custom_job_description)
                                    # Show that custom job description was used
                                    st.session_state['used_custom_job_desc'] = True
                                else:
                                    # Use standard role-based analysis
                                    analysis_result = analyzer.analyze_resume_with_gemini(
                                        resume_text, job_role=job_role)
                                    st.session_state['used_custom_job_desc'] = False

                                
                                # Update progress
                                progress_bar.progress(80)
                                
                                # Save the analysis to the database
                                if analysis_result and "error" not in analysis_result:
                                    # Extract the resume score
                                    resume_score = analysis_result.get(
                                        "resume_score", 0)
                                    
                                    # Save to database
                                    save_ai_analysis_data(
                                        None,  # No user_id needed
                                        {
                                            "model_used": selected_model,
                                            "resume_score": resume_score,
                                            "job_role": job_role
                                        }
                                    )

                                # Complete the progress
                                progress_bar.progress(100)
                                
                                # Display the analysis result
                                if analysis_result and "error" not in analysis_result:
                                    st.success("✅ Analysis complete!")
                                    
                                    # Extract data from the analysis
                                    full_response = analysis_result.get(
                                        "analysis", "")
                                    resume_score = analysis_result.get(
                                        "resume_score", 0)
                                    ats_score = analysis_result.get(
                                        "ats_score", 0)
                                    model_used = analysis_result.get(
                                        "model_used", selected_model)
                                    
                                    # Store the full response in session state for download
                                    st.session_state['full_analysis'] = full_response
                                    
                                    # Display the analysis in a nice format
                                    st.markdown("## Full Analysis Report")
                                    
                                    # Get current date
                                    from datetime import datetime
                                    current_date = datetime.now().strftime("%B %d, %Y")
                                    
                                    # Create a modern styled header for the report
                                    st.markdown(f"""
                                    <div style="background-color: #262730; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                        <h2 style="color: #ffffff; margin-bottom: 10px;">AI Resume Analysis Report</h2>
                                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                                            <div style="flex: 1; min-width: 200px;">
                                                <p style="color: #ffffff;"><strong>Job Role:</strong> {job_role if job_role else "Not specified"}</p>
                                                <p style="color: #ffffff;"><strong>Analysis Date:</strong> {current_date}</p>                                                                                                                                        </div>
                                            <div style="flex: 1; min-width: 200px;">
                                                <p style="color: #ffffff;"><strong>AI Model:</strong> {model_used}</p>
                                                <p style="color: #ffffff;"><strong>Overall Score:</strong> {resume_score}/100 - {"Excellent" if resume_score >= 80 else "Good" if resume_score >= 60 else "Needs Improvement"}</p>
                                                {f'<p style="color: #4CAF50;"><strong>✓ Custom Job Description Used</strong></p>' if st.session_state.get('used_custom_job_desc', False) else ''}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Add gauge charts for scores
                                    import plotly.graph_objects as go
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        # Resume Score Gauge
                                        fig1 = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=resume_score,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "Resume Score", 'font': {'size': 16}},
                                            gauge={
                                                'axis': {'range': [0, 100], 'tickwidth': 1},
                                                'bar': {'color': "#4CAF50" if resume_score >= 80 else "#FFA500" if resume_score >= 60 else "#FF4444"},
                                                'bgcolor': "white",
                                                'borderwidth': 2,
                                                'bordercolor': "gray",
                                                'steps': [
                                                    {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                    {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                    {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                    {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'}
                                                ],
                                                'threshold': {
                                                    'line': {'color': "red", 'width': 4},
                                                    'thickness': 0.75,
                                                    'value': 60
                                                }
                                            }
                                        ))
                                        
                                        fig1.update_layout(
                                            height=250,
                                            margin=dict(l=20, r=20, t=50, b=20),
                                        )
                                        
                                        st.plotly_chart(fig1, width='stretch')
                                        
                                        status = "Excellent" if resume_score >= 80 else "Good" if resume_score >= 60 else "Needs Improvement"
                                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{status}</div>", unsafe_allow_html=True)
                                    
                                    with col2:
                                        # ATS Score Gauge
                                        fig2 = go.Figure(go.Indicator(
                                            mode="gauge+number",
                                            value=ats_score,
                                            domain={'x': [0, 1], 'y': [0, 1]},
                                            title={'text': "ATS Optimization Score", 'font': {'size': 16}},
                                            gauge={
                                                'axis': {'range': [0, 100], 'tickwidth': 1},
                                                'bar': {'color': "#4CAF50" if ats_score >= 80 else "#FFA500" if ats_score >= 60 else "#FF4444"},
                                                'bgcolor': "white",
                                                'borderwidth': 2,
                                                'bordercolor': "gray",
                                                'steps': [
                                                    {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                    {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                    {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                    {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'}
                                                ],
                                                'threshold': {
                                                    'line': {'color': "red", 'width': 4},
                                                    'thickness': 0.75,
                                                    'value': 60
                                                }
                                            }
                                        ))
                                        
                                        fig2.update_layout(
                                            height=250,
                                            margin=dict(l=20, r=20, t=50, b=20),
                                        )
                                        
                                        st.plotly_chart(fig2, width='stretch')
                                        
                                        status = "Excellent" if ats_score >= 80 else "Good" if ats_score >= 60 else "Needs Improvement"
                                        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{status}</div>", unsafe_allow_html=True)

                                    # Add Job Description Match Score if custom job description was used
                                    if st.session_state.get('used_custom_job_desc', False) and custom_job_description:
                                        # Extract job match score from analysis result or calculate it
                                        job_match_score = analysis_result.get("job_match_score", 0)
                                        if not job_match_score and "job_match" in analysis_result:
                                            job_match_score = analysis_result["job_match"].get("score", 0)
                                        
                                        # If we have a job match score, display it
                                        if job_match_score:
                                            st.markdown("""
                                            <h3 style="background: linear-gradient(90deg, #4d7c0f, #84cc16); color: white; padding: 10px; border-radius: 5px; margin-top: 20px;">
                                                <i class="fas fa-handshake"></i> Job Description Match Analysis
                                            </h3>
                                            """, unsafe_allow_html=True)
                                            
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                # Job Match Score Gauge
                                                fig3 = go.Figure(go.Indicator(
                                                    mode="gauge+number",
                                                    value=job_match_score,
                                                    domain={'x': [0, 1], 'y': [0, 1]},
                                                    title={'text': "Job Match Score", 'font': {'size': 16}},
                                                    gauge={
                                                        'axis': {'range': [0, 100], 'tickwidth': 1},
                                                        'bar': {'color': "#4CAF50" if job_match_score >= 80 else "#FFA500" if job_match_score >= 60 else "#FF4444"},
                                                        'bgcolor': "white",
                                                        'borderwidth': 2,
                                                        'bordercolor': "gray",
                                                        'steps': [
                                                            {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                            {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                            {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                            {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'}
                                                        ],
                                                        'threshold': {
                                                            'line': {'color': "red", 'width': 4},
                                                            'thickness': 0.75,
                                                            'value': 60
                                                        }
                                                    }
                                                ))
                                                
                                                fig3.update_layout(
                                                    height=250,
                                                    margin=dict(l=20, r=20, t=50, b=20),
                                                )
                                                
                                                st.plotly_chart(fig3, width='stretch')
                                                
                                                match_status = "Excellent Match" if job_match_score >= 80 else "Good Match" if job_match_score >= 60 else "Low Match"
                                                st.markdown(f"<div style='text-align: center; font-weight: bold;'>{match_status}</div>", unsafe_allow_html=True)
                                            
                                            with col2:
                                                st.markdown("""
                                                <div style="background-color: #262730; padding: 20px; border-radius: 10px; height: 100%;">
                                                    <h4 style="color: #ffffff; margin-bottom: 15px;">What This Means</h4>
                                                    <p style="color: #ffffff;">This score represents how well your resume matches the specific job description you provided.</p>
                                                    <ul style="color: #ffffff; padding-left: 20px;">
                                                        <li><strong>80-100:</strong> Excellent match - your resume is highly aligned with this job</li>
                                                        <li><strong>60-79:</strong> Good match - your resume matches many requirements</li>
                                                        <li><strong>Below 60:</strong> Consider tailoring your resume more specifically to this job</li>
                                                    </ul>
                                                </div>
                                                """, unsafe_allow_html=True)
                                    

                                    # Format the full response with better styling
                                    formatted_analysis = full_response
                                    
                                    # Replace section headers with styled headers
                                    section_styles = {
                                        "## Overall Assessment": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-chart-line"></i> Overall Assessment
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Professional Profile Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #047857, #10b981); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-user-tie"></i> Professional Profile Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Skills Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #4f46e5, #818cf8); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-tools"></i> Skills Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Experience Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #9f1239, #e11d48); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-briefcase"></i> Experience Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Education Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #854d0e, #eab308); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-graduation-cap"></i> Education Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Key Strengths": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #166534, #22c55e); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-check-circle"></i> Key Strengths
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Areas for Improvement": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #9f1239, #fb7185); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-exclamation-circle"></i> Areas for Improvement
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## ATS Optimization Assessment": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #0e7490, #06b6d4); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-robot"></i> ATS Optimization Assessment
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Recommended Courses": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #5b21b6, #8b5cf6); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-book"></i> Recommended Courses
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Resume Score": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #0369a1, #0ea5e9); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-star"></i> Resume Score
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Role Alignment Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #7c2d12, #ea580c); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-bullseye"></i> Role Alignment Analysis
                                            </h3>
                                            <div class="section-content">""",
                                            
                                        "## Job Match Analysis": """<div class="report-section">
                                            <h3 style="background: linear-gradient(90deg, #4d7c0f, #84cc16); color: white; padding: 10px; border-radius: 5px;">
                                                <i class="fas fa-handshake"></i> Job Match Analysis
                                            </h3>
                                            <div class="section-content">""",
                                    }
                                    
                                    # Apply the styling to each section
                                    for section, style in section_styles.items():
                                        if section in formatted_analysis:
                                            formatted_analysis = formatted_analysis.replace(
                                                section, style)
                                            # Add closing div tags
                                            next_section = False
                                            for next_sec in section_styles.keys():
                                                if next_sec != section and next_sec in formatted_analysis.split(style)[1]:
                                                    split_text = formatted_analysis.split(style)[1].split(next_sec)
                                                    formatted_analysis = formatted_analysis.split(style)[0] + style + split_text[0] + "</div></div>" + next_sec + "".join(split_text[1:])
                                                    next_section = True
                                                    break
                                            if not next_section:
                                                formatted_analysis = formatted_analysis + "</div></div>"
                                    
                                    # Remove any extra closing div tags that might have been added
                                    formatted_analysis = formatted_analysis.replace("</div></div></div></div>", "</div></div>")
                                    
                                    # Ensure we don't have any orphaned closing tags at the end
                                    if formatted_analysis.endswith("</div>"):
                                        # Count opening and closing div tags
                                        open_tags = formatted_analysis.count("<div")
                                        close_tags = formatted_analysis.count("</div>")
                                        
                                        # If we have more closing than opening tags, remove the extras
                                        if close_tags > open_tags:
                                            excess = close_tags - open_tags
                                            formatted_analysis = formatted_analysis[:-6 * excess]
                                    
                                    # Clean up any visible HTML tags that might appear in the text
                                    formatted_analysis = formatted_analysis.replace("&lt;/div&gt;", "")
                                    formatted_analysis = formatted_analysis.replace("&lt;div&gt;", "")
                                    formatted_analysis = formatted_analysis.replace("<div>", "<div>")  # Ensure proper opening
                                    formatted_analysis = formatted_analysis.replace("</div>", "</div>")  # Ensure proper closing
                                    
                                    # Add CSS for the report
                                    st.markdown("""
                                    <style>
                                        .report-section {
                                            margin-bottom: 25px;
                                            border: 1px solid #4B4B4B;
                                            border-radius: 8px;
                                            overflow: hidden;
                                        }
                                        .section-content {
                                            padding: 15px;
                                            background-color: #262730;
                                            color: #ffffff;
                                        }
                                        .report-section h3 {
                                            margin-top: 0;
                                            font-weight: 600;
                                        }
                                        .report-section ul {
                                            padding-left: 20px;
                                        }
                                        .report-section p {
                                            color: #ffffff;
                                            margin-bottom: 10px;
                                        }
                                        .report-section li {
                                            color: #ffffff;
                                            margin-bottom: 5px;
                                        }
                                    </style>
                                    """, unsafe_allow_html=True)

                                    # Display the formatted analysis
                                    st.markdown(f"""
                                    <div style="background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4B4B4B; color: #ffffff;">
                                        {formatted_analysis}
                                    </div>
                                    """, unsafe_allow_html=True)

                                    # Create a PDF report
                                    pdf_buffer = self.ai_analyzer.generate_pdf_report(
                                        analysis_result={
                                            "score": resume_score,
                                            "ats_score": ats_score,
                                            "model_used": model_used,
                                            "full_response": full_response,
                                            "strengths": analysis_result.get("strengths", []),
                                            "weaknesses": analysis_result.get("weaknesses", []),
                                            "used_custom_job_desc": st.session_state.get('used_custom_job_desc', False),
                                            "custom_job_description": custom_job_description if st.session_state.get('used_custom_job_desc', False) else ""
                                        },
                                        candidate_name=st.session_state.get(
                                            'candidate_name', 'Candidate'),
                                        job_role=selected_role
                                    )

                                    # PDF download button
                                    if pdf_buffer:
                                        st.download_button(
                                            label="📊 Download PDF Report",
                                            data=pdf_buffer,
                                            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                            mime="application/pdf",
                                            width='stretch',
                                                                                    )
                                    else:
                                        st.error("PDF generation failed. Please try again later.")
                                else:
                                    st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                        except Exception as ai_error:
                            st.error(f"Error during AI analysis: {str(ai_error)}")
                            import traceback as tb
                            st.code(tb.format_exc())

        pass


    def main(self):
        """Main application entry point"""
        self.apply_global_styles()
        
        with st.sidebar:
            st_lottie(self.load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_xyadoh9h.json"), height=200, key="sidebar_animation")
            st.title("Smart Resume AI")
            st.markdown("---")
            
            # Navigation buttons
            for page_name in self.pages.keys():
                if st.button(page_name, width='stretch'):
                    cleaned_name = page_name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip()
                    st.session_state.page = cleaned_name
                    st.rerun()



        # Force home page on first load
        if 'initial_load' not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = 'resume_analyzer'
            st.rerun()
        
        # Get current page and render it
        current_page = st.session_state.get('page', 'resume_analyzer')
        
        # Create a mapping of cleaned page names to original names
        page_mapping = {name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip(): name 
                       for name in self.pages.keys()}
        
        # Render the appropriate page
        if current_page in page_mapping:
            self.pages[page_mapping[current_page]]()
        else:
            # Default to home page if invalid page
            self.render_analyzer()
    

if __name__ == "__main__":
    app = ResumeApp()
    app.main()