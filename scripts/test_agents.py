import os
import sys
import asyncio

# Ensure the src directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.coordinator import coordinator_agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def run_agent(prompt: str):
    session_service = InMemorySessionService()
    runner = Runner(agent=coordinator_agent, app_name="personal-assistant", session_service=session_service)
    session = await session_service.create_session(app_name="personal-assistant", user_id="user")
    
    new_message = types.Content(role='user', parts=[types.Part(text=prompt)])
    
    print("\n--- Running Agent (streaming events) ---")
    async for event in runner.run_async(user_id='user', session_id=session.id, new_message=new_message):
        print(f"Event: {event}")
    print("---------------------------------")

async def main():
    print("🤖 Testing ADK Agents...")
    print("Which trigger would you like to simulate?")
    print("1. 7 AM Morning Trigger (Sends Morning Briefing Email)")
    print("2. 8 PM Evening Trigger (Drafts Journal in Google Docs)")
    
    choice = input("\nEnter 1 or 2: ")
    
    if choice == '1':
        print("\n🌅 Simulating 7 AM Morning Trigger...")
        await run_agent("It is 7:00 AM. Execute the morning trigger.")
        print("Check your email inbox!")
        
    elif choice == '2':
        print("\n🌙 Simulating 8 PM Evening Trigger...")
        await run_agent("It is 8:00 PM. Execute the evening trigger.")
        print("Check your Google Docs for the new draft!")
        
    else:
        print("Invalid choice.")

if __name__ == '__main__':
    asyncio.run(main())
