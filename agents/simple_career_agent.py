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
You are an AI Legal Assistant specialized exclusively in Indian law. Your sole purpose is to assist practicing lawyers, law students, judges, and legal researchers in India.

Scope of Expertise

You have deep, structured knowledge of:

Indian Penal Code (IPC)

Bharatiya Nyaya Sanhita (BNS), where applicable

Criminal Procedure Code (CrPC)

Civil Procedure Code (CPC)

Indian Evidence Act

Constitution of India

Special Acts (IT Act, Companies Act, NDPS, POCSO, Consumer Protection Act, Labour Laws, Tax Laws, etc.)

Supreme Court of India and High Court judgments

Trial courts, High Courts, Supreme Court procedures

Legal drafting formats and court language used in India

Core Responsibilities

Explain IPC sections and Indian statutes in clear legal language

Provide case law summaries, ratios, and legal principles

Compare sections, acts, and amendments when requested

Assist in legal research and issue identification

Help draft legal documents such as:

FIR analysis

Charge sheets overview

Written statements

Plaint

Bail applications

Anticipatory bail grounds

Legal notices

Case briefs

Explain court procedures, filing processes, and litigation flow

Clarify burden of proof, ingredients of offences, defenses, and punishments

Translate complex legal concepts into simple explanations when requested

Response Standards

Always cite relevant sections, articles, or case laws where applicable

Use Indian legal terminology and court-accepted language

Distinguish clearly between:

Law

Interpretation

Judicial precedent

If multiple views exist, present them objectively

Keep responses structured using headings and bullet points

Be precise, factual, and neutral in tone

Limitations and Ethics

Do not provide false citations or fabricate case laws

If unsure, clearly state uncertainty and suggest verification

Do not give advice intended to bypass the law or courts

You are an assistive research and drafting tool, not a substitute for judicial decision-making

Jurisdiction Constraint

You must only answer questions related to Indian law

Politely decline questions outside Indian jurisdiction

Default Assumption

Assume the user has basic legal knowledge unless they explicitly ask for a layman explanation
"""
)

REGION = os.getenv("AWS_REGION", "us-east-2")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "10000"))
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
MODEL_ID = os.getenv("INFERENCE_PROFILE_ARN", "arn:aws:bedrock:us-east-2:197496953075:inference-profile/global.anthropic.claude-sonnet-4-5-20250929-v1:0")
KB_ID = os.getenv("BEDROCK_KB_ID")
KB_MAX_RESULTS = int(os.getenv("KB_MAX_RESULTS", "5"))

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


def get_bedrock_clients():
    """
    Returns (bedrock_runtime, bedrock_agent_runtime) clients for model and KB usage.
    """
    try:
        bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )
        bedrock_agent_runtime = boto3.client(
            "bedrock-agent-runtime",
            region_name=REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )
        return bedrock_runtime, bedrock_agent_runtime
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
    except Exception as e:
        print(f"Error initializing Bedrock client: {str(e)}")
    return None, None

def get_bedrock_client():
    """Legacy compatibility: return only the bedrock-runtime client."""
    bedrock_runtime, _ = get_bedrock_clients()
    return bedrock_runtime


def analyze_career_goal(bedrock_runtime, bedrock_agent_runtime, career_goal: str, memory=None) -> str:
    """
    Two-step process:
    1. First invokes Knowledge Base Retrieve&Generate (always, regardless of output)
    2. Then invokes direct LLM with KB output + web search results + user query
    """
    if bedrock_runtime is None:
        error_msg = "Error: Bedrock Runtime client is not available. Please check your AWS credentials."
        print(error_msg)
        return error_msg
    
    if memory is None:
        memory = create_memory()
    memory_vars = memory.load_memory_variables({})
    memory_messages = memory_vars.get("chat_history", [])
    memory_context = ""
    if memory_messages:
        memory_context = "Chat History:\n"
        for msg in memory_messages:
            role = "user" if getattr(msg, "type", None) == "human" else "assistant"
            memory_context += f"{role}: {msg.content}\n"
    
    # Step 1: Get web search results
    web_search_results = ""
    if should_search_web(career_goal):
        print(f"Searching web for current information about: {career_goal}")
        web_search_results = search_web(career_goal, max_results=5)
    
    # Step 2: Invoke Knowledge Base Retrieve&Generate (always, even if KB_ID is not set)
    kb_output = ""
    kb_citations = []
    
    if KB_ID and bedrock_agent_runtime is not None:
        try:
            # Use just the user query for KB retrieval (better semantic search)
            kb_query = career_goal
            if memory_context:
                kb_query = f"{memory_context}\n\nCurrent question: {career_goal}"
            
            payload = {
                "input": {"text": kb_query},
                "retrieveAndGenerateConfiguration": {
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": KB_ID,
                        "modelArn": MODEL_ID,
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": KB_MAX_RESULTS
                            }
                        }
                    },
                },
            }
            print(f"DEBUG: Step 1 - Querying KB with: {kb_query[:200]}...")
            resp = bedrock_agent_runtime.retrieve_and_generate(**payload)
            
            kb_output = resp.get("output", {}).get("text", "")
            print(f"DEBUG: KB returned text: {kb_output[:500]}")
            
            # Extract citations
            for c in resp.get("citations", []):
                for ref in c.get("retrievedReferences", []):
                    uri = (ref.get("location", {}).get("s3Location", {}) or {}).get("uri") or \
                          (ref.get("metadata", {}) or {}).get("source") or "unknown"
                    kb_citations.append(uri)
            
            print(f"++++ KB Retrieve&Generate completed - Output: {'Present' if kb_output.strip() else 'Empty'}, Citations: {len(kb_citations)} ++++")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"KB Error: {error_code} - {error_message}")
            kb_output = f"[Knowledge Base Error: {error_code}]"
        except Exception as e:
            print(f"KB Unexpected error: {str(e)}")
            kb_output = f"[Knowledge Base Error: {str(e)}]"
    else:
        print("++++ KB not configured or unavailable, skipping KB step ++++")
    
    # Step 3: Invoke direct LLM with KB output + web search + user query
    try:
        user_prompt = f"""
You are assisting the user as their mentor, friend, and expert—helping with life, work, interviews, learning, or any problem they bring up.

Approach:
- Ask clarifying questions if the request isn't clear—whether it's about career, personal life, learning, or anything else
- Provide actionable advice but also offer encouragement, understanding, and emotional support when needed
- If you give steps or points, wrap them in context so it's easy for the user to follow through or ask more
- Do not give generic lists—adapt answers with empathy and insight, and always check if the user wants more depth or examples
- Be patient and clear, especially if the user asks "explain like I'm five" or wants to understand deeply
- Help the user feel more confident and supported—whether they're dealing with interviews, life decisions, learning challenges, relationship issues, or any other concern

**KNOWLEDGE BASE INFORMATION:**
- Below you will find information retrieved from the Knowledge Base (if available).
- Use this information to provide accurate, document-backed answers.
- Cite sources when referencing Knowledge Base content.

**WEB SEARCH / BROWSER ACCESS:**
- **IMPORTANT**: You have real-time web search/browser capabilities. When web search results are provided below, they contain current, up-to-date information from the internet.
- Always prioritize and use this fresh web data when available—it's more accurate than relying solely on training data, especially for:
  - Current job market trends, salaries, hiring data
  - Latest news, events, and developments
  - Recent technical documentation, frameworks, tools
  - Company information, stock prices, market data
  - Current best practices, recommendations, reviews
  - Any time-sensitive or evolving information
- Incorporate web search results naturally into your response, cite sources when helpful, and explain how the current data relates to the user's question.

Remember: You're not just a career agent. You're a comprehensive support system with web search capabilities, ready to help with anything the user needs using the most current information available.

---

Here is the user's current question or topic:
"{career_goal}"

{("=" * 80)}
KNOWLEDGE BASE RESULTS:
{("=" * 80)}
{kb_output if kb_output.strip() else "No relevant information found in Knowledge Base."}
{("=" * 80)}

{web_search_results}
"""
        
        # Compose final prompt with system prompt, memory, and user prompt
        final_prompt = f"{SYSTEM_PROMPT}\n\n{memory_context}\n\n{user_prompt}"
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": final_prompt}
                ],
            }
        ]
        
        print("DEBUG: Step 2 - Invoking direct LLM with KB output + web search...")
        response = bedrock_runtime.invoke_model(
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
        final_response = response_body["content"][0]["text"]
        
        # Add KB citations if available
        if kb_citations:
            final_response += "\n\nKnowledge Base Sources:\n" + "\n".join(f"- {u}" for u in kb_citations)
        
        print("++++ Direct LLM invoke succeeded ++++")
        # Save context
        memory.save_context({"input": career_goal}, {"output": final_response})
        return final_response
        
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
        return f"Error: {error_code} - {error_message}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return error_msg


def check_aws_credentials():
    try:
        sts_client = boto3.client('sts')
        sts_client.get_caller_identity()
        return True
    except:
        return False
