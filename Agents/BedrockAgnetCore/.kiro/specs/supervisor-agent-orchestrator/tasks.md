# Implementation Plan: Supervisor Agent Orchestrator

## Overview

This implementation plan breaks down the supervisor agent orchestrator into discrete coding tasks. The approach follows a bottom-up strategy: build core components first (configuration, memory client, specialist client), then the routing engine, then the supervisor orchestrator, and finally the AgentCore runtime handler. Testing tasks are included as optional sub-tasks to allow for faster MVP development.

## Tasks

- [ ] 1. Set up project structure and dependencies
  - Create directory structure: `src/`, `tests/`, `config/`
  - Create `pyproject.toml` with dependencies: langchain, langgraph, groq, httpx, pydantic, python-dotenv, hypothesis, pytest
  - Create `.bedrock_agentcore.yaml` configuration file with runtime, handler, environment variables, and dependencies
  - Create `.env.example` file with all required and optional environment variables
  - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_

- [ ] 2. Implement configuration management
  - [ ] 2.1 Create configuration models and loader
    - Define `AgentConfig` Pydantic model with all configuration fields
    - Implement `ConfigManager.load()` to read from environment variables
    - Implement `ConfigManager.validate()` to check required fields
    - Handle missing required config with clear error messages
    - Provide defaults for optional configuration values
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ]* 2.2 Write property test for configuration validation
    - **Property 19: Configuration validation**
    - **Validates: Requirements 8.4**
  
  - [ ]* 2.3 Write unit tests for configuration loading
    - Test loading with all env vars present
    - Test loading with missing required env vars
    - Test default values for optional env vars
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 3. Implement MCP memory client
  - [ ] 3.1 Create memory client with retrieve and store methods
    - Define `MCPMemoryClient` class with async methods
    - Implement `retrieve_memory()` with httpx async client
    - Implement `store_interaction()` with httpx async client
    - Implement `get_server_info()` method
    - Add timeout handling and error catching
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 3.2 Write property test for memory operations using correct identifiers
    - **Property 6: Memory operations use correct identifiers**
    - **Validates: Requirements 2.2, 2.4**
  
  - [ ]* 3.3 Write property test for resilience to memory failures
    - **Property 8: Resilience to memory failures**
    - **Validates: Requirements 2.5, 5.2**
  
  - [ ]* 3.4 Write unit tests for memory client
    - Test successful retrieve and store operations
    - Test handling of network errors
    - Test timeout handling
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4. Implement specialist invocation client
  - [ ] 4.1 Create specialist client with retry logic
    - Define `SpecialistClient` class with async methods
    - Implement `invoke_qna_specialist()` with httpx
    - Implement `_retry_with_backoff()` with exponential backoff
    - Add timeout and error handling
    - _Requirements: 1.3, 5.1, 5.3_
  
  - [ ]* 4.2 Write property test for specialist invocation following routing
    - **Property 2: Specialist invocation follows routing decision**
    - **Validates: Requirements 1.3**
  
  - [ ]* 4.3 Write property test for LLM retry with exponential backoff
    - **Property 15: LLM retry with exponential backoff**
    - **Validates: Requirements 5.3**
  
  - [ ]* 4.4 Write property test for specialist failure fallback
    - **Property 14: Specialist failure fallback**
    - **Validates: Requirements 5.1**
  
  - [ ]* 4.5 Write unit tests for specialist client
    - Test successful specialist invocation
    - Test retry logic with simulated failures
    - Test exponential backoff timing
    - Test final failure after retries exhausted
    - _Requirements: 1.3, 5.1, 5.3, 5.4_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement routing engine
  - [ ] 6.1 Create query router with LLM-based routing
    - Define `QueryRouter` class with Groq LLM integration
    - Define `RoutingDecision` Pydantic model
    - Implement `route()` method that calls LLM with routing prompt
    - Implement `_build_routing_prompt()` to construct system and user prompts
    - Include memory context in routing prompts
    - Parse LLM response into RoutingDecision
    - _Requirements: 1.1, 1.2, 1.5, 6.1, 6.3_
  
  - [ ]* 6.2 Write property test for routing produces valid destinations
    - **Property 1: Routing produces valid destinations**
    - **Validates: Requirements 1.1**
  
  - [ ]* 6.3 Write property test for system prompts in LLM calls
    - **Property 18: System prompts in LLM calls**
    - **Validates: Requirements 6.3**
  
  - [ ]* 6.4 Write property test for memory context in specialist invocations
    - **Property 4: Memory context included in specialist invocations**
    - **Validates: Requirements 1.5**
  
  - [ ]* 6.5 Write unit tests for routing engine
    - Test routing FAQ queries to QNA specialist
    - Test routing general queries to direct response
    - Test prompt construction with memory context
    - Test LLM response parsing
    - _Requirements: 1.1, 1.2, 1.5, 6.3_

- [ ] 7. Implement core supervisor agent with LangGraph
  - [ ] 7.1 Define agent state and state machine
    - Define `AgentState` TypedDict with all required fields
    - Create LangGraph StateGraph with nodes for each workflow step
    - Define edges between nodes (retrieve_memory → route_query → invoke_specialist/direct_response → store_interaction)
    - Compile the graph into a runnable
    - _Requirements: 3.2, 3.4_
  
  - [ ] 7.2 Implement memory retrieval node
    - Implement `_retrieve_memory()` async function
    - Call MCPMemoryClient.retrieve_memory() with actor_id, session_id, query
    - Store retrieved memories in state.memory_context
    - Handle memory retrieval failures gracefully
    - _Requirements: 2.1, 2.2, 2.5_
  
  - [ ] 7.3 Implement routing node
    - Implement `_route_query()` async function
    - Call QueryRouter.route() with query and memory context
    - Store routing decision in state.routing_decision
    - _Requirements: 1.1, 1.2_
  
  - [ ] 7.4 Implement specialist invocation node
    - Implement `_invoke_specialist()` async function
    - Call SpecialistClient based on routing decision
    - Store specialist response in state.specialist_response
    - Handle specialist failures with fallback
    - _Requirements: 1.3, 1.5, 5.1_
  
  - [ ] 7.5 Implement direct response generation node
    - Implement `_generate_direct_response()` async function
    - Call Groq LLM to generate response using query and memory context
    - Store generated response in state.final_response
    - _Requirements: 1.4, 6.2_
  
  - [ ] 7.6 Implement interaction storage node
    - Implement `_store_interaction()` async function
    - Call MCPMemoryClient.store_interaction() with user query and assistant response
    - Include actor_id and session_id
    - Handle storage failures gracefully
    - _Requirements: 2.3, 2.4_
  
  - [ ] 7.7 Implement main process_query method
    - Create `SupervisorAgent` class with LangGraph integration
    - Implement `process_query()` that initializes state and invokes the graph
    - Handle actor_id and session_id defaults (generate if not provided)
    - Return AgentResponse with all relevant fields
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 7.8 Write property test for memory retrieval precedes response generation
    - **Property 5: Memory retrieval precedes response generation**
    - **Validates: Requirements 2.1**
  
  - [ ]* 7.9 Write property test for interaction storage after completion
    - **Property 7: Interaction storage after completion**
    - **Validates: Requirements 2.3**
  
  - [ ]* 7.10 Write property test for state persistence across workflow steps
    - **Property 9: State persistence across workflow steps**
    - **Validates: Requirements 3.2**
  
  - [ ]* 7.11 Write property test for error handling in workflow steps
    - **Property 10: Error handling in workflow steps**
    - **Validates: Requirements 3.4**
  
  - [ ]* 7.12 Write property test for actor ID handling
    - **Property 11: Actor ID handling**
    - **Validates: Requirements 4.1, 4.3**
  
  - [ ]* 7.13 Write property test for session ID handling
    - **Property 12: Session ID handling**
    - **Validates: Requirements 4.2, 4.4**
  
  - [ ]* 7.14 Write property test for session isolation
    - **Property 13: Session isolation**
    - **Validates: Requirements 4.5**
  
  - [ ]* 7.15 Write property test for direct response generation
    - **Property 3: Direct response generation for unrouted queries**
    - **Validates: Requirements 1.4, 6.2**

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement logging system
  - [ ] 9.1 Create structured logging configuration
    - Configure Python logging with JSON formatter
    - Set log level from environment variable
    - Add context fields (actor_id, session_id, request_id) to all logs
    - Create logger utility functions for each log type
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ] 9.2 Add logging to all supervisor components
    - Add logging to memory retrieval and storage operations
    - Add logging to routing decisions with reasoning
    - Add logging to specialist invocations
    - Add logging to error handling paths
    - Add logging to incoming queries
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 5.5_
  
  - [ ]* 9.3 Write property test for comprehensive logging
    - **Property 20: Comprehensive logging**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**
  
  - [ ]* 9.4 Write property test for structured logging format
    - **Property 21: Structured logging format**
    - **Validates: Requirements 9.5**
  
  - [ ]* 9.5 Write property test for error logging
    - **Property 17: Error logging**
    - **Validates: Requirements 5.5**

- [ ] 10. Implement error handling and resilience
  - [ ] 10.1 Add circuit breaker pattern for external services
    - Create `CircuitBreaker` class with open/closed/half-open states
    - Track consecutive failures per service
    - Open circuit after 5 failures, close after 60 seconds
    - Integrate with memory client and specialist client
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ] 10.2 Implement error response formatting
    - Define `ErrorResponse` Pydantic model
    - Create error code constants (ERR_MEMORY_001, etc.)
    - Implement error message sanitization (remove stack traces)
    - Add timestamp and request_id to error responses
    - _Requirements: 5.4, 10.3_
  
  - [ ]* 10.3 Write property test for error message after retry exhaustion
    - **Property 16: Error message after retry exhaustion**
    - **Validates: Requirements 5.4**
  
  - [ ]* 10.4 Write property test for error information in error responses
    - **Property 23: Error information in error responses**
    - **Validates: Requirements 10.3**

- [ ] 11. Implement response generation and formatting
  - [ ] 11.1 Create response models and formatting
    - Define `AgentResponse` Pydantic model
    - Implement response formatting for specialist outputs
    - Implement response formatting for direct responses
    - Implement response formatting for errors
    - Ensure consistent schema across all response types
    - _Requirements: 10.1, 10.4_
  
  - [ ]* 11.2 Write property test for specialist output in response
    - **Property 22: Specialist output in response**
    - **Validates: Requirements 10.1**
  
  - [ ]* 11.3 Write property test for consistent response format
    - **Property 24: Consistent response format**
    - **Validates: Requirements 10.4**

- [ ] 12. Implement AgentCore runtime handler
  - [ ] 12.1 Create HTTP handler for AgentCore
    - Define `AgentCoreHandler` class
    - Implement `handle_request()` to parse AgentCore request format
    - Implement `_parse_request()` to extract query, actor_id, session_id
    - Implement `_format_response()` to format AgentResponse for AgentCore
    - Add error handling for malformed requests
    - _Requirements: 7.4_
  
  - [ ] 12.2 Create main entry point
    - Create `main.py` with `handler()` function for AgentCore
    - Initialize ConfigManager and load configuration
    - Initialize all components (memory client, specialist client, router, supervisor)
    - Handle initialization errors with clear messages
    - _Requirements: 7.4, 7.5, 8.5_
  
  - [ ]* 12.3 Write unit tests for AgentCore handler
    - Test request parsing with valid AgentCore requests
    - Test response formatting to AgentCore format
    - Test error handling for malformed requests
    - _Requirements: 7.4_

- [ ] 13. Final checkpoint - Integration testing
  - [ ] 13.1 Create integration test suite
    - Test end-to-end query processing with mocked services
    - Test query processing with memory service unavailable
    - Test query processing with specialist service unavailable
    - Test concurrent queries from multiple actors/sessions
    - _Requirements: 1.1, 2.1, 2.3, 4.5_
  
  - [ ] 13.2 Create deployment verification script
    - Script to verify all environment variables are set
    - Script to test connectivity to MCP memory server
    - Script to test connectivity to QNA specialist
    - Script to test Groq API authentication
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: core components → orchestration → runtime handler
- All async operations use httpx for HTTP calls and proper error handling
- LangGraph manages the state machine for workflow orchestration
