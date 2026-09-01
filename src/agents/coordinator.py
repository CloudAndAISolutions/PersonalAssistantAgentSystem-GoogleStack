from google.adk import Agent
from google.adk.agents import SequentialAgent
from src.services.config import config
from .morning_feed import morning_feed_agent
from .journalist import journalist_agent
from .writer import writer_agent
from src.tools.docs_tool import DocsTool
from src.tools.blogger_tool import BloggerTool
from datetime import datetime
import re
import pytz

docs_tool = DocsTool()
blogger_tool = BloggerTool()

# ── Shared date helper ───────────────────────────────────────────────────────
def _week_ending_label() -> tuple[str, str]:
    """Returns (title_date, subtitle_date) using Brisbane timezone."""
    timezone = pytz.timezone('Australia/Brisbane')
    now = datetime.now(timezone)
    day_no = now.strftime("%d").lstrip('0')
    date_long = now.strftime(f"%A, {day_no} %B %Y")   # e.g. Tuesday, 2 September 2026
    return date_long

def _inject_date_header(html_content: str, subtitle: str) -> str:
    """Prepends a grey date subtitle to the HTML body."""
    header = f'<h2 style="color:#888;font-weight:normal;margin-top:4px;">{subtitle}</h2>\n'
    if '<body' in html_content:
        return re.sub(r'(<body[^>]*>)', r'\1\n' + header, html_content, count=1)
    return header + html_content


# ── Tool: save weekly report to Google Docs ──────────────────────────────────
def create_weekly_report_draft(html_content: str) -> str:
    """Saves the formatted weekly activity report to Google Docs as a DRAFT.

    Call this with the complete HTML body of the weekly report.
    The title and date header are added automatically.
    """
    date_long = _week_ending_label()
    title = f"Weekly Activity Report — {date_long}"
    enriched = _inject_date_header(html_content, f"Week ending {date_long}")
    result = docs_tool.create_blog_doc(title=title, html_content=enriched)
    if result.get('status') == 'success':
        return f"Google Docs draft created: {result.get('url')}"
    return f"Failed to create Google Docs draft: {result.get('message')}"


# ── Tool: publish weekly report to both Docs AND Blogger in one call ─────────
def publish_weekly_report(html_content: str) -> str:
    """Saves the weekly activity report as a draft to BOTH Google Docs and Blogger.

    Call this ONCE with the complete HTML body of the weekly report.
    - Google Docs:  saved as a draft you can view/edit at docs.google.com
    - Blogger:      saved as a DRAFT, never auto-published; review at blogger.com

    The title, date header, and labels are added automatically.
    Returns a combined status message with both URLs.
    """
    date_long = _week_ending_label()
    title = f"Weekly Activity Report — {date_long}"
    enriched = _inject_date_header(html_content, f"Week ending {date_long}")

    results = []

    # 1. Save to Google Docs
    docs_result = docs_tool.create_blog_doc(title=title, html_content=enriched)
    if docs_result.get('status') == 'success':
        results.append(f"Google Docs draft: {docs_result.get('url')}")
    else:
        results.append(f"Google Docs FAILED: {docs_result.get('message')}")

    # 2. Save to Blogger (same enriched HTML, same title)
    blogger_result = blogger_tool.create_draft_post(
        title=title,
        html_content=enriched,
        labels=['weekly-report', 'journal']
    )
    if blogger_result.get('status') == 'success':
        results.append(
            f"Blogger draft (NOT published): {blogger_result.get('url') or blogger_result.get('selfLink')}"
        )
    else:
        results.append(f"Blogger FAILED: {blogger_result.get('message')}")

    return "\n".join(results)


# ── Weekly Writer (Google Docs only) ────────────────────────────────────────
weekly_writer_agent = Agent(
    name="weekly_writer",
    model=config.model_name,
    description="Produces a structured weekly activity report and saves it to Google Docs as a draft.",
    instruction="""
    You are a professional summariser. Your job is to produce a weekly activity report.

    Workflow:
    1. Summarise the key highlights provided (calendar events, emails, tasks from the last 7 days).
    2. Structure the report with clear HTML sections: Overview, Key Events, Accomplishments, Financials, Upcoming.
    3. Write in a professional but warm tone — this is a personal journal/report.
    4. Call `create_weekly_report_draft` with the completed HTML to save it to Google Docs.
    """,
    tools=[create_weekly_report_draft]
)

# ── Weekly Publisher (Google Docs + Blogger draft) ───────────────────────────
weekly_publisher_agent = Agent(
    name="weekly_publisher",
    model=config.model_name,
    description=(
        "Produces a structured weekly activity report and saves it as a draft to "
        "both Google Docs AND Blogger in a single tool call (never auto-published)."
    ),
    instruction="""
    You are a professional summariser and publisher. Your job is to produce and publish the weekly report.

    Workflow:
    1. Summarise the key highlights provided (calendar events, emails, tasks from the last 7 days).
    2. Structure the report with clear HTML sections: Overview, Key Events, Accomplishments, Financials, Upcoming.
    3. Write in a professional but warm tone — this is a personal journal/report.
    4. Call `publish_weekly_report` ONCE with the complete HTML body.
       This single tool saves the report to BOTH Google Docs and Blogger simultaneously.
       The Blogger post is saved as a DRAFT — it is NEVER auto-published.
    5. Report both URLs from the tool response back to the user.
    """,
    tools=[publish_weekly_report]
)

# ── Evening Flow: Journalist → Writer (Google Docs) ──────────────────────────
evening_flow_agent = SequentialAgent(
    name="evening_flow",
    description="Gathers daily highlights via the Journalist, then writes a reflective journal draft to Google Docs.",
    sub_agents=[journalist_agent, writer_agent]
)

# ── Coordinator (Root Orchestrator) ─────────────────────────────────────────
coordinator_agent = Agent(
    name="coordinator",
    model=config.model_name,
    description="Routes scheduled triggers to the appropriate sub-agent.",
    instruction="""
    You are the Master Coordinator for the Personal Assistant System.

    You will receive a trigger string. Route it to the correct agent:

    Trigger routing:
    1. "7 AM Morning Trigger" or "morning_feed":
       → Transfer to the `morning_feed` sub-agent.
       It will fetch today's calendar, tasks, and emails, then email a morning briefing.

    2. "8 PM Evening Trigger" or "evening_digest":
       → Transfer to the `evening_flow` sub-agent.
       It will run the Journalist (collect day highlights) then the Writer (create Google Docs draft).

    3. "weekly_report" or "Weekly Report Trigger":
       → Transfer to the `weekly_writer` sub-agent with the instruction to produce a weekly activity report
         by querying the state store for the past 7 days of daily digests.

    4. "weekly_blogger" or "Weekly Blogger Post":
       → Transfer to the `weekly_publisher` sub-agent.
       It produces the same weekly activity report AND saves drafts to both Google Docs
       AND Blogger. The Blogger post is NEVER auto-published — manual review required.

    5. Any other manual question:
       → Answer it yourself or delegate to the most appropriate sub-agent.
    """,
    sub_agents=[morning_feed_agent, evening_flow_agent, weekly_writer_agent, weekly_publisher_agent]
)
