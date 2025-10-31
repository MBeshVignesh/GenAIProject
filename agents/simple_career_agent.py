"""
Career Matching Agent - Generates personalized career recommendations.
Uses AWS Bedrock Claude Sonnet 4.5 to analyze job market data and course catalog
to provide comprehensive career guidance and project recommendations.
"""

import asyncio
import json
import os
from botocore.exceptions import ClientError, NoCredentialsError
import boto3
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory

# Load environment variables from .env file
load_dotenv('aws_credentials.env')

SYSTEM_PROMPT = (
    """
You are a friendly, supportive, and insightful mentor, friend, and expert career coach.
- Help the user with job search, interviews (tech and business), resume and cover letter writing, career transitions, skills growth, and clarity on any topic they ask.
- Be conversational, encouraging, and clear—explain complex things simply, and offer real understanding, not just lists or bullet points.
- Adapt your tone: be empathetic if the user is nervous, anxious, or discouraged. Offer practical, specific guidance but in a warm and motivating way.
- Share advice as someone invested in the user's personal success and happiness.
If the user asks for a specific format (bullets, table, summary), comply—but otherwise, be as helpful as you would be in a text chat with a friend who's trying to grow their career.
"""
)

REGION = os.getenv("AWS_REGION", "us-east-2")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "10000"))
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
MODEL_ID = os.getenv("INFERENCE_PROFILE_ARN","arn:aws:bedrock:us-east-2:197496953075:inference-profile/global.anthropic.claude-sonnet-4-5-20250929-v1:0")

# Make a LangChain memory instance for conversational context
career_agent_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


def get_bedrock_client():
    try:
        return boto3.client(
            "bedrock-runtime",
            region_name=REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
    except Exception as e:
        print(f"Error initializing Bedrock client: {str(e)}")
    return None


def analyze_career_goal(bedrock_client, career_goal: str) -> str:
    # Load current chat history from memory
    memory_vars = career_agent_memory.load_memory_variables({})
    memory_messages = memory_vars.get("chat_history", [])

    memory_context = ""
    if memory_messages:
        memory_context = "Chat History:\n"
        for msg in memory_messages:
            role = "user" if getattr(msg, "type", None) == "human" else "assistant"
            memory_context += f"{role}: {msg.content}\n"

    user_prompt = f"""
You are assisting the user with whatever they need: interviews, resume or cover letter improvement, business or technical topics, or simply providing clarity and advice as a mentor and friend. Use a conversational and friendly tone. Always:
- Ask clarifying questions if the request isn't clear.
- Provide actionable advice but also offer encouragement, understanding, and explanations.
- If you give steps or points, wrap them in context so it's easy for the user to follow through or ask more.
- Do not give generic lists—adapt answers with empathy and insight, and always check if the user wants more depth or examples.
- Be patient and clear, especially if the user asks "explain like I'm five" or wants to understand deeply.
- Help the user feel more confident—especially for interviews, communication, or new challenges.

---

Here is the user's current question or topic:
"{career_goal}"
"""
    
    composed_prompt = f"{SYSTEM_PROMPT}\n\n{memory_context}\nUser message:\n{career_goal}\n\n{user_prompt}"
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": composed_prompt}
            ],
        }
    ]
    try:
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "messages": messages
            }),
        )
        body = response.get("body")
        if hasattr(body, "read"):
            body = body.read()
        response_body = json.loads(body)
        recommendation = response_body["content"][0]["text"]
        print("++++ Direct Sonnet invoke succeeded ++++")
        # Save new user input and answer in memory
        career_agent_memory.save_context({"input": career_goal}, {"output": recommendation})
        return recommendation
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error: {error_code} - {error_message}")
        if error_code == 'AccessDeniedException':
            print("Please check your AWS permissions for Bedrock.")
        elif error_code == 'ValidationException':
            print("Invalid request parameters. Check model ID and request format.")
        else:
            print(f"AWS Bedrock error: {error_code}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    return ""


def check_aws_credentials():
    try:
        sts_client = boto3.client('sts')
        sts_client.get_caller_identity()
        return True
    except:
        return False
