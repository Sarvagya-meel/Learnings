# PyCharm Virtual Environment Setup Guide

## Quick Setup - Add Existing venv to PyCharm

### Step 1: Open PyCharm Settings

**macOS:**
- Press `Cmd + ,` OR
- Click `PyCharm` → `Preferences`

**Windows/Linux:**
- Press `Ctrl + Alt + S` OR
- Click `File` → `Settings`

### Step 2: Navigate to Python Interpreter

1. In the left sidebar, expand `Project: BedrockAgnetCore`
2. Click on `Python Interpreter`

### Step 3: Add Existing Interpreter

1. Click the **gear icon ⚙️** (top right, next to the interpreter dropdown)
2. Select `Add Interpreter` → `Add Local Interpreter...`
3. In the dialog, select `Existing environment`
4. Click the **folder icon 📁** next to the Interpreter field

### Step 4: Select the venv Python Executable

Navigate to and select ONE of these paths:

#### For QNA Specialist Agent:
```
/Users/sameel/Documents/WorkSpace/Learnings/Agents/BedrockAgnetCore/Agents/agentcore-qna-specialist-agent/.venv/bin/python
```

#### For Supervisor Agent:
```
/Users/sameel/Documents/WorkSpace/Learnings/Agents/BedrockAgnetCore/Agents/agentcore-supervisor-agent/.venv/bin/python
```

#### For MCP Memory Server:
```
/Users/sameel/Documents/WorkSpace/Learnings/Agents/BedrockAgnetCore/Servers/agentcore-memory-mcp/.venv/bin/python
```

### Step 5: Apply and Verify

1. Click `OK` to close the Add Interpreter dialog
2. Click `OK` to close Settings
3. PyCharm will now index the packages (wait for it to finish)

### Step 6: Verify Installation

Open PyCharm's Python Console (bottom toolbar) and run:

```python
import sys
print(sys.executable)
print(sys.version)
```

You should see the path to your `.venv/bin/python`

---

## Alternative: Use PyCharm Terminal

If the GUI method doesn't work, use PyCharm's built-in terminal:

### Step 1: Open Terminal in PyCharm

- Click `View` → `Tool Windows` → `Terminal` OR
- Press `Alt + F12` (Windows/Linux) or `Option + F12` (macOS)

### Step 2: Activate the venv

```bash
# For QNA Agent
source Agents/agentcore-qna-specialist-agent/.venv/bin/activate

# For Supervisor Agent
source Agents/agentcore-supervisor-agent/.venv/bin/activate

# For MCP Server
source Servers/agentcore-memory-mcp/.venv/bin/activate
```

### Step 3: Verify

```bash
which python
python --version
pip list
```

---

## Create Shared venv (Optional)

If you want ONE venv for all projects:

### Step 1: Run the setup script

```bash
chmod +x setup_shared_venv.sh
./setup_shared_venv.sh
```

### Step 2: Add to PyCharm

Follow Steps 1-3 above, then select:
```
/Users/sameel/Documents/WorkSpace/Learnings/Agents/BedrockAgnetCore/.venv/bin/python
```

---

## Troubleshooting

### Issue: "No Python interpreter configured"

**Solution:**
1. Make sure the venv exists: `ls -la Agents/agentcore-qna-specialist-agent/.venv/bin/python`
2. If not, create it: `cd Agents/agentcore-qna-specialist-agent && python3 -m venv .venv`

### Issue: "Cannot find python executable"

**Solution:**
The path might be slightly different. Try:
```bash
# Find the exact path
find . -name "python" -path "*/.venv/bin/*" 2>/dev/null
```

Then use the full path shown.

### Issue: PyCharm doesn't recognize installed packages

**Solution:**
1. Go to `File` → `Invalidate Caches...`
2. Select `Invalidate and Restart`
3. Wait for PyCharm to re-index

### Issue: Want to switch between different venvs

**Solution:**
1. Click the Python version in the bottom-right status bar
2. Select `Interpreter Settings...`
3. Choose a different interpreter from the dropdown

---

## Quick Reference

### Activate venv in Terminal

```bash
# QNA Agent
source Agents/agentcore-qna-specialist-agent/.venv/bin/activate

# Supervisor Agent
source Agents/agentcore-supervisor-agent/.venv/bin/activate

# MCP Server
source Servers/agentcore-memory-mcp/.venv/bin/activate
```

### Deactivate venv

```bash
deactivate
```

### Install packages in venv

```bash
# Make sure venv is activated first
pip install package-name

# Or install from pyproject.toml
pip install -e .
```

### Check which venv is active

```bash
which python
echo $VIRTUAL_ENV
```

---

## Visual Guide

```
PyCharm Settings
├── Project: BedrockAgnetCore
│   └── Python Interpreter
│       └── ⚙️ (gear icon)
│           └── Add Interpreter
│               └── Add Local Interpreter
│                   └── Existing environment
│                       └── 📁 (folder icon)
│                           └── Navigate to .venv/bin/python
│                               └── OK
```

---

## Next Steps

After setting up the interpreter:

1. ✅ PyCharm will recognize all installed packages
2. ✅ Code completion will work
3. ✅ Import statements will be resolved
4. ✅ You can run/debug Python files directly
5. ✅ Terminal will auto-activate the venv

Enjoy coding! 🚀
