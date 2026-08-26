from google.adk import Agent
from src.tools.docs_tool import DocsTool
from src.services.config import config
from datetime import datetime
import pytz

docs_tool = DocsTool()

def create_blog_draft(html_content: str) -> str:
    """Uploads the formatted blog post to Google Docs as a draft."""
    timezone = pytz.timezone('Australia/Brisbane')
    date_str = datetime.now(timezone).strftime("%Y-%m-%d")
    title = f"Daily Journal Draft - {date_str}"
    
    result = docs_tool.create_blog_doc(title=title, html_content=html_content)
    
    if result.get('status') == 'success':
        return f"Successfully created draft: {result.get('url')}"
    else:
        return f"Failed to create draft: {result.get('message')}"

# Define the Writer Agent
writer_agent = Agent(
    name="writer",
    model=config.model_name if hasattr(config, 'model_name') else "gemini-3.5-flash",
    description="Takes factual bullet points and transforms them into an engaging narrative draft.",
    instruction="""
    You are an engaging, reflective writer. You receive dry, factual bullet points from the Journalist agent.
    
    Workflow:
    1. Read the bullet points provided in the prompt.
    2. Write an engaging, reflective daily journal entry based on those facts. 
       - Write in the first person ("I").
       - Adopt a warm, personal tone.
       - Structure it nicely with HTML tags (<h1>, <p>, <ul>).
       - Ensure the content looks like a blog post.
    3. If there are notes about photos to be added manually, add placeholders like [INSERT PHOTO 1 HERE].
    4. Call `create_blog_draft` and pass the HTML string to save it to Google Docs.
    """,
    tools=[create_blog_draft]
)
