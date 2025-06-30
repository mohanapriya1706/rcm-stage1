from google.adk.agents import Agent, LlmAgent
from dotenv import load_dotenv

load_dotenv()

root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='npp_assistant',
    instruction='Help the user with understanding the Notice of Privacy Practices.',
)
