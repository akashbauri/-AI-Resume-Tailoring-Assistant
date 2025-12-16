from crewai_tools import (
    ScrapeWebsiteTool,
    SerperDevTool,
    FileReadTool,
    MDXSearchTool
)
import os

# Initialize tools
scrape_tool = ScrapeWebsiteTool()
search_tool = SerperDevTool()

# Dynamic file reading based on uploaded file
def get_resume_path():
    """Get the path of uploaded resume file"""
    if os.path.exists('./resume.pdf'):
        return './resume.pdf'
    elif os.path.exists('./resume.docx'):
        return './resume.docx'
    elif os.path.exists('./resume.doc'):
        return './resume.doc'
    return None

resume_path = get_resume_path()
if resume_path:
    read_resume = FileReadTool(file_path=resume_path)
    semantic_search_resume = MDXSearchTool(mdx=resume_path)
else:
    # Placeholder tools
    read_resume = FileReadTool(file_path='./resume.pdf')
    semantic_search_resume = MDXSearchTool(mdx='./resume.pdf')
