# Google's Agent Development Kit.

As a reminder, ADK is a Python framework designed to streamline the development of applications powered by Large Language Models (LLMs). It offers robust building blocks for creating agents that can reason, plan, utilize tools, interact dynamically with users, and collaborate effectively within a team.
## How to run?
- It is designed to be run directly with commands like adk web (for a web UI), adk run (for CLI interaction), or adk api_server (to expose an API)
- To activate the Poetry-managed virtual environment manually from Command Prompt:

    ```
    venv\Scripts\activate
    ```
- Using the terminal, navigate to the parent directory of your agent project (e.g. using cd ..):
    ```
    parent_folder/      <-- navigate to this directory
        multi_tool_agent/
            __init__.py
            agent.py
            .env
    ```
- Run the following command to launch the dev UI:
    ```
    adk web
    ```
- Run the following command, to chat with your Weather agent in Terminal:
  ```
  adk run multi_tool_agent
  ```

## Core Concept
* Agent: The fundamental worker unit designed for specific tasks. Agents can use language models (LlmAgent) for complex reasoning, or act as deterministic controllers of the execution, which are called "workflow agents" (SequentialAgent, ParallelAgent, LoopAgent).