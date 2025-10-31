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
from datetime import datetime

# Web search functionality
try:
    from ddgs import DDGS
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    print("Warning: ddgs package not available. Web search will be disabled.")
try:
    from langchain.memory import ConversationBufferMemory  # preferred import
except Exception:
    # Minimal fallback so app still works without langchain.memory
    class _Msg:
        def __init__(self, msg_type: str, content: str):
            self.type = msg_type
            self.content = content

    class ConversationBufferMemory:  # type: ignore
        def __init__(self, memory_key: str = "chat_history", return_messages: bool = True):
            self.memory_key = memory_key
            self.return_messages = return_messages
            self._messages = []  # list[_Msg]

        def load_memory_variables(self, _: dict):
            return {self.memory_key: list(self._messages)}

        def save_context(self, inputs: dict, outputs: dict):
            user_text = inputs.get("input", "")
            if user_text:
                self._messages.append(_Msg("human", user_text))
            ai_text = outputs.get("output", "")
            if ai_text:
                self._messages.append(_Msg("ai", ai_text))

# Load environment variables from .env file
load_dotenv('aws_credentials.env')

SYSTEM_PROMPT = (
    """
You are a friendly, supportive, and insightful mentor, friend, and expert career coach.
- Help the user with job search, interviews (tech and business), resume and cover letter writing, career transitions, skills growth, and clarity on any topic they ask.
- Be conversational, encouraging, and clear—explain complex things simply, and offer real understanding, not just lists or bullet points.
- Adapt your tone: be empathetic if the user is nervous, anxious, or discouraged. Offer practical, specific guidance but in a warm and motivating way.
- Share advice as someone invested in the user's personal success and happiness.
- You have access to real-time web search results for current information (salaries, job market trends, latest tech stacks, hiring data, etc.). When current information is provided via web search, prioritize using it to give accurate, up-to-date answers.
If the user asks for a specific format (bullets, table, summary), comply—but otherwise, be as helpful as you would be in a text chat with a friend who's trying to grow their career.
"""
)

REGION = os.getenv("AWS_REGION", "us-east-2")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "10000"))
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
MODEL_ID = os.getenv("INFERENCE_PROFILE_ARN","arn:aws:bedrock:us-east-2:197496953075:inference-profile/global.anthropic.claude-sonnet-4-5-20250929-v1:0")

def create_memory():
    """
    Create a new, isolated memory instance for each user session.
    This ensures each Streamlit session has its own independent conversation memory.
    """
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True)


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web for current information using DuckDuckGo.
    Returns formatted search results as a string.
    """
    if not WEB_SEARCH_AVAILABLE:
        return ""
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            print("results** -- ",results)
            if not results:
                return ""
            
            search_summary = f"\n[Current Web Search Results for '{query}']:\n"
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                snippet = result.get('body', 'No description')
                url = result.get('href', '')
                search_summary += f"\n{i}. {title}\n   {snippet}\n   Source: {url}\n"
            
            return search_summary
    except Exception as e:
        print(f"Web search error: {str(e)}")
        return ""


def should_search_web(user_query: str) -> bool:
    """
    Determine if the query requires current/latest information that should be searched.
    """
    if not WEB_SEARCH_AVAILABLE:
        return False
    
    # Keywords that suggest need for current information
    current_info_keywords = [
        # Time-related
        "latest", "current", "today", "recent", "now", "2025", "2024", "2026",
        "this year", "this month", "this week", "newest", "updated",
        # Market & Career
        "trends", "news", "update", "salary", "market", "demand", "supply",
        "hiring", "jobs", "job market", "employment", "career outlook",
        "industry outlook", "growth", "opportunities", "openings",
        # Companies & Employers
        "companies", "employers", "recruiters", "top companies", "best companies",
        "hiring managers", "startups", "tech companies",
        # Technology & Skills
        "tech stack", "framework", "technology", "tools", "skills in demand",
        "programming languages", "certification", "course", "program",
        "training", "bootcamp", "education", "degree", "credentials",
        # Salary & Compensation
        "pay", "compensation", "wage", "income", "earnings", "benefits",
        "perks", "bonus", "equity", "remote work", "work from home",
        # Interview & Application
        "interview questions", "interview process", "application", "resume tips",
        "cover letter", "portfolio", "github", "linkedin",
        # Industry-Specific
        "ai", "machine learning", "data science", "software engineering",
        "cloud", "devops", "cybersecurity", "blockchain", "web3",
        # Location-Based
        "remote", "hybrid", "work from home",
        # Other Current Info Indicators
        "what's", "what is", "how much", "how many", "where", "who is hiring",
        "best practices", "recommended", "popular", "in-demand", "look", "more about"
    ]
    
    query_lower = user_query.lower()
    return any(keyword in query_lower for keyword in current_info_keywords)


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


def analyze_career_goal(bedrock_client, career_goal: str, memory=None) -> str:
    """
    Analyze career goal with optional conversation memory.
    Args:
        bedrock_client: AWS Bedrock client
        career_goal: User's question or prompt
        memory: Optional ConversationBufferMemory instance (creates new if None)
    Returns:
        Response string from the agent
    """
    # Use provided memory or create a new one (for backward compatibility)
    if memory is None:
        memory = create_memory()
    
    # Load current chat history from memory
    memory_vars = memory.load_memory_variables({})
    memory_messages = memory_vars.get("chat_history", [])

    memory_context = ""
    if memory_messages:
        memory_context = "Chat History:\n"
        for msg in memory_messages:
            role = "user" if getattr(msg, "type", None) == "human" else "assistant"
            memory_context += f"{role}: {msg.content}\n"

    # Check if we need to search the web for current information
    web_search_results = ""
    if should_search_web(career_goal):
        print(f"Searching web for current information about: {career_goal}")
        web_search_results = search_web(career_goal, max_results=5)

    user_prompt = f"""
You are assisting the user with whatever they need: interviews, resume or cover letter improvement, business or technical topics, or simply providing clarity and advice as a mentor and friend. Use a conversational and friendly tone. Always:
- Ask clarifying questions if the request isn't clear.
- Provide actionable advice but also offer encouragement, understanding, and explanations.
- If you give steps or points, wrap them in context so it's easy for the user to follow through or ask more.
- Do not give generic lists—adapt answers with empathy and insight, and always check if the user wants more depth or examples.
- Be patient and clear, especially if the user asks "explain like I'm five" or wants to understand deeply.
- Help the user feel more confident—especially for interviews, communication, or new challenges.
- **IMPORTANT: You have access to current web search results when provided below. Use this real-time information to give accurate, up-to-date answers about job markets, salaries, trends, tech stacks, and any current events or recent developments.**

---

Here is the user's current question or topic:
"{career_goal}"
{web_search_results}
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
        memory.save_context({"input": career_goal}, {"output": recommendation})
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
