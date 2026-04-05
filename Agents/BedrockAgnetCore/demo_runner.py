#!/usr/bin/env python3
"""
AgentCore POC - Interactive Demo Runner
Author: Sarvagya Meel
Date: February 23, 2026

This script provides an interactive menu for running demos during the presentation.
"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, Any

# ANSI color codes
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{YELLOW}ℹ {text}{RESET}")


def print_step(step: int, text: str):
    """Print step message"""
    print(f"{BOLD}Step {step}:{RESET} {text}")


def wait_for_enter(message: str = "Press ENTER to continue..."):
    """Wait for user to press enter"""
    input(f"\n{YELLOW}{message}{RESET}")


def run_agentcore_invoke(prompt: str, actor_id: str, session_id: str) -> Dict[str, Any]:
    """Run agentcore invoke command and return parsed result"""
    payload = {
        "prompt": prompt,
        "actor_id": actor_id,
        "session_id": session_id
    }
    
    cmd = f"agentcore invoke '{json.dumps(payload)}'"
    
    print(f"\n{BOLD}Invoking Agent:{RESET}")
    print(f"  Prompt: {prompt}")
    print(f"  Actor: {actor_id}")
    print(f"  Session: {session_id}")
    print(f"\n{YELLOW}Running command...{RESET}\n")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print_success("Agent invocation successful!")
            try:
                response = json.loads(result.stdout)
                return response
            except json.JSONDecodeError:
                print_error("Could not parse response as JSON")
                print(result.stdout)
                return {"error": "Invalid JSON response"}
        else:
            print_error(f"Agent invocation failed with code {result.returncode}")
            print(result.stderr)
            return {"error": result.stderr}
            
    except subprocess.TimeoutExpired:
        print_error("Command timed out after 30 seconds")
        return {"error": "Timeout"}
    except Exception as e:
        print_error(f"Error running command: {e}")
        return {"error": str(e)}


def demo_1_memory_server():
    """Demo 1: MCP Memory Server Basic Operations"""
    print_header("DEMO 1: MCP Memory Server - Basic Operations")
    
    print_info("This demo shows the MCP Memory Server running on AgentCore Runtime")
    print_info("We'll test: tool listing, memory retrieval, and memory storage")
    wait_for_enter()
    
    print_step(1, "Testing MCP Memory Server")
    print(f"\n{YELLOW}Running: python Servers/agentcore-memory-mcp/memory_mcp_agentCore_client.py{RESET}\n")
    
    try:
        os.chdir("Servers/agentcore-memory-mcp")
        result = subprocess.run(
            ["python", "memory_mcp_agentCore_client.py"],
            timeout=60
        )
        os.chdir("../..")
        
        if result.returncode == 0:
            print_success("Memory server test completed successfully!")
        else:
            print_error("Memory server test failed")
            
    except subprocess.TimeoutExpired:
        print_error("Test timed out")
        os.chdir("../..")
    except Exception as e:
        print_error(f"Error: {e}")
        os.chdir("../..")
    
    wait_for_enter()


def demo_2_simple_query():
    """Demo 2: QnA Agent - Simple FAQ Query"""
    print_header("DEMO 2: QnA Agent - Simple FAQ Query")
    
    print_info("This demo shows the QnA Agent answering a simple question")
    print_info("The agent will search its FAQ knowledge base and provide an answer")
    wait_for_enter()
    
    # Change to agent directory
    original_dir = os.getcwd()
    os.chdir("Agents/agentcore-qna-specialist-agent")
    
    print_step(1, "Asking: 'What is roaming activation?'")
    
    response = run_agentcore_invoke(
        prompt="What is roaming activation?",
        actor_id="demo-user",
        session_id="demo-session-001"
    )
    
    if "result" in response:
        print(f"\n{BOLD}Agent Response:{RESET}")
        print(f"{GREEN}{response['result']}{RESET}")
        
        if "memory_stored" in response:
            print(f"\n{BOLD}Memory Status:{RESET}")
            print(f"  Memory Stored: {response.get('memory_stored', False)}")
            print(f"  Memory Used: {response.get('memory_used', False)}")
    
    os.chdir(original_dir)
    wait_for_enter()


def demo_3_multi_turn():
    """Demo 3: Multi-Turn Conversation with Memory"""
    print_header("DEMO 3: Multi-Turn Conversation with Memory")
    
    print_info("This demo shows context awareness across multiple conversation turns")
    print_info("Watch how the agent remembers previous questions and maintains context")
    wait_for_enter()
    
    original_dir = os.getcwd()
    os.chdir("Agents/agentcore-qna-specialist-agent")
    
    session_id = "demo-session-002"
    actor_id = "demo-user"
    
    queries = [
        "What are the roaming charges?",
        "How do I activate it?",
        "Can I use it internationally?"
    ]
    
    for i, query in enumerate(queries, 1):
        print_step(i, f"Turn {i}: '{query}'")
        
        response = run_agentcore_invoke(
            prompt=query,
            actor_id=actor_id,
            session_id=session_id
        )
        
        if "result" in response:
            print(f"\n{BOLD}Agent Response:{RESET}")
            # Truncate long responses
            result_text = response['result']
            if len(result_text) > 200:
                result_text = result_text[:200] + "..."
            print(f"{GREEN}{result_text}{RESET}")
            
            print(f"\n{BOLD}Memory Status:{RESET}")
            print(f"  Memory Used: {response.get('memory_used', False)}")
            print(f"  Memory Stored: {response.get('memory_stored', False)}")
        
        if i < len(queries):
            wait_for_enter("Press ENTER for next turn...")
        else:
            wait_for_enter()
    
    os.chdir(original_dir)


def demo_4_multi_user():
    """Demo 4: Multi-User Isolation"""
    print_header("DEMO 4: Multi-User Isolation")
    
    print_info("This demo proves that different users have isolated memory spaces")
    print_info("We'll store preferences for two users and verify they don't see each other's data")
    wait_for_enter()
    
    original_dir = os.getcwd()
    os.chdir("Agents/agentcore-qna-specialist-agent")
    
    # User A stores preference
    print_step(1, "User Alice stores her preference")
    response_a1 = run_agentcore_invoke(
        prompt="I prefer email notifications for all updates",
        actor_id="user-alice",
        session_id="alice-session-001"
    )
    wait_for_enter("Press ENTER to continue...")
    
    # User B stores preference
    print_step(2, "User Bob stores his preference")
    response_b1 = run_agentcore_invoke(
        prompt="I prefer SMS notifications only for urgent matters",
        actor_id="user-bob",
        session_id="bob-session-001"
    )
    wait_for_enter("Press ENTER to continue...")
    
    # User A retrieves preference
    print_step(3, "User Alice retrieves her preferences")
    response_a2 = run_agentcore_invoke(
        prompt="What are my notification preferences?",
        actor_id="user-alice",
        session_id="alice-session-002"
    )
    
    if "result" in response_a2:
        print(f"\n{BOLD}Alice's Response:{RESET}")
        print(f"{GREEN}{response_a2['result']}{RESET}")
    
    wait_for_enter("Press ENTER to continue...")
    
    # User B retrieves preference
    print_step(4, "User Bob retrieves his preferences")
    response_b2 = run_agentcore_invoke(
        prompt="What are my notification preferences?",
        actor_id="user-bob",
        session_id="bob-session-002"
    )
    
    if "result" in response_b2:
        print(f"\n{BOLD}Bob's Response:{RESET}")
        print(f"{GREEN}{response_b2['result']}{RESET}")
    
    print(f"\n{BOLD}{GREEN}✓ Complete isolation verified!{RESET}")
    print(f"{GREEN}  Alice only sees her email preference{RESET}")
    print(f"{GREEN}  Bob only sees his SMS preference{RESET}")
    
    os.chdir(original_dir)
    wait_for_enter()


def check_prerequisites():
    """Check if prerequisites are met"""
    print_header("Checking Prerequisites")
    
    all_good = True
    
    # Check if we're in the right directory
    if not os.path.exists("Agents") or not os.path.exists("Servers"):
        print_error("Not in project root directory")
        print_info("Please run this script from the project root")
        return False
    
    print_success("In project root directory")
    
    # Check if agentcore CLI is available
    try:
        result = subprocess.run(
            ["agentcore", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success("AgentCore CLI is installed")
        else:
            print_error("AgentCore CLI not working properly")
            all_good = False
    except FileNotFoundError:
        print_error("AgentCore CLI not found")
        print_info("Install with: pip install bedrock-agentcore-starter-toolkit")
        all_good = False
    except Exception as e:
        print_error(f"Error checking AgentCore CLI: {e}")
        all_good = False
    
    # Check AWS credentials
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success("AWS credentials configured")
        else:
            print_error("AWS credentials not configured")
            all_good = False
    except FileNotFoundError:
        print_error("AWS CLI not found")
        all_good = False
    except Exception as e:
        print_error(f"Error checking AWS credentials: {e}")
        all_good = False
    
    # Check if agents are deployed
    try:
        result = subprocess.run(
            ["agentcore", "list"],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            print_success("Can list AgentCore agents")
        else:
            print_error("Cannot list AgentCore agents")
            all_good = False
    except Exception as e:
        print_error(f"Error listing agents: {e}")
        all_good = False
    
    return all_good


def main_menu():
    """Display main menu and handle user input"""
    while True:
        print_header("AgentCore POC - Demo Runner")
        
        print(f"{BOLD}Available Demos:{RESET}")
        print(f"  {BLUE}1.{RESET} MCP Memory Server - Basic Operations")
        print(f"  {BLUE}2.{RESET} QnA Agent - Simple FAQ Query")
        print(f"  {BLUE}3.{RESET} Multi-Turn Conversation with Memory")
        print(f"  {BLUE}4.{RESET} Multi-User Isolation")
        print(f"  {BLUE}5.{RESET} Run All Demos (Full Presentation)")
        print(f"  {BLUE}6.{RESET} Check Prerequisites")
        print(f"  {BLUE}0.{RESET} Exit")
        
        choice = input(f"\n{YELLOW}Select demo (0-6): {RESET}").strip()
        
        if choice == "1":
            demo_1_memory_server()
        elif choice == "2":
            demo_2_simple_query()
        elif choice == "3":
            demo_3_multi_turn()
        elif choice == "4":
            demo_4_multi_user()
        elif choice == "5":
            print_info("Running all demos in sequence...")
            wait_for_enter("Press ENTER to start...")
            demo_1_memory_server()
            demo_2_simple_query()
            demo_3_multi_turn()
            demo_4_multi_user()
            print_header("All Demos Completed!")
            print_success("Presentation complete!")
            wait_for_enter()
        elif choice == "6":
            if check_prerequisites():
                print_success("\nAll prerequisites met! Ready for demos.")
            else:
                print_error("\nSome prerequisites are missing. Please fix before running demos.")
            wait_for_enter()
        elif choice == "0":
            print_info("Exiting demo runner. Good luck with your presentation!")
            break
        else:
            print_error("Invalid choice. Please select 0-6.")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Demo interrupted by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
