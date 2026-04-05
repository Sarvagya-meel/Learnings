# Quick Start: QNA Specialist with MCP Memory

## 🚀 5-Minute Setup

### 1. Get MCP Server Endpoint

```bash
cd Servers/agentcore-memory-mcp
agentcore list
# Copy the endpoint URL
```

### 2. Configure Environment

```bash
cd Agents/agentcore-qna-specialist-agent
cp .env.example .env
# Edit .env with your GROQ_API_KEY and MCP_MEMORY_SERVER_URL
```

### 3. Test Locally

```bash
python3.13 -m venv .venv
source .venv/bin/activate
uv sync
python test_mcp_integration.py
```

### 4. Deploy

```bash
agentcore configure -e 03_agentcore_mcp_memory.py
agentcore deploy
agentcore launch --env GROQ_API_KEY=$GROQ_API_KEY --env MCP_MEMORY_SERVER_URL=$MCP_MEMORY_SERVER_URL
```

### 5. Test

```bash
agentcore invoke '{"prompt": "What is roaming?", "actor_id": "user1", "session_id": "sess1"}'
```

## 📋 What You Need

- ✅ MCP Memory Server deployed
- ✅ Groq API key
- ✅ Python 3.13+
- ✅ AWS credentials configured

## 🔧 Key Files

| File | Purpose |
|------|---------|
| `03_agentcore_mcp_memory.py` | Main agent code |
| `.env` | Configuration |
| `test_mcp_integration.py` | Local testing |
| `README_MCP_INTEGRATION.md` | Full docs |
| `DEPLOYMENT_GUIDE.md` | Deployment steps |

## 💡 Key Features

- 🧠 **Memory Context**: Retrieves previous conversations
- 💬 **Multi-Turn**: Maintains context across queries
- 👥 **Multi-User**: Separate contexts per actor/session
- 🔄 **Auto-Store**: Saves all interactions
- 📊 **Logging**: Full observability

## 🎯 Example Usage

```bash
# First query
agentcore invoke '{
  "prompt": "What are roaming charges?",
  "actor_id": "user123",
  "session_id": "session456"
}'

# Follow-up (uses memory)
agentcore invoke '{
  "prompt": "How do I activate it?",
  "actor_id": "user123",
  "session_id": "session456"
}'
```

## 🐛 Quick Troubleshooting

| Problem | Fix |
|---------|-----|
| Memory fails | Check MCP server URL |
| No context | Verify previous interactions stored |
| Deploy fails | Check Python 3.13+ installed |
| API errors | Verify Groq API key |

## 📚 More Info

- Full docs: `README_MCP_INTEGRATION.md`
- Deployment: `DEPLOYMENT_GUIDE.md`
- Updates: `UPDATES_SUMMARY.md`

---

**Ready to deploy?** Follow `DEPLOYMENT_GUIDE.md` for detailed steps.
