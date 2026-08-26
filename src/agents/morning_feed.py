from google.adk import Agent
from src.tools.gmail_tool import GmailTool
from src.tools.calendar_tool import CalendarTool
from src.tools.tasks_tool import TasksTool
from src.services.config import config

# Initialize tools
gmail_tool = GmailTool()
calendar_tool = CalendarTool()
tasks_tool = TasksTool()

def get_unread_emails() -> str:
    """Fetches unread personal and work emails, automatically filtering out noise/newsletters."""
    emails = gmail_tool.get_unread_emails(max_results=10, since="1d")
    if not emails:
        return "No new important emails."
    
    result = "Unread Emails:\n"
    for e in emails:
        result += f"- From: {e['from']} | Subject: {e['subject']} | Snippet: {e['snippet']}\n"
    return result

def get_today_events() -> str:
    """Fetches all calendar events and meetings scheduled for today."""
    events = calendar_tool.get_today_events()
    if not events:
        return "No events scheduled for today."
        
    result = "Today's Events:\n"
    for e in events:
        result += f"- {e.get('start', 'Time unknown')}: {e['title']}\n"
    return result

def get_pending_tasks() -> str:
    """Fetches all pending tasks and flags overdue ones."""
    tasks = tasks_tool.get_pending_tasks()
    if not tasks:
        return "No pending tasks."
        
    result = "Pending Tasks:\n"
    for t in tasks:
        overdue = "[OVERDUE] " if t['overdue'] else ""
        result += f"- {overdue}{t['title']} (Due: {t['due']})\n"
    return result

def send_morning_briefing(html_content: str) -> str:
    """Sends the final HTML morning briefing to the user's email."""
    # Note: Replace with actual email address or fetch from profile
    # For now, we assume the user is sending it to themselves ('me')
    try:
        gmail_tool.send_email(
            to='me',
            subject='🌅 Your Morning Briefing',
            html_body=html_content
        )
        return "Briefing sent successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"

# Define the Morning Feed Agent
morning_feed_agent = Agent(
    name="morning_feed",
    model=config.model_name if hasattr(config, 'model_name') else "gemini-3.5-flash",
    description="Generates a daily morning briefing email based on calendar, tasks, and emails.",
    instruction="""
    You are a highly efficient personal assistant. Your job is to prepare a morning briefing.
    
    Workflow:
    1. Call `get_today_events` to check the calendar.
    2. Call `get_pending_tasks` to check for tasks, paying special attention to OVERDUE items.
    3. Call `get_unread_emails` to find important emails.
    4. Compile this information into a beautifully formatted HTML email. 
       - Use headings (<h2>, <h3>).
       - Highlight overdue tasks in bold red text.
       - Group events chronologically.
       - Keep it concise and uplifting.
    5. Call `send_morning_briefing` with the HTML content to deliver it to the user.
    """,
    tools=[get_unread_emails, get_today_events, get_pending_tasks, send_morning_briefing]
)
