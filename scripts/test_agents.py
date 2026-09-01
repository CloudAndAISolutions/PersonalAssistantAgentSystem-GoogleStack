import os
import sys
import asyncio

# Ensure the src directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.coordinator import coordinator_agent
from src.services.runner_utils import run_agent_with_fallback
from src.services.config import config

async def run_agent(prompt: str):
    print(f"\n--- Running Agent (primary: {config.model_name} | fallback: {config.fallback_model_name}) ---")
    async for event in run_agent_with_fallback(coordinator_agent, prompt):
        print(f"Event: {event}")
    print("---------------------------------")

async def main():
    print("🤖 Testing ADK Agents...")
    print("Which trigger would you like to simulate?")
    print("1. 7 AM Morning Trigger        (Sends Morning Briefing Email)")
    print("2. 8 PM Evening Trigger        (Daily Journal draft → Google Docs)")
    print("3. Weekly Report Trigger       (Weekly report draft → Google Docs)")
    print("4. Weekly Blogger Post         (Weekly report draft → Google Docs + Blogger)")

    choice = input("\nEnter 1, 2, 3, or 4: ").strip()

    if choice == '1':
        print("\n🌅 Simulating 7 AM Morning Trigger...")
        await run_agent("It is 7:00 AM. Execute the morning trigger.")
        print("Check your email inbox!")

    elif choice == '2':
        print("\n🌙 Simulating 8 PM Evening Trigger...")
        await run_agent("It is 8:00 PM. Execute the evening trigger.")
        print("Check your Google Docs for the new daily journal draft!")

    elif choice == '3':
        print("\n📊 Simulating Weekly Report Trigger (Google Docs only)...")
        await run_agent(
            "It is Sunday 8:00 PM. Execute the weekly_report trigger. "
            "Produce a structured weekly activity report covering the past 7 days. "
            "Use any available context about recent calendar events, emails, and tasks."
        )
        print("Check your Google Docs for the new weekly report draft!")

    elif choice == '4':
        print("\n📝 Simulating Weekly Blogger Post (Google Docs + Blogger draft)...")
        await run_agent(
            "It is Sunday 8:00 PM. Execute the weekly_blogger trigger. "
            "Produce a structured weekly activity report covering the past 7 days "
            "and save it as a draft to both Google Docs and Blogger. "
            "The Blogger post must remain as a DRAFT — do not publish it."
        )
        print("Check Google Docs and your Blogger dashboard (Drafts) for the new post!")
        print("⚠️  Note: Blogger requires BLOGGER_BLOG_ID to be set in .env")

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == '__main__':
    asyncio.run(main())
