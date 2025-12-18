import streamlit as st
import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# Handle CrewAI imports with error checking
try:
    from crewai import Agent, Task, Crew, LLM
    CREWAI_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ CrewAI not installed: {e}")
    CREWAI_AVAILABLE = False

try:
    from crewai_tools import (
        ScrapeWebsiteTool,
        SerperDevTool,
        FileReadTool,
        MDXSearchTool
    )
    TOOLS_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ CrewAI Tools not installed: {e}")
    TOOLS_AVAILABLE = False

# Import document processing libraries with fallbacks
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

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Resume Tailoring Assistant | Akash Bauri",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .developer-credit {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 50px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        font-weight: 600;
        z-index: 999;
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== API KEY CONFIGURATION ==========
def get_api_key(key_name):
    """
    Get API key from Streamlit secrets or environment variables
    Priority: Streamlit Secrets > Environment Variables
    """
    try:
        return st.secrets[key_name]
    except (KeyError, FileNotFoundError, AttributeError):
        return os.getenv(key_name)

# Get API keys
GROQ_API_KEY = get_api_key("GROQ_API_KEY")
SERPER_API_KEY = get_api_key("SERPER_API_KEY")

# Set environment variables
if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY
    os.environ["OPENAI_API_KEY"] = GROQ_API_KEY
    os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"

if SERPER_API_KEY:
    os.environ["SERPER_API_KEY"] = SERPER_API_KEY

def check_api_keys():
    """Validate API keys are present"""
    if not GROQ_API_KEY or not SERPER_API_KEY:
        st.error("❌ API keys not configured!")
        with st.expander("🔑 How to Configure API Keys"):
            st.code("""
# For Streamlit Cloud:
Go to App Settings → Secrets → Add:

GROQ_API_KEY = "your_groq_key_here"
SERPER_API_KEY = "your_serper_key_here"

# For Local Development:
Create .env file with:

GROQ_API_KEY=your_groq_key_here
SERPER_API_KEY=your_serper_key_here
            """)
        return False
    return True

# Initialize LLM with proper Groq configuration
def initialize_llm(model_name="llama-3.3-70b-versatile"):
    """Initialize Groq LLM for CrewAI"""
    try:
        llm = LLM(
            model=f"groq/{model_name}",
            api_key=GROQ_API_KEY,
            temperature=0.7,
            max_tokens=2000
        )
        return llm
    except Exception as e:
        st.error(f"Error initializing LLM: {e}")
        return None

# Initialize tools
if TOOLS_AVAILABLE:
    scrape_tool = ScrapeWebsiteTool()
    search_tool = SerperDevTool()
else:
    scrape_tool = None
    search_tool = None

# ========== HELPER FUNCTIONS ==========

def extract_text_from_docx(file):
    """Extract text from uploaded DOCX file"""
    if not DOCX_AVAILABLE:
        st.error("❌ DOCX support not available")
        return None
    try:
        doc = docx.Document(file)
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return "\n".join(text)
    except Exception as e:
        st.error(f"Error reading DOCX file: {str(e)}")
        return None

def extract_text_from_pdf(file):
    """Extract text from uploaded PDF file"""
    if not PDF_AVAILABLE:
        st.error("❌ PDF support not available")
        return None
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = []
        for page in pdf_reader.pages:
            text.append(page.extract_text())
        return "\n".join(text)
    except Exception as e:
        st.error(f"Error reading PDF file: {str(e)}")
        return None

def markdown_to_ats_pdf(markdown_file_path):
    """Convert markdown resume to ATS-friendly PDF using ReportLab"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from io import BytesIO
        import re
        
        # Read markdown content
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='black',
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='black',
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor='black',
            spaceAfter=6,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor='black',
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        # Story for building PDF
        story = []
        
        # Parse markdown line by line
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                story.append(Spacer(1, 0.1*inch))
                continue
            
            # H1 - Title
            if line.startswith('# '):
                text = line[2:].strip()
                story.append(Paragraph(text, title_style))
                
            # H2 - Main sections
            elif line.startswith('## '):
                text = line[3:].strip()
                story.append(Spacer(1, 0.15*inch))
                story.append(Paragraph(text, heading_style))
                
            # H3 - Subsections
            elif line.startswith('### '):
                text = line[4:].strip()
                story.append(Paragraph(text, subheading_style))
                
            # Bullet points
            elif line.startswith('- ') or line.startswith('* '):
                text = '• ' + line[2:].strip()
                story.append(Paragraph(text, body_style))
                
            # Numbered lists
            elif re.match(r'^\d+\. ', line):
                text = line
                story.append(Paragraph(text, body_style))
                
            # Regular text
            else:
                text = line.replace('**', '').replace('__', '').replace('*', '').replace('_', '')
                story.append(Paragraph(text, body_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

# ========== UI COMPONENTS ==========

# Title and description
st.markdown('<h1 class="main-header">🚀 AI Resume Tailoring Assistant</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Powered by CrewAI & Groq | Transform your resume with AI agents</p>',
    unsafe_allow_html=True
)

# Developer Credit Badge
st.markdown(
    '<div class="developer-credit">👨‍💻 Developed by Akash Bauri | AI Engineer</div>',
    unsafe_allow_html=True
)

st.markdown("""
### 📋 How It Works:
1. **Upload** your resume (PDF or DOCX format)
2. **Provide** job posting URL and GitHub profile
3. **Add** a personal summary about yourself
4. **Click** "Tailor My Resume" and let AI agents work their magic
5. **Download** your tailored resume as ATS-friendly PDF

---
""")

# Check if dependencies are available
if not CREWAI_AVAILABLE or not TOOLS_AVAILABLE:
    st.error("❌ Required dependencies not installed. Please check requirements.txt")
    st.stop()

# Sidebar for inputs
with st.sidebar:
    st.header("📋 Input Your Details")
    
    # Resume upload
    st.subheader("1️⃣ Upload Resume")
    uploaded_file = st.file_uploader(
        "Choose your resume file",
        type=['pdf', 'docx', 'doc'],
        help="Upload your current resume in PDF or DOCX format"
    )
    
    if uploaded_file:
        file_type = uploaded_file.type
        file_size = uploaded_file.size / 1024
        
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        st.info(f"📊 Size: {file_size:.2f} KB")
        
        # Save the file
        file_extension = uploaded_file.name.split('.')[-1]
        resume_path = f"resume.{file_extension}"
        
        with open(resume_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract and display preview
        with st.expander("👁️ Preview Resume Content"):
            if file_extension == 'pdf':
                resume_text = extract_text_from_pdf(uploaded_file)
            else:
                resume_text = extract_text_from_docx(uploaded_file)
            
            if resume_text:
                st.text_area("Resume Content", resume_text[:500] + "...", height=200, disabled=True)
    
    st.markdown("---")
    
    # Job posting URL
    st.subheader("2️⃣ Job Details")
    job_posting_url = st.text_input(
        "Job Posting URL",
        placeholder="https://example.com/careers/job-id",
        help="Paste the full URL of the job posting"
    )
    
    st.markdown("---")
    
    # GitHub URL
    st.subheader("3️⃣ GitHub Profile")
    github_url = st.text_input(
        "GitHub Profile URL",
        placeholder="https://github.com/yourusername",
        help="Your GitHub profile URL"
    )
    
    st.markdown("---")
    
    # Personal writeup
    st.subheader("4️⃣ Personal Summary")
    personal_writeup = st.text_area(
        "About Yourself",
        placeholder="Example: I'm a passionate AI Engineer with 3 years of experience...",
        height=200,
        help="Write a brief professional summary"
    )
    
    st.markdown("---")
    
    # Model selection
    st.subheader("5️⃣ AI Model")
    model_choice = st.selectbox(
        "Groq Model",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ],
        index=0,
        help="Select AI model"
    )
    
    st.markdown("---")
    
    # Process button
    process_button = st.button(
        "🎯 Tailor My Resume",
        type="primary",
        use_container_width=True
    )

# ========== AI AGENTS CREATION ==========

@st.cache_resource
def create_agents(model_name):
    """Create CrewAI agents with proper LLM configuration"""
    
    # Initialize LLM
    llm = initialize_llm(model_name)
    
    if not llm:
        st.error("❌ Failed to initialize LLM")
        return None, None, None, None
    
    researcher = Agent(
        role="Tech Job Researcher",
        goal="Analyze job postings and extract key requirements",
        tools=[scrape_tool, search_tool],
        llm=llm,
        verbose=True,
        backstory=(
            "Expert at analyzing job postings to identify critical skills and requirements."
        )
    )
    
    profiler = Agent(
        role="Personal Profiler",
        goal="Build comprehensive professional profiles",
        tools=[scrape_tool, search_tool],
        llm=llm,
        verbose=True,
        backstory=(
            "Expert at synthesizing resumes, GitHub profiles, and personal statements."
        )
    )
    
    resume_strategist = Agent(
        role="Resume Strategist",
        goal="Create ATS-optimized resumes",
        tools=[scrape_tool, search_tool],
        llm=llm,
        verbose=True,
        backstory=(
            "Expert at crafting ATS-friendly resumes that highlight relevant experience."
        )
    )
    
    interview_preparer = Agent(
        role="Interview Preparer",
        goal="Generate targeted interview questions",
        tools=[scrape_tool, search_tool],
        llm=llm,
        verbose=True,
        backstory=(
            "Expert at anticipating interview questions based on job requirements."
        )
    )
    
    return researcher, profiler, resume_strategist, interview_preparer

# ========== CREW EXECUTION ==========

def run_crew(job_url, github, writeup, resume_file, model_name):
    """Execute CrewAI workflow"""
    
    agents = create_agents(model_name)
    if None in agents:
        raise Exception("Failed to create agents")
    
    researcher, profiler, resume_strategist, interview_preparer = agents
    
    # Task 1: Job Analysis
    research_task = Task(
        description=(
            f"Analyze this job posting: {job_url}\n"
            "Extract: required skills, qualifications, responsibilities, ATS keywords."
        ),
        expected_output=(
            "Detailed job requirements with must-have skills and ATS keywords."
        ),
        agent=researcher,
        async_execution=True
    )
    
    # Task 2: Candidate Profiling
    profile_task = Task(
        description=(
            f"Build profile from:\n"
            f"GitHub: {github}\n"
            f"Resume: {resume_file}\n"
            f"Summary: {writeup}\n"
            "Identify relevant skills and experiences."
        ),
        expected_output=(
            "Complete professional profile with skills and achievements."
        ),
        agent=profiler,
        async_execution=True
    )
    
    # Task 3: Resume Tailoring
    resume_strategy_task = Task(
        description=(
            "Create ATS-optimized resume:\n"
            "- Use job keywords naturally\n"
            "- Highlight relevant experience\n"
            "- Quantify achievements\n"
            "- Single-column format\n"
            "Do NOT fabricate information."
        ),
        expected_output=(
            "Complete ATS-friendly resume in markdown with: Summary, Skills, Experience, Projects, Education."
        ),
        output_file="tailored_resume.md",
        context=[research_task, profile_task],
        agent=resume_strategist
    )
    
    # Task 4: Interview Prep
    interview_preparation_task = Task(
        description=(
            "Generate TOP 10 interview questions with:\n"
            "1. The question\n"
            "2. Why it's asked\n"
            "3. Key talking points\n"
            "4. How to connect to experience"
        ),
        expected_output=(
            "Top 10 interview questions with detailed guidance."
        ),
        output_file="interview_materials.md",
        context=[research_task, profile_task, resume_strategy_task],
        agent=interview_preparer
    )
    
    # Create and run crew
    job_application_crew = Crew(
        agents=[researcher, profiler, resume_strategist, interview_preparer],
        tasks=[research_task, profile_task, resume_strategy_task, interview_preparation_task],
        verbose=True
    )
    
    # Execute
    result = job_application_crew.kickoff(inputs={
        'job_posting_url': job_url,
        'github_url': github,
        'personal_writeup': writeup
    })
    
    return result

# ========== MAIN PROCESSING ==========

if process_button:
    # Check API keys
    if not check_api_keys():
        st.stop()
    
    # Validation
    if not uploaded_file:
        st.error("❌ Please upload your resume")
    elif not job_posting_url:
        st.error("❌ Please provide job posting URL")
    elif not github_url:
        st.error("❌ Please provide GitHub URL")
    elif not personal_writeup:
        st.error("❌ Please write personal summary")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("📊 Initializing AI agents...")
            progress_bar.progress(20)
            
            status_text.text("🔍 Analyzing job and profile...")
            progress_bar.progress(40)
            
            # Run crew
            result = run_crew(
                job_posting_url,
                github_url,
                personal_writeup,
                resume_path,
                model_choice
            )
            
            status_text.text("✍️ Generating resume...")
            progress_bar.progress(70)
            
            status_text.text("📄 Creating PDF...")
            progress_bar.progress(90)
            
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            
            st.success("🎉 Your materials are ready!")
            
            # Display results
            tab1, tab2, tab3 = st.tabs([
                "📄 Resume (Markdown)",
                "📥 ATS PDF",
                "💬 Interview Questions"
            ])
            
            with tab1:
                if os.path.exists("tailored_resume.md"):
                    with open("tailored_resume.md", "r", encoding="utf-8") as f:
                        resume_content = f.read()
                    
                    st.markdown("### Your Tailored Resume")
                    st.markdown(resume_content)
                    
                    st.download_button(
                        "⬇️ Download Markdown",
                        resume_content,
                        file_name="tailored_resume.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ Resume not generated")
            
            with tab2:
                st.markdown("### 📥 ATS-Friendly PDF")
                if os.path.exists("tailored_resume.md"):
                    try:
                        pdf_bytes = markdown_to_ats_pdf("tailored_resume.md")
                        
                        if pdf_bytes:
                            st.success("✅ PDF generated!")
                            st.download_button(
                                "📥 Download PDF",
                                pdf_bytes,
                                file_name="ATS_Resume.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"PDF error: {e}")
            
            with tab3:
                if os.path.exists("interview_materials.md"):
                    with open("interview_materials.md", "r", encoding="utf-8") as f:
                        interview_content = f.read()
                    
                    st.markdown("### 🎯 Top 10 Questions")
                    st.markdown(interview_content)
                    
                    st.download_button(
                        "⬇️ Download Guide",
                        interview_content,
                        file_name="Interview_Questions.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            with st.expander("🔍 Details"):
                st.exception(e)

# Footer
with st.expander("ℹ️ About"):
    st.markdown("""
    ### 🤖 Technology
    - **CrewAI**: Multi-agent framework
    - **Groq API**: Llama 3.3 70B
    - **Serper**: Web search
    
    **Developer:** Akash Bauri | AI Engineer
    """)

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Built by Akash Bauri**")
with col2:
    st.markdown("**CrewAI & Groq**")
with col3:
    st.markdown("**© 2025**")
