"""
QNA Specialist Agent with MCP Memory Integration
Author: Updated for MCP Memory Server Integration
Date: 2026-02-17

This agent:
1. Answers FAQ questions using a knowledge base
2. Retrieves conversation context from MCP Memory Server
3. Stores interactions back to MCP Memory Server
4. Supports actor_id and session_id for multi-user scenarios
"""

import csv
import os
import json
import logging
import itertools
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from urllib.parse import quote

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain.agents import create_agent
from dotenv import load_dotenv

# Import AgentCore runtime
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Create the AgentCore app instance
app = BedrockAgentCoreApp()

_ = load_dotenv()

# JSON-RPC ID counter
_jsonrpc_id = itertools.count(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("qna.specialist")

# Configuration
MCP_MEMORY_SERVER_ARN = os.getenv(
    "MCP_MEMORY_SERVER_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_ACTOR_ID = "qna-specialist-user"
DEFAULT_SESSION_ID = "default-session"


# ============================================================================
# MCP Memory Client using JSON-RPC over HTTP with AWS SigV4
# ============================================================================

class MCPMemoryClient:
    """Client for interacting with MCP Memory Server via JSON-RPC"""
    
    def __init__(self, server_arn: str, region: str = "us-east-1", 
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None):
        self.server_arn = server_arn
        self.region = region
        
        # Build the invocation URL
        encoded_arn = quote(server_arn, safe='')
        self.invoke_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        
        # Get AWS credentials - use provided credentials or fall back to boto3 session
        if aws_access_key_id and aws_secret_access_key:
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region
            )
        else:
            session = boto3.Session(region_name=region)
        
        self.credentials = session.get_credentials()
        
        if not self.credentials:
            logger.error("No AWS credentials found! Please configure AWS credentials.")
            raise ValueError("AWS credentials are required but not found")
        
        logger.info(f"Initialized MCP client for ARN: {server_arn}")
        logger.info(f"Using AWS Access Key: {self.credentials.access_key[:8]}...")
    
    def _jsonrpc_call(self, method: str, params: Dict[str, Any], timeout: float = 30.0) -> Any:
        """Make a JSON-RPC call to the MCP server with AWS SigV4 authentication"""
        payload = {
            "jsonrpc": "2.0",
            "id": next(_jsonrpc_id),
            "method": method,
            "params": params,
        }
        body = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        # Create and sign the request
        request = AWSRequest(method="POST", url=self.invoke_url, data=body, headers=headers)
        SigV4Auth(self.credentials, "bedrock-agentcore", self.region).add_auth(request)
        
        # Execute the request
        response = requests.post(
            self.invoke_url,
            headers=dict(request.headers),
            data=body,
            timeout=timeout
        )
        response.raise_for_status()
        
        # Parse response (handle SSE format)
        resp_text = response.text.strip()
        
        # Handle SSE format (data: {...})
        if resp_text.startswith("data:"):
            data_lines = []
            for line in resp_text.splitlines():
                if not line.strip():
                    break
                if line.startswith("data:"):
                    data_lines.append(line[len("data:"):].lstrip())
            resp_text = "\n".join(data_lines)
        
        resp_json = json.loads(resp_text)
        
        if resp_json.get("error"):
            raise Exception(f"JSON-RPC error: {resp_json['error']}")
        
        return resp_json.get("result", {})
    
    async def retrieve_memory(
        self,
        query: str,
        actor_id: str,
        session_id: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve memories from MCP server"""
        try:
            logger.info(f"Retrieving memory for actor={actor_id}, session={session_id}")
            
            # Call the retrieve_memory tool via JSON-RPC
            result = self._jsonrpc_call(
                "tools/call",
                {
                    "name": "retrieve_memory",
                    "arguments": {
                        "query": query,
                        "max_results": max_results,
                        "actor_id": actor_id,
                        "session_id": session_id
                    }
                }
            )
            
            # Parse the tool response
            # Result structure: {structuredContent: {result: {content: [{text: "..."}]}}}
            content = result.get("structuredContent", {}).get("result", {}).get("content", [{}])
            if content:
                text = content[0].get("text", "{}")
                data = json.loads(text) if isinstance(text, str) else text
                
                items = data.get("data", {}).get("items", [])
                logger.info(f"Retrieved {len(items)} memories")
                return items
            
            return []
            
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}", exc_info=True)
            return []
    
    async def store_interaction(
        self,
        user_msg: str,
        assistant_msg: str,
        actor_id: str,
        session_id: str
    ) -> bool:
        """Store interaction in MCP server"""
        try:
            logger.info(f"Storing interaction for actor={actor_id}, session={session_id}")
            
            # Call the store_interaction tool via JSON-RPC
            result = self._jsonrpc_call(
                "tools/call",
                {
                    "name": "store_interaction",
                    "arguments": {
                        "user_msg": user_msg,
                        "assistant_msg": assistant_msg,
                        "actor_id": actor_id,
                        "session_id": session_id
                    }
                }
            )
            
            # Parse the tool response
            content = result.get("structuredContent", {}).get("result", {}).get("content", [{}])
            if content:
                text = content[0].get("text", "{}")
                data = json.loads(text) if isinstance(text, str) else text
                
                stored = data.get("data", {}).get("stored", False)
                if stored:
                    logger.info("Interaction stored successfully")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Memory storage failed: {e}", exc_info=True)
            return False


# Initialize MCP Memory Client
mcp_client = MCPMemoryClient(
    MCP_MEMORY_SERVER_ARN, 
    AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


# ============================================================================
# FAQ Knowledge Base
# ============================================================================

def load_faq_csv(path: str) -> List[Document]:
    """Load FAQ data from CSV file"""
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = row["question"].strip()
            a = row["answer"].strip()
            docs.append(Document(page_content=f"Q: {q}\nA: {a}"))
    return docs


# Load and index FAQ data
docs = load_faq_csv("./lauki_qna.csv")
emb = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
)
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
chunks = splitter.split_documents(docs)
faq_store = FAISS.from_documents(chunks, emb)


# ============================================================================
# Agent Tools
# ============================================================================

@tool
def search_faq(query: str) -> str:
    """Search the FAQ knowledge base for relevant information.
    Use this tool when the user asks questions about products, services, or policies.
    
    Args:
        query: The search query to find relevant FAQ entries
        
    Returns:
        Relevant FAQ entries that might answer the question
    """
    results = faq_store.similarity_search(query, k=3)
    
    if not results:
        return "No relevant FAQ entries found."
    
    context = "\n\n---\n\n".join([
        f"FAQ Entry {i+1}:\n{doc.page_content}" 
        for i, doc in enumerate(results)
    ])
    
    return f"Found {len(results)} relevant FAQ entries:\n\n{context}"


@tool
def search_detailed_faq(query: str, num_results: int = 5) -> str:
    """Search the FAQ knowledge base with more results for complex queries.
    Use this when the initial search doesn't provide enough information.
    
    Args:
        query: The search query
        num_results: Number of results to retrieve (default: 5)
        
    Returns:
        More comprehensive FAQ entries
    """
    results = faq_store.similarity_search(query, k=num_results)
    
    if not results:
        return "No relevant FAQ entries found."
    
    context = "\n\n---\n\n".join([
        f"FAQ Entry {i+1}:\n{doc.page_content}" 
        for i, doc in enumerate(results)
    ])
    
    return f"Found {len(results)} detailed FAQ entries:\n\n{context}"


@tool
def reformulate_query(original_query: str, focus_aspect: str) -> str:
    """Reformulate the query to focus on a specific aspect.
    Use this when you need to search for a different angle of the question.
    
    Args:
        original_query: The original user question
        focus_aspect: The specific aspect to focus on (e.g., "pricing", "activation", "troubleshooting")
        
    Returns:
        A reformulated query focused on the specified aspect
    """
    reformulated = f"{focus_aspect} related to {original_query}"
    results = faq_store.similarity_search(reformulated, k=3)
    
    if not results:
        return f"No results found for aspect: {focus_aspect}"
    
    context = "\n\n---\n\n".join([
        f"Entry {i+1}:\n{doc.page_content}" 
        for i, doc in enumerate(results)
    ])
    
    return f"Results for '{focus_aspect}' aspect:\n\n{context}"


tools = [search_faq, search_detailed_faq, reformulate_query]


# ============================================================================
# LLM and Agent Configuration
# ============================================================================

model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=GROQ_API_KEY
)

system_prompt = """You are a helpful FAQ assistant with access to a knowledge base and conversation memory.

Your goal is to answer user questions accurately using the available tools while considering previous conversation context.

Guidelines:
1. Consider any previous conversation context provided to personalize your response
2. Use the search_faq tool to find relevant information from the knowledge base
3. If the initial search doesn't provide enough info, use search_detailed_faq for more results
4. If the query is complex, use reformulate_query to search different aspects
5. Synthesize information from multiple tool calls if needed
6. Always provide a clear, concise answer based on the retrieved information
7. If you cannot find relevant information, clearly state that
8. Reference previous context when relevant to show continuity

Think step-by-step and use tools strategically to provide the best answer."""

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt
)


# ============================================================================
# Helper Functions
# ============================================================================

def format_memory_context(memories: List[Dict[str, Any]]) -> str:
    """Format retrieved memories into a readable context string"""
    if not memories:
        return ""
    
    lines = []
    for mem in memories:
        content = mem.get("content", "")
        strategy = mem.get("strategy", "")
        relevance = mem.get("relevance", 0.0)
        
        if content:
            lines.append(f"- {content} (relevance: {relevance:.2f})")
    
    if lines:
        return "Previous conversation context:\n" + "\n".join(lines)
    return ""


async def process_query_with_memory(
    query: str,
    actor_id: str,
    session_id: str
) -> Dict[str, Any]:
    """Process a query with memory retrieval and storage"""
    
    # Step 1: Retrieve memory context
    logger.info(f"Processing query for actor={actor_id}, session={session_id}")
    memories = await mcp_client.retrieve_memory(
        query=query,
        actor_id=actor_id,
        session_id=session_id,
        max_results=5
    )
    
    # Step 2: Format memory context
    memory_context = format_memory_context(memories)
    
    # Step 3: Build the full prompt with memory context
    if memory_context:
        full_prompt = f"{memory_context}\n\nCurrent question: {query}"
        logger.info("Using memory context in query")
    else:
        full_prompt = query
        logger.info("No memory context available")
    
    # Step 4: Invoke the agent
    result = agent.invoke({"messages": [("human", full_prompt)]})
    
    # Step 5: Extract the response
    messages = result.get("messages", [])
    answer = messages[-1].content if messages else "No response generated"
    
    # Step 6: Store the interaction
    store_success = await mcp_client.store_interaction(
        user_msg=query,
        assistant_msg=answer,
        actor_id=actor_id,
        session_id=session_id
    )
    
    return {
        "result": answer,
        "actor_id": actor_id,
        "session_id": session_id,
        "memory_used": len(memories) > 0,
        "memory_stored": store_success
    }


# ============================================================================
# AgentCore Entrypoint
# ============================================================================

@app.entrypoint
async def agent_invocation(payload, context):
    """Handler for agent invocation in AgentCore runtime with MCP memory support"""
    logger.info(f"Received payload: {payload}")
    logger.info(f"Context: {context}")
    
    try:
        # Extract query from payload
        query = payload.get("prompt", payload.get("query", "No prompt found in input"))
        
        # Extract or generate actor_id and session_id
        actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
        session_id = payload.get("session_id", payload.get("thread_id", DEFAULT_SESSION_ID))
        
        # Process the query with memory
        response = await process_query_with_memory(query, actor_id, session_id)
        
        logger.info(f"Response generated: memory_used={response['memory_used']}, memory_stored={response['memory_stored']}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        return {
            "result": "I apologize, but I encountered an error processing your request. Please try again.",
            "error": str(e),
            "actor_id": payload.get("actor_id", DEFAULT_ACTOR_ID),
            "session_id": payload.get("session_id", DEFAULT_SESSION_ID)
        }


if __name__ == "__main__":
    app.run()
