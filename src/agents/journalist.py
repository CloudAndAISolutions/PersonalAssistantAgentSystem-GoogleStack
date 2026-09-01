from google.adk import Agent
from src.tools.gmail_tool import GmailTool
from src.tools.calendar_tool import CalendarTool
from src.tools.tasks_tool import TasksTool
from src.services.config import config

# Initialize tools
gmail_tool = GmailTool()
calendar_tool = CalendarTool()
tasks_tool = TasksTool()

def summarize_day_emails() -> str:
    """Fetches important emails received today to help summarize the day's activity."""
    # Reusing the get_important_emails function to get context
    emails = gmail_tool.get_important_emails(max_results=15, since="1d")
    if not emails:
        return "No significant emails found today."
    
    result = "Today's Important Emails:\n"
    for e in emails:
        result += f"- From: {e['from']} | Subject: {e['subject']}\n"
    return result

def summarize_day_events() -> str:
    """Fetches all calendar events that happened today."""
    events = calendar_tool.get_today_events()
    if not events:
        return "No events on the calendar today."
        
    result = "Today's Events:\n"
    for e in events:
        result += f"- {e.get('start', 'Time unknown')}: {e['title']}\n"
    return result

def summarize_completed_tasks() -> str:
    """Note: Tasks API doesn't easily filter by 'completed today' without pagination logic.
    For this prototype, we'll return a placeholder or query pending tasks to infer state."""
    # In a full implementation, you'd fetch tasks with 'showCompleted=True' and filter by 'completed' timestamp.
    return "Task tracking for completed items requires additional API logic. Skip for now."

def make_journalist_agent(name: str = "journalist") -> Agent:
    """Factory that creates a fresh Journalist agent instance.
    
    ADK enforces a single-parent constraint, so each SequentialAgent that needs
    a journalist must get its own instance via this factory.
    """
    return Agent(
        name=name,
        model=config.model_name,
        description="Analyzes the day's digital footprint and extracts key factual bullet points.",
        instruction="""
    You are an objective journalist observing the user's day.
    
    Workflow:
    1. Call `summarize_day_events` to see what meetings or events occurred.
    2. Call `summarize_day_emails` to see what important communications happened.
    3. Compile these facts into a strictly factual, bulleted list of "What happened today".
    4. Do NOT write prose. Do NOT write a blog post. Only output raw, structured facts.
    5. Pass this factual list back to the Coordinator so it can be sent to the Writer agent.
    """,
        tools=[summarize_day_events, summarize_day_emails, summarize_completed_tasks]
    )

# Default instance (used by evening_flow in coordinator)
journalist_agent = make_journalist_agent("journalist")
