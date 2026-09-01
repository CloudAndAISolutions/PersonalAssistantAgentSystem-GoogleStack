"""
blogger_writer.py — Agent that publishes journal narratives to Blogger as draft posts.

This agent is the production counterpart of writer.py.
- writer.py    → saves to Google Docs (dev/review mode)
- blogger_writer.py → saves to Blogger as a DRAFT (production mode, never auto-published)

The user manually reviews and publishes from the Blogger dashboard.
"""
from google.adk import Agent
from src.tools.blogger_tool import BloggerTool
from src.services.config import config
from datetime import datetime
import pytz

blogger_tool = BloggerTool()

def create_blogger_draft(html_content: str, labels: str = "") -> str:
    """Saves the formatted blog post to Blogger as a DRAFT (never auto-published).

    The post will appear in your Blogger dashboard under 'Drafts' for review.
    Publish manually when you are satisfied.

    Args:
        html_content: Complete HTML body of the blog post.
        labels:       Optional comma-separated tags/labels (e.g. "journal,daily,life").
    """
    timezone = pytz.timezone('Australia/Brisbane')
    now = datetime.now(timezone)
    day_no    = now.strftime("%d").lstrip('0')
    date_long = now.strftime(f"%A, {day_no} %B %Y")    # e.g. Tuesday, 2 September 2026
    title = f"Daily Journal — {date_long}"

    # Inject a visible date subtitle into the post body
    import re
    date_header = f'<h2 style="color:#888;font-weight:normal;margin-top:4px;">{date_long}</h2>\n'
    if '<body' in html_content:
        html_content = re.sub(r'(<body[^>]*>)', r'\1\n' + date_header, html_content, count=1)
    else:
        html_content = date_header + html_content

    label_list = [l.strip() for l in labels.split(',') if l.strip()] if labels else []

    result = blogger_tool.create_draft_post(
        title=title,
        html_content=html_content,
        labels=label_list or ['journal', 'daily']
    )

    if result.get('status') == 'success':
        return (
            f"Successfully saved Blogger draft: {result.get('url') or result.get('selfLink')}\n"
            f"Post ID: {result.get('id')}\n"
            f"Review and publish it from your Blogger dashboard."
        )
    else:
        return f"Failed to save Blogger draft: {result.get('message')}"


# Define the Blogger Writer Agent
blogger_writer_agent = Agent(
    name="blogger_writer",
    model=config.model_name,
    description=(
        "Takes factual bullet points and writes an engaging daily journal post, "
        "then saves it to Blogger as a DRAFT for manual review before publishing."
    ),
    instruction="""
    You are an engaging, reflective writer producing content for a personal Blogger blog.
    You receive dry, factual bullet points from the Journalist agent (or from context).

    Workflow:
    1. Read the bullet points provided in the prompt.
    2. Write an engaging, reflective daily journal entry based on those facts.
       - Write in the first person ("I").
       - Adopt a warm, personal, conversational tone.
       - Use valid HTML (<h1>, <p>, <ul>, <strong>). 
       - Make it feel like a genuine personal blog post.
    3. Add photo placeholders where relevant: [INSERT PHOTO 1 HERE].
    4. Call `create_blogger_draft` with the complete HTML body.
       - Optionally pass a comma-separated `labels` string (e.g. "journal,daily,life").
       - The tool will handle the title and date automatically.
    5. Report the draft URL back to the user.

    IMPORTANT: The post is always saved as a DRAFT. Never claim it has been published.
    """,
    tools=[create_blogger_draft]
)
