source Servers/agentcore-reciept-mcp/.venv/bin/activate




## 📘 Overview

This repository explains MCP server implementation for receipt extraction use case that can extract receipt photo information such as store name, purchase date and total/amount then write output of extract information to **Amazon DynamoDB** table and send email of output of extract information using **Amazon SNS**.

## 📁 Repository Structure

| File / Notebook | Description |
| :--- | :--- |
| `MCPServerAgentCoreRuntime.ipynb` | Notebook of MCP server implementation using **Google Gemini** and **AgentCore Runtime**. |
| `MCPServerAgentCoreGateway.ipynb` | Notebook of MCP server implementation using **Google Gemini**, **AgentCore Runtime** and **AgentCore Gateway** |
| `photos` | Sample receipt photo folder used in two notebooks. |

## ✅ Prerequisites

1. **Amazon Web Services (AWS)**: Access to AWS services, you can sign up/sign in [here.](https://console.aws.amazon.com)

| AWS service | Description |
| :--- | :--- |
| Amazon S3 | upload file from local to S3 and download file from S3 to receipt extraction MCP server processes. |
| AWS Secret Manager | store Gemini API Key and LLM inference in receipt extraction MCP server. |
| AgentCore Runtime, AgentCore Gateway and AgentCore Identity. |
| AgentCore Starter Toolkit | quickly configure and deploy MCP server with several AWS services such as Amazon ECR, AWS CodeBuild, and AWS IAM. |
| Amazon Cognito | Authentication and authorization for AgentCore Identity. |
| Amazon DynamoDB | Write result of receipt extraction to NoSQL database. |
| Amazon SNS | Send email notification about result of receipt extraction. |

2. Google Gemini account, you can sign up/sign in [here](https://aistudio.google.com)

3. Langchain.

## 🚀 Getting Started

1. If you don't have AWS credentials (AWS secret key and AWS access key), click this [getting started](https://github.com/budionosanai/amazon-bedrock-agentcore-one-to-one?tab=readme-ov-file#-getting-started---first-time-only) but if you already have AWS credentials, skip this getting started and go to second step.

2. Open, run and following this notebooks :

| Notebook | Using |
| :--- | :--- |
| **[MCP Server on AgentCore Runtime](./MCPServerAgentCoreRuntime.ipynb)** | **Google Colab**. |
| **[MCP Server on AgentCore Gateway](./MCPServerAgentCoreGateway.ipynb)** | **Google Colab**. |

3. **(OPTIONAL)** Delete AWS services in AgentCore notebook with this code :

```
agentcore_runtime = boto3.client('bedrock-agentcore-control', region)

agentcore_runtime.delete_agent_runtime(agentRuntimeId=launch_result.agent_id)

ecr = boto3.client('ecr', region)

ecr.delete_repository(repositoryName=launch_result.ecr_uri.split('/')[1], force=True)

codebuild = boto3.client('codebuild', region)

codebuild.delete_project(name=launch_result.codebuild_id.split(':')[0])

s3 = boto3.client('s3', region)

s3.delete_bucket(Bucket='receipts-extraction')

secretsmanager = boto3.client('secretsmanager', region)

secretsmanager.delete_secret(SecretId='geminiapikey')

cognito = boto3.client('cognito-idp', region)

cognito.delete_user_pool(UserPoolId=cognito_pool_id)

cognito.delete_user_pool(UserPoolId=runtime_cognito_pool_id)

dynamodb = boto3.client('dynamodb', region)

dynamodb.delete_table(TableName='receiptsExtraction')

sns = boto3.client('sns', region)
sts_client = boto3.client('sts')
response = sts_client.get_caller_identity()
aws_account_id = response['Account']
sns.delete_topic(TopicArn=f"arn:aws:sns:us-west-2:{aws_account_id}:receiptsExtractionEmail")

identity.delete_oauth2_credential_provider(name=cognito_provider_name)

gateway_target.delete_gateway_target(
    gatewayIdentifier = gateway_id,
    targetId = create_gateway_target_response['targetId']
)

gateway.delete_gateway(gateway_id)

runtime.delete_agent_runtime(agentRuntimeId=agent_id)
```

## ⚠️ Warning

**Ensure securely API keys such as AWS credentials and Gemini API key — DO NOT HARDCORE them in notebooks.**

## 📚 Resources

* [Amazon Bedrock AgentCore documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
* [Langchain documentation](https://docs.langchain.com/oss/python/langchain/overview)
* [Google Gemini documentation](https://ai.google.dev/gemini-api/docs/)

## Tutorial Blog

* https://dev.to/budionosan/amazon-bedrock-agentcore-mcp-server-on-agentcore-runtime-and-agentcore-gateway-el9

## 🙏 Acknowledgments

**Amazon Web Services, Google Gemini, Langchain and Google Colab**