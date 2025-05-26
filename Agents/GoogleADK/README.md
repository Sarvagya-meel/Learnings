# Google's Agent Development Kit (ADK).

### 📦 How to run the agent?

To run a agent with adk agent debugger the main file must only be named agent.py(limitation from sdk as of now).

#### Create a ``__init__.py`` with content sas below:

```
from . import agent
```

#### Open terminal and navigate to folder containing the `agent.py`
```
cd ./Agents/GoogleADK/adk_learning_01/math_agent/

```

#### Run below command:
```
adk web
```