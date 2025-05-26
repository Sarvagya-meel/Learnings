from dotenv import load_dotenv
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService

load_dotenv()

session_service = InMemorySessionService()
MODEL_GPT_4O = "openai/gpt-4o"
MODEL_GPT_4O_LITE_LLM = LiteLlm(model=MODEL_GPT_4O)

instruction_prompt = """
You will add two numbers using a math addition tool
"""

# Define constants for identifying the interaction context
APP_NAME = "math_app"
USER_ID = "user_1"
SESSION_ID = "session_001"  # Using a fixed ID for simplicity

# Create the specific session where the conversation will happen
session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)


async def add(
        num_1: int,
        num_2: int
) :
    """Tool to call database (nl2sql) agent."""
    result = num_1 + num_2
    return result


math_agent = Agent(
    model=MODEL_GPT_4O_LITE_LLM,
    name="math_agent",
    instruction=instruction_prompt,
    global_instruction="",
    sub_agents=[],
    tools=[
        add
    ],
)

root_agent = math_agent