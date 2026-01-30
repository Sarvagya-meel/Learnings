# Google's Agent Development Kit.

As a reminder, ADK is a Python framework designed to streamline the development of applications powered by Large Language Models (LLMs). It offers robust building blocks for creating agents that can reason, plan, utilize tools, interact dynamically with users, and collaborate effectively within a team.

ADK makes switching between models seamless through its integration with the LiteLLM library. LiteLLM acts as a consistent interface to over 100 different LLMs.
* Performance: Some models excel at specific tasks (e.g., coding, reasoning, creative writing).
* Cost: Different models have varying price points.
* Capabilities: Models offer diverse features, context window sizes, and fine-tuning options.
* Availability/Redundancy: Having alternatives ensures your application remains functional even if one provider experiences issues.

## 📦 How to run the agent?

- To run an agent with adk agent debugger, the main file must only be named agent.py (limitation from sdk as of now).
- Create a ``__init__.py`` with content sas below:
    ```
    from . import agent
    ```
- Using the terminal, navigate to the parent directory of your agent project (e.g., using `cd ..`):
    ```
    parent_folder/      <-- navigate to this directory
        multi_tool_agent/
            __init__.py
            agent.py
            .env
    ```
- It is designed to be run directly with commands like adk web (for a web UI), adk run (for CLI interaction), or adk api_server (to expose an API)
- Run the following command to launch the dev UI:
    ```
    adk web
    ```
- Run the following command, to chat with your Weather agent in Terminal:
  ```
  adk run multi_tool_agent
  ```

## Core Concept

1. A Tool: A Python function that equips the agent with the ability to fetch weather data.
   * Key Concept: Docstrings are Crucial! The agent's LLM relies heavily on the function's docstring to understand:
     * What the tool does.
     * When to use it.
     * What arguments it requires (city: str).
     * What information it returns.
   * Best Practice: Write clear, descriptive, and accurate docstrings for your tools. This is essential for the LLM to use the tool correctly
2. Agent: The fundamental worker unit designed for specific tasks. Agents can use language models (LlmAgent) for complex reasoning, or act as deterministic controllers of the execution, which are called "workflow agents" (SequentialAgent, ParallelAgent, LoopAgent).The AI "brain" that understands the user's request, knows it has a weather tool, and decides when and how to use it.
   * We configure it with several key parameters:
     * name: A unique identifier for this agent (e.g., "weather_agent_v1").
     * model: Specifies which LLM to use (e.g., MODEL_GEMINI_2_0_FLASH). We'll start with a specific Gemini model.
     * description: A concise summary of the agent's overall purpose. This becomes crucial later when other agents need to decide whether to delegate tasks to this agent.
     * instruction: Detailed guidance for the LLM on how to behave, its persona, its goals, and specifically how and when to utilize its assigned tools.
     * tools: A list containing the actual Python tool functions the agent is allowed to use (e.g., [get_weather]).
   * Best Practice: Provide clear and specific instruction prompts. The more detailed the instructions, the better the LLM can understand its role and how to use its tools effectively. Be explicit about error handling if needed.
   * Best Practice: Choose descriptive name and description values. These are used internally by ADK and are vital for features like automatic delegation (covered later).
3. Setup Runner and Session Service
   * To manage conversations and execute the agent, we need two more components:
     * SessionService: Responsible for managing conversation history and state for different users and sessions. The InMemorySessionService is a simple implementation that stores everything in memory, suitable for testing and simple applications. It keeps track of the messages exchanged. We'll explore state persistence more in Step 4.
     * Runner: The engine that orchestrates the interaction flow. It takes user input, routes it to the appropriate agent, manages calls to the LLM and tools based on the agent's logic, handles session updates via the SessionService, and yields events representing the progress of the interaction.
4. Interact with the Agent
   * We need a way to send messages to our agent and receive its responses. Since LLM calls and tool executions can take time, ADK's Runner operates asynchronously.
   * We'll define an async helper function (call_agent_async) that:
     * Take a user query string. 
     * Package it into the ADK Content format. 
     * Calls runner.run_async, providing the user/session context and the new message. 
     * Iterates through the Events yielded by the runner. Events represent steps in the agent's execution (e.g., tool call requested, a tool result received, intermediate LLM thought, final response). 
     * Identifies and prints the final response event using event.is_final_response(). 
   * Why async? Interactions with LLMs and potential tools (like external APIs) are I/O-bound operations. Using asyncio allows the program to handle these operations efficiently without blocking execution.
5. Run the Conversation
   * Finally, let's test our setup by sending a few queries to the agent. We wrap our async calls in a main async function and run it using await. 
   * Watch the output:
     * See the user queries. 
     * Notice the --- Tool: get_weather called... --- logs when the agent uses the tool. 
     * Observe the agent's final responses, including how it handles the case where weather data isn't available (for Paris).