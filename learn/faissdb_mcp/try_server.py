import os
import asyncio
import logging
from dotenv import load_dotenv
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseConnectionParams, StdioServerParameters

load_dotenv('agent.env',override=True)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise EnvironmentError("Missing GEMINI_API_KEY in environment.")


PATH_TO_YOUR_MCP_SERVER_SCRIPT = os.path.abspath("faiss_server.py")
if not os.path.isfile(PATH_TO_YOUR_MCP_SERVER_SCRIPT):
    raise FileNotFoundError(f"MCP server script not found at {PATH_TO_YOUR_MCP_SERVER_SCRIPT}")

connection_params  = SseConnectionParams(
    url="http://127.0.0.1:4200/rag_query"
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Step 1: Agent Definition ---
async def get_agent_async():
    """Creates an ADK Agent equipped with tools from the MCP Server."""
    logger.debug("Setting up MCP toolset connection...")

    # Log script path being passed to the MCP server
    logger.debug(f"Using MCP server script at: {PATH_TO_YOUR_MCP_SERVER_SCRIPT}")


    try:
        toolset = MCPToolset(
            connection_params=connection_params
        )

        logger.debug("MCP toolset initialized successfully.")
    except Exception as e:
        logger.exception("Failed to initialize MCP toolset.")
        raise

    try:
        root_agent = LlmAgent(
            model='gemini-2.0-flash',
            name='rag_mcp_client',
            instruction="Use the 'rag_query' tool to fetch content provided by the user.",
            tools=[toolset]
        )
        logger.debug("LLM Agent created successfully.")
    except Exception as e:
        logger.exception("Failed to create root LLM Agent.")
        raise

    return root_agent, toolset


async def async_main():
    logger.info("Starting async_main()")

    session_service = InMemorySessionService()

    try:
        session = await session_service.create_session(
            state={}, app_name='testing', user_id='user_fs'
        )
        logger.debug(f"Session created: id={session.id}, user_id={session.user_id}")
    except Exception as e:
        logger.exception("Failed to create session.")
        return

    query = "what is the effective date of this npp?"
    logger.info(f"User Query: '{query}'")
    content = types.Content(role='user', parts=[types.Part(text=query)])

    try:
        root_agent, toolset = await get_agent_async()
    except Exception as e:
        logger.exception("Failed to initialize agent or toolset.")
        return

    try:
        runner = Runner(
            app_name='testing',
            agent=root_agent,
            session_service=session_service,
        )
        logger.debug("Runner initialized successfully.")
    except Exception as e:
        logger.exception("Failed to initialize runner.")
        return

    logger.info("Running agent...")
    try:
        events_async = runner.run_async(
            session_id=session.id, user_id=session.user_id, new_message=content
        )

        async for event in events_async:
            logger.info(f"Event received: {event}")

    except Exception as e:
        logger.exception("Error while running agent or receiving events.")

    logger.info("Closing MCP server connection...")
    try:
        await toolset.close()
        logger.debug("MCP toolset connection closed successfully.")
    except Exception as e:
        logger.exception("Error while closing MCP toolset connection.")

    logger.info("Cleanup complete.")

if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        logger.exception("Fatal error occurred in __main__.")