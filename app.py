import streamlit as st
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq  # Use direct LangChain integration
import warnings

warnings.filterwarnings('ignore')
load_dotenv()

# Page config
st.set_page_config(page_title="AI Resume Tailoring | Akash Bauri", page_icon="📄", layout="wide")

# CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: 700; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 0.5rem;}
    .developer-credit {position: fixed; bottom: 15px; right: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 12px 20px; border-radius: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); font-weight: 600; font-size: 0.85rem; z-index: 999;}
    .stButton>button {background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white;}
</style>
""", unsafe_allow_html=True)

# API Keys
def get_key(name):
    try:
        return st.secrets.get(name)
    except:
        return os.getenv(name)

GROQ_KEY = get_key("GROQ_API_KEY")
SERPER_KEY = get_key("SERPER_API_KEY")

# Tools
try:
    from crewai_tools import ScrapeWebsiteTool, SerperDevTool
    scrape_tool = ScrapeWebsiteTool()
    search_tool = SerperDevTool() if SERPER_KEY else None
    if SERPER_KEY: os.environ["SERPER_API_KEY"] = SERPER_KEY
except:
    scrape_tool = None
    search_tool = None

# UI
st.markdown('<h1 class="main-header">🚀 AI Resume Tailoring Assistant</h1>', unsafe_allow_html=True)
st.markdown('<div class="developer-credit">👨‍💻 Developed by Akash Bauri | AI Engineer</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("📝 Your Info")
    uploaded = st.file_uploader("**1. Resume**", type=['pdf', 'docx'])
    job = st.text_input("**2. Job URL**", placeholder="https://...")
    github = st.text_input("**3. GitHub**", placeholder="https://github.com/...")
    summary = st.text_area("**4. Summary**", height=120, placeholder="I'm an AI Engineer...")
    model_choice = st.selectbox("**5. Model**", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"], index=0)
    btn = st.button("🎯 **Tailor Resume**", use_container_width=True, type="primary")

def run_crew(job_url, github_url, summ, model_name):
    # DIRECT LANGCHAIN INITIALIZATION (Most stable)
    llm = ChatGroq(
        api_key=GROQ_KEY,
        model=model_name,
        temperature=0.7
    )

    tools = [t for t in [scrape_tool, search_tool] if t]

    # Agents
    researcher = Agent(role="Job Analyst", goal="Extract job requirements", 
                      backstory="Expert analyst", tools=tools, llm=llm, verbose=True)
    profiler = Agent(role="Profile Analyst", goal="Analyze candidate profile", 
                    backstory="Expert evaluator", tools=tools, llm=llm, verbose=True)
    writer = Agent(role="Resume Writer", goal="Write ATS-optimized resumes", 
                   backstory="Expert resume writer", tools=tools, llm=llm, verbose=True)
    interviewer = Agent(role="Interview Coach", goal="Create interview questions", 
                       backstory="Expert coach", tools=tools, llm=llm, verbose=True)

    # Tasks
    task1 = Task(description=f"Analyze job at {job_url}.", expected_output="Job requirements", agent=researcher)
    task2 = Task(description=f"Analyze GitHub {github_url} and summary: {summ}", expected_output="Candidate profile", agent=profiler)
    task3 = Task(description="Write ATS resume", expected_output="Complete markdown resume", agent=writer, context=[task1, task2])
    task4 = Task(description="Generate 10 interview questions", expected_output="10 questions", agent=interviewer, context=[task3])

    crew = Crew(agents=[researcher, profiler, writer, interviewer], tasks=[task1, task2, task3, task4], verbose=True)
    return crew.kickoff()

if btn:
    if not GROQ_KEY:
        st.error("❌ Add GROQ_API_KEY in Secrets!")
        st.stop()
    
    try:
        with st.spinner("🤖 AI agents working..."):
            result = run_crew(job, github, summary, model_choice)
            st.success("✅ Done!")
            st.markdown(result.raw)
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
