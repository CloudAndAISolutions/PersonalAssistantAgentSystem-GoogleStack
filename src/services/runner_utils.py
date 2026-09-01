"""
runner_utils.py — Model-fallback ADK runner utility.

Usage:
    from src.services.runner_utils import run_agent_with_fallback

    async for event in run_agent_with_fallback(coordinator_agent, prompt):
        print(event)

On first use, the primary model (config.model_name) is tried.
If the API returns a 503 UNAVAILABLE (high demand), ALL agents in the
sub-agent graph are patched to use config.fallback_model_name and the
run is retried automatically.
"""
import asyncio
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import BaseAgent
from google.genai.errors import ServerError
from google.genai import types
from src.services.config import config


def _patch_model(agent: BaseAgent, new_model: str):
    """Recursively patch the model name on every LlmAgent in the graph."""
    if hasattr(agent, 'model'):
        try:
            agent.model = new_model
        except Exception:
            pass  # SequentialAgent and similar don't have a model field — safe to skip
    for sub in getattr(agent, 'sub_agents', []) or []:
        _patch_model(sub, new_model)


async def run_agent_with_fallback(root_agent: BaseAgent, prompt: str):
    """Run root_agent with prompt, falling back to config.fallback_model_name on 503.

    Yields ADK Event objects from runner.run_async().
    Re-raises any non-503 errors.
    """
    for attempt, model in enumerate([config.model_name, config.fallback_model_name]):
        if attempt > 0:
            print(f"\n⚠️  Primary model returned 503. Retrying with fallback: {model} …\n")
            _patch_model(root_agent, model)

        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="personal-assistant",
            session_service=session_service
        )
        session = await session_service.create_session(
            app_name="personal-assistant", user_id="user"
        )
        new_message = types.Content(role='user', parts=[types.Part(text=prompt)])

        try:
            async for event in runner.run_async(
                user_id='user',
                session_id=session.id,
                new_message=new_message
            ):
                yield event
            return  # success — stop retrying

        except ServerError as e:
            if '503' in str(e) or 'UNAVAILABLE' in str(e):
                if attempt < 1:
                    continue  # retry with fallback
                # Exhausted all models
                raise RuntimeError(
                    f"Both models ({config.model_name} and {config.fallback_model_name}) "
                    f"returned 503. Please try again later.\n{e}"
                ) from e
            raise  # non-503 — propagate immediately
