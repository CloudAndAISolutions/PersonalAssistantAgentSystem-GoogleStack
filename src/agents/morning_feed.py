from google.adk import Agent
from src.tools.gmail_tool import GmailTool
from src.tools.calendar_tool import CalendarTool
from src.tools.tasks_tool import TasksTool
from src.services.config import config
from datetime import datetime
import pytz

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

def compile_and_send_briefing(
    events_summary: str,
    tasks_summary: str,
    emails_summary: str
) -> str:
    """Renders an HTML morning briefing from the three summaries and emails it to the user.
    
    Call this once you have the output of get_today_events, get_pending_tasks, and
    get_unread_emails. Pass those raw text outputs directly as the three arguments.
    Do NOT pre-render HTML yourself — this function handles all formatting.
    
    Args:
        events_summary:  Raw text output from get_today_events().
        tasks_summary:   Raw text output from get_pending_tasks().
        emails_summary:  Raw text output from get_unread_emails().
    """
    timezone = pytz.timezone('Australia/Brisbane')
    today = datetime.now(timezone).strftime("%A, %B %d")

    # Build the HTML email internally
    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:640px;margin:auto;color:#333;">
    <h1 style="color:#f4a61e;">☀️ Good Morning! Here's your day — {today}</h1>
    <hr/>

    <h2>📅 Today's Schedule</h2>
    <pre style="background:#f9f9f9;padding:12px;border-radius:6px;white-space:pre-wrap;">{events_summary}</pre>

    <h2>📋 Tasks to Tackle</h2>
    <pre style="background:#f9f9f9;padding:12px;border-radius:6px;white-space:pre-wrap;color:{'#c0392b' if '[OVERDUE]' in tasks_summary else '#333'};">{tasks_summary}</pre>

    <h2>📧 Email Highlights</h2>
    <pre style="background:#f9f9f9;padding:12px;border-radius:6px;white-space:pre-wrap;">{emails_summary}</pre>

    <hr/>
    <p style="color:#888;font-size:12px;">Sent by your Personal Assistant Agent · {today}</p>
    </body></html>
    """

    try:
        gmail_tool.send_email(
            to='me',
            subject=f'☀️ Morning Briefing — {today}',
            html_body=html
        )
        return "Morning briefing sent successfully to your inbox!"
    except Exception as e:
        return f"Failed to send briefing: {str(e)}"

# Define the Morning Feed Agent
morning_feed_agent = Agent(
    name="morning_feed",
    model=config.model_name,
    description="Generates a daily morning briefing email based on calendar, tasks, and emails.",
    instruction="""
    You are a highly efficient personal assistant. Your job is to prepare a morning briefing.
    
    Workflow — follow these steps in order:
    1. Call `get_today_events` to check the calendar.
    2. Call `get_pending_tasks` to check for tasks (pay attention to [OVERDUE] items).
    3. Call `get_unread_emails` to find important emails.
    4. Call `compile_and_send_briefing`, passing the raw text output of each of the above 
       three calls directly as the three arguments:
         - events_summary  = output of step 1
         - tasks_summary   = output of step 2
         - emails_summary  = output of step 3
       Do NOT rewrite or format the content — pass it verbatim.
    """,
    tools=[get_unread_emails, get_today_events, get_pending_tasks, compile_and_send_briefing]
)
