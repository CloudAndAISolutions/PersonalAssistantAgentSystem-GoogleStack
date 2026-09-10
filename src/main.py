import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import asyncio

from src.agents.coordinator import coordinator_agent
from src.services.runner_utils import run_agent_with_fallback
from src.services.config import config

app = FastAPI(
    title="Personal Assistant Agent System",
    description="API to trigger multi-agent workflows for morning briefings, daily journals, and weekly reports.",
    version="1.0.0"
)

# Map trigger endpoints to the appropriate prompt for the Coordinator
TRIGGER_PROMPTS = {
    "morning_feed": "It is 7:00 AM. Execute the morning_feed trigger.",
    "evening_digest": "It is 8:00 PM. Execute the evening_digest trigger.",
    "weekly_report": (
        "It is Sunday 8:00 PM. Execute the weekly_report trigger. "
        "Produce a structured weekly activity report covering the past 7 days. "
        "Use any available context about recent calendar events, emails, and tasks."
    ),
    "weekly_blogger": (
        "It is Sunday 8:00 PM. Execute the weekly_blogger trigger. "
        "Produce a structured weekly activity report covering the past 7 days "
        "and save it as a draft to both Google Docs and Blogger. "
        "The Blogger post must remain as a DRAFT — do not publish it."
    )
}

@app.post("/trigger/{agent_type}")
async def trigger_agent(agent_type: str, request: Request):
    """
    Endpoint called by Cloud Scheduler (or local testing tools).
    Valid agent_types:
      - morning_feed
      - evening_digest
      - weekly_report
      - weekly_blogger
    """
    if agent_type not in TRIGGER_PROMPTS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid agent_type: '{agent_type}'. Must be one of {list(TRIGGER_PROMPTS.keys())}."
        )

    prompt = TRIGGER_PROMPTS[agent_type]
    print(f"\n🚀 Received trigger: {agent_type}")
    print(f"🤖 Running Agent (primary: {config.model_name} | fallback: {config.fallback_model_name})")
    
    events_collected = []
    try:
        # Execute the agent workflow, passing the prompt to the root coordinator
        async for event in run_agent_with_fallback(coordinator_agent, prompt):
            events_collected.append(str(event))
            print(f"Event: {event}")
            
        print(f"✅ Finished trigger: {agent_type}")
        return {
            "status": "success", 
            "agent_type": agent_type, 
            "message": "Trigger executed successfully", 
            "events_emitted": len(events_collected)
        }
        
    except Exception as e:
        print(f"❌ Error executing trigger {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok", 
        "model_primary": config.model_name,
        "model_fallback": config.fallback_model_name,
        "use_vertexai": config.USE_VERTEXAI
    }

if __name__ == "__main__":
    import uvicorn
    # When running locally via `python src/main.py`
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
