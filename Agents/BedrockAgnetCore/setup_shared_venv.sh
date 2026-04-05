#!/bin/bash
# Setup Shared Virtual Environment for All Projects

echo "Creating shared virtual environment..."

# Create shared venv at project root
python3 -m venv .venv

# Activate it
source .venv/bin/activate

echo "Installing dependencies from all projects..."

# Install QNA Agent dependencies
echo "Installing QNA Agent dependencies..."
pip install -r Agents/agentcore-qna-specialist-agent/pyproject.toml 2>/dev/null || \
cd Agents/agentcore-qna-specialist-agent && pip install -e . && cd ../..

# Install Supervisor Agent dependencies
echo "Installing Supervisor Agent dependencies..."
pip install -r Agents/agentcore-supervisor-agent/pyproject.toml 2>/dev/null || \
cd Agents/agentcore-supervisor-agent && pip install -e . && cd ../..

# Install MCP Server dependencies
echo "Installing MCP Server dependencies..."
pip install -r Servers/agentcore-memory-mcp/pyproject.toml 2>/dev/null || \
cd Servers/agentcore-memory-mcp && pip install -e . && cd ../..

echo ""
echo "✓ Shared venv created at: $(pwd)/.venv"
echo ""
echo "To use in PyCharm:"
echo "  1. Go to Settings → Project → Python Interpreter"
echo "  2. Add Existing Interpreter"
echo "  3. Select: $(pwd)/.venv/bin/python"
echo ""
echo "To activate in terminal:"
echo "  source .venv/bin/activate"
