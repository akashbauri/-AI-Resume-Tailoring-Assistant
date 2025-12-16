import streamlit as st
import os
from dotenv import load_dotenv

# Handle CrewAI imports with error checking
try:
    from crewai import Agent, Task, Crew
except ImportError:
    st.error("❌ CrewAI not installed. Please check requirements.txt")
    st.stop()

try:
    from crewai_tools import (
        ScrapeWebsiteTool,
        SerperDevTool,
        FileReadTool,
        MDXSearchTool
    )
except ImportError:
    st.error("❌ CrewAI Tools not installed. Please check requirements.txt")
    st.stop()

# Import other dependencies with fallbacks
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    st.warning("⚠️ python-docx not available. DOCX upload disabled.")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    st.warning("⚠️ PyPDF2 not available. PDF reading limited.")

import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# ... rest of your app code
