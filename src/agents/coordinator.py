from google.adk import Agent
from google.adk.agents import SequentialAgent
from src.services.config import config
from .morning_feed import morning_feed_agent
from .journalist import journalist_agent
from .writer import writer_agent

# Define the Sequential Agent for the Evening Flow
evening_flow_agent = SequentialAgent(
    name="evening_flow",
    description="Gathers daily highlights and then writes a reflective journal in Google Docs.",
    sub_agents=[journalist_agent, writer_agent]
)

# Define the Coordinator Agent
coordinator_agent = Agent(
    name="coordinator",
    model=config.model_name if hasattr(config, 'model_name') else "gemini-3.5-flash",
    description="The main orchestrator that routes requests based on the time of day.",
    instruction="""
    You are the Master Coordinator for the Personal Assistant System.
    
    You will receive a trigger context (e.g., "7 AM Morning Trigger" or "8 PM Evening Trigger").
    
    Routing Logic:
    1. If the trigger is the "7 AM Morning Trigger":
       - Hand off the task to the `morning_feed` agent to generate and send the morning briefing.
       
    2. If the trigger is the "8 PM Evening Trigger":
       - Hand off the task to the `evening_flow` agent.
       
    3. If the user asks a direct question (Manual Trigger), answer it yourself or delegate to the appropriate sub-agent if they have the right tools.
    """,
    sub_agents=[morning_feed_agent, evening_flow_agent]
)
