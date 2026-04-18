"""
CLI entrypoint
Supports direct interaction with the Agent from the command line for local debugging
"""
import argparse
import asyncio
import logging
import sys
import uuid

from app.config.settings import get_settings
from app.graph.graph import get_graph
from app.monitoring.logger import setup_logging
from app.skills.base import skill_registry
from app.skills.controlm_skill import ControlMSkill
from app.skills.playwright_skill import PlaywrightSkill
from app.state.agent_state import AgentState


def _init():
    """Initialize logging and skills"""
    settings = get_settings()
    setup_logging(settings.monitoring.log_level, "text")
    skill_registry.register(ControlMSkill())
    skill_registry.register(PlaywrightSkill())


async def run_single(message: str, session_id: str, stream: bool) -> None:
    """Execute a single conversation turn"""
    graph = get_graph()
    state = AgentState(
        session_id=session_id,
        user_input=message,
    )
    config = {"configurable": {"thread_id": session_id}}

    if stream:
        print("\n[Agent Streaming Response]")
        async for event in graph.astream_events(state, config=config, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk:
                    print(chunk, end="", flush=True)
        print("\n")
    else:
        result = await graph.ainvoke(state, config=config)
        print(f"\n[Agent Response]\n{result.get('final_response', '(no response)')}\n")
        if result.get("current_skill"):
            print(f"[Executed Skill] {result['current_skill']}")
        if result.get("error"):
            print(f"[Error] {result['error']}", file=sys.stderr)


async def interactive_mode(session_id: str) -> None:
    """Interactive conversation mode"""
    print(f"\n🤖 LangGraph Agent interactive mode (session: {session_id})")
    print("Type 'quit' or 'exit' to exit\n")
    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        await run_single(user_input, session_id, stream=False)


def main():
    parser = argparse.ArgumentParser(
        description="LangGraph Enterprise Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.cli chat "Query status of Control-M job MyJob"
  python -m app.cli chat "Take screenshot of Baidu homepage" --stream
  python -m app.cli interactive
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # single conversation
    chat_parser = subparsers.add_parser("chat", help="Single conversation")
    chat_parser.add_argument("message", help="User message")
    chat_parser.add_argument("--session-id", default=None, help="Session ID")
    chat_parser.add_argument("--stream", action="store_true", help="Stream output")

    # interactive mode
    interactive_parser = subparsers.add_parser("interactive", help="Interactive chat")
    interactive_parser.add_argument("--session-id", default=None)

    # list skills
    subparsers.add_parser("skills", help="List all registered skills")

    args = parser.parse_args()
    _init()

    if args.command == "skills":
        print("\nRegistered skills:")
        for skill in skill_registry.get_all_skills().values():
            print(f"  - {skill.name}: {skill.description}")
        return

    session_id = getattr(args, "session_id", None) or str(uuid.uuid4())

    if args.command == "chat":
        asyncio.run(run_single(args.message, session_id, args.stream))
    elif args.command == "interactive":
        asyncio.run(interactive_mode(session_id))


if __name__ == "__main__":
    main()
