"""
Simple Lambda function that implements a tool for AgentCore API Gateway.
Returns a greeting message when called.
"""

import json


def lambda_handler(event, context):
    """
    Lambda handler for the DefaultTool.
    
    Args:
        event: Lambda event containing the tool invocation
        context: Lambda context
        
    Returns:
        Tool response with greeting message
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Extract tool information from event
    tool_name = event.get('toolName', 'DefaultTool')
    tool_input = event.get('toolInput', {})
    
    # Generate response
    response_message = "Hello, from hello lambda tool:>)"
    
    # Return in AgentCore tool response format
    return {
        'statusCode': 200,
        'body': json.dumps({
            'toolName': tool_name,
            'toolResult': {
                'content': [
                    {
                        'text': response_message
                    }
                ]
            }
        })
    }


# For local testing
if __name__ == "__main__":
    test_event = {
        'toolName': 'DefaultTool',
        'toolInput': {}
    }
    
    result = lambda_handler(test_event, None)
    print(f"\nResponse: {json.dumps(result, indent=2)}")
