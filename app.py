import streamlit as st
import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# Load environment first
load_dotenv()

# Imports
try:
    from crewai import Agent, Task, Crew
    CREWAI_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ CrewAI: {e}")
    CREWAI_AVAILABLE = False

try:
    from crewai_tools import ScrapeWebsiteTool, SerperDevTool
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="AI Resume Tailoring | Akash Bauri",
    page_icon="📄",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .developer-credit {
        position: fixed;
        bottom: 15px;
        right: 15px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 40px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        font-weight: 600;
        font-size: 0.85rem;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# ========== API KEYS ==========

def get_api_key(key_name):
    try:
        return st.secrets[key_name]
    except:
        return os.getenv(key_name)

GROQ_API_KEY = get_api_key("GROQ_API_KEY")
SERPER_API_KEY = get_api_key("SERPER_API_KEY")

# Set environment variables
if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY
    os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
    os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
    
if SERPER_API_KEY:
    os.environ["SERPER_API_KEY"] = SERPER_API_KEY

def check_keys():
    if not GROQ_API_KEY:
        st.error("❌ Groq API key missing!")
        with st.expander("Setup"):
            st.code("""GROQ_API_KEY = "gsk_..."
SERPER_API_KEY = "..."""")
        return False
    return True

# Tools
scrape_tool = ScrapeWebsiteTool() if TOOLS_AVAILABLE else None
search_tool = SerperDevTool() if TOOLS_AVAILABLE and SERPER_API_KEY else None

# ========== HELPERS ==========

def extract_pdf(file):
    if not PDF_AVAILABLE:
        return None
    try:
        reader = PyPDF2.PdfReader(file)
        return "\n".join([p.extract_text() for p in reader.pages])
    except:
        return None

def extract_docx(file):
    if not DOCX_AVAILABLE:
        return None
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        return None

def make_pdf(md_file):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                topMargin=0.75*inch, bottomMargin=0.75*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        title = ParagraphStyle('T', parent=styles['Heading1'], fontSize=18, 
                              alignment=TA_CENTER, fontName='Helvetica-Bold')
        head = ParagraphStyle('H', parent=styles['Heading2'], fontSize=14, fontName='Helvetica-Bold')
        body = ParagraphStyle('B', parent=styles['Normal'], fontSize=11)
        
        story = []
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.1*inch))
            elif line.startswith('# '):
                story.append(Paragraph(line[2:], title))
            elif line.startswith('## '):
                story.append(Spacer(1, 0.15*inch))
                story.append(Paragraph(line[3:], head))
            elif line.startswith('- '):
                story.append(Paragraph('• ' + line[2:], body))
            else:
                story.append(Paragraph(line.replace('**', '').replace('*', ''), body))
        
        doc.build(story)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"PDF error: {e}")
        return None

# ========== UI ==========

st.markdown('<h1 class="main-header">🚀 AI Resume Tailoring Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Powered by CrewAI & Groq | Built by Akash Bauri</p>', unsafe_allow_html=True)
st.markdown('<div class="developer-credit">👨‍💻 Developed by Akash Bauri | AI Engineer</div>', unsafe_allow_html=True)

st.markdown("**Upload resume → Add job URL & GitHub → Get tailored resume + interview questions**")

if not CREWAI_AVAILABLE:
    st.error("❌ CrewAI not installed")
    st.stop()

# Sidebar
with st.sidebar:
    st.header("📝 Your Info")
    
    uploaded = st.file_uploader("**1. Resume**", type=['pdf', 'docx'])
    
    if uploaded:
        st.success(f"✅ {uploaded.name}")
        ext = uploaded.name.split('.')[-1]
        resume_path = f"resume.{ext}"
        with open(resume_path, "wb") as f:
            f.write(uploaded.getbuffer())
    
    st.markdown("---")
    job = st.text_input("**2. Job URL**", placeholder="https://...")
    
    st.markdown("---")
    github = st.text_input("**3. GitHub**", placeholder="https://github.com/...")
    
    st.markdown("---")
    summary = st.text_area("**4. Summary**", height=120, placeholder="I'm an AI Engineer...")
    
    st.markdown("---")
    model = st.selectbox("**5. Model**", 
                         ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
                         index=0)
    
    st.markdown("---")
    btn = st.button("🎯 **Tailor Resume**", use_container_width=True, type="primary")

# ========== CREW ==========

def create_agents(model_name):
    """Create agents with model name"""
    
    tools = [t for t in [scrape_tool, search_tool] if t]
    
    # Simple agent creation - let CrewAI handle LLM internally
    researcher = Agent(
        role="Job Analyst",
        goal="Extract job requirements",
        backstory="Expert at analyzing job postings",
        tools=tools,
        verbose=False,
        allow_delegation=False
    )
    
    profiler = Agent(
        role="Profile Analyst",
        goal="Analyze candidate profile",
        backstory="Expert at evaluating resumes",
        tools=tools,
        verbose=False,
        allow_delegation=False
    )
    
    writer = Agent(
        role="Resume Writer",
        goal="Write ATS-optimized resumes",
        backstory="Expert resume writer",
        tools=tools,
        verbose=False,
        allow_delegation=False
    )
    
    interviewer = Agent(
        role="Interview Coach",
        goal="Create interview questions",
        backstory="Expert interview coach",
        tools=tools,
        verbose=False,
        allow_delegation=False
    )
    
    return researcher, profiler, writer, interviewer

def run_crew(job_url, github_url, summ, model_name):
    """Run crew"""
    
    # Set model in environment
    os.environ["OPENAI_MODEL_NAME"] = model_name
    
    researcher, profiler, writer, interviewer = create_agents(model_name)
    
    # Tasks
    task1 = Task(
        description=f"Analyze job at {job_url}. List required skills and keywords.",
        expected_output="Job requirements and ATS keywords",
        agent=researcher
    )
    
    task2 = Task(
        description=f"Analyze GitHub {github_url} and summary: {summ}",
        expected_output="Candidate skills and experience",
        agent=profiler
    )
    
    task3 = Task(
        description="Write ATS resume with keywords, quantified achievements, clean format",
        expected_output="Complete markdown resume",
        agent=writer,
        output_file="tailored_resume.md",
        context=[task1, task2]
    )
    
    task4 = Task(
        description="Generate 10 interview questions with answers",
        expected_output="10 questions with guidance",
        agent=interviewer,
        output_file="interview_materials.md",
        context=[task1, task2, task3]
    )
    
    crew = Crew(
        agents=[researcher, profiler, writer, interviewer],
        tasks=[task1, task2, task3, task4],
        verbose=True
    )
    
    return crew.kickoff()

# ========== MAIN ==========

if btn:
    if not check_keys():
        st.stop()
    
    if not all([uploaded, job, github, summary]):
        st.error("❌ Fill all fields")
        st.stop()
    
    try:
        with st.spinner("🤖 Working..."):
            result = run_crew(job, github, summary, model)
        
        st.success("✅ Done!")
        
        t1, t2, t3 = st.tabs(["📄 Resume", "📥 PDF", "💬 Questions"])
        
        with t1:
            if os.path.exists("tailored_resume.md"):
                with open("tailored_resume.md", "r") as f:
                    md = f.read()
                st.markdown(md)
                st.download_button("⬇️ Download", md, "resume.md", use_container_width=True)
        
        with t2:
            if os.path.exists("tailored_resume.md"):
                pdf = make_pdf("tailored_resume.md")
                if pdf:
                    st.download_button("📥 PDF", pdf, "Resume.pdf", "application/pdf", use_container_width=True)
        
        with t3:
            if os.path.exists("interview_materials.md"):
                with open("interview_materials.md", "r") as f:
                    iq = f.read()
                st.markdown(iq)
                st.download_button("⬇️ Download", iq, "questions.md", use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ {str(e)}")
        with st.expander("Details"):
            st.exception(e)

st.markdown("---")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Akash Bauri**")
with c2:
    st.markdown("**CrewAI + Groq**")
with c3:
    st.markdown("**© 2025**")
