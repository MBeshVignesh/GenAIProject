"""
Career Matching Agent - Generates personalized career recommendations.
Uses AWS Bedrock Claude Sonnet 4.5 to analyze job market data and course catalog
to provide comprehensive career guidance and project recommendations.
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('aws_credentials.env')


class CareerAgent:
    def __init__(self):
        """Initialize the career agent with AWS Bedrock client."""
        self.bedrock_runtime = None
        self.region = os.getenv("AWS_REGION", "us-east-2")  # keep consistent with where your profile/KB live
        self.inference_profile_arn = os.getenv("INFERENCE_PROFILE_ARN_SONNET")  # REQUIRED for Sonnet
        self.kb_id = os.getenv("BEDROCK_KB_ID")  # OPTIONAL: if set, we can do Retrieve&Generate (KB-backed)
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "10000"))
        self.kb_max_results = int(os.getenv("KB_MAX_RESULTS", "5"))
        self.kb_similarity_threshold = float(os.getenv("KB_SIMILARITY_THRESHOLD", "0.7"))  # Claude 3 Sonnet
        self._initialize_bedrock_client()

        # System prompt for career guidance
        self.system_prompt = """You are an experienced, no-nonsense career coach. Be specific, actionable, and concise. Prefer bullet points over paragraphs.
        When the user requests a specific output format or style, follow it exactly."""

    def _initialize_bedrock_client(self):
        """Initialize AWS Bedrock client with proper error handling."""
        try:
            # Initialize Bedrock client
            self.bedrock_runtime = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            ) 
            print("AWS Bedrock client initialized successfully")
        except NoCredentialsError:
            print("Error: AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
            self.bedrock_runtime = None
        except Exception as e:
            print(f"Error initializing Bedrock client: {str(e)}")
            self.bedrock_runtime = None

    async def analyze(self, career_goal: str) -> str:

        try:
            # Create user prompt
            user_prompt = f"""
            1) Understand the user's Career Goal from their words (make a good-faith).
            2) If the user explicitly requests a specific structure, tone, or format (e.g., JSON, table, specific headings), follow it exactly.
            3) **Scope rule:** If the user requests only a subset (e.g., “only projects”, “just skills”, “give me a 3-month plan only”), output only that subset and nothing else.
            Guidelines:
            - Use the user’s domain/industry context if present.
            - Name concrete tools (e.g., Pandas, SQL window functions, dbt, Airflow) instead of vague labels.
            - Make bullets outcome-oriented (“Able to build X…”, “Can evaluate Y…”).
            - Zero filler. If scope is restricted, return only what was requested.
            If user shows anxiety or constraints (time, money, work/life):
            - Offer one “small next step” and a lightweight alternative path.
            - Keep empathy brief and specific (e.g., “Balancing work and study is hard—let’s keep first steps under 4 hrs/week.”), then return to action."""

            composed_prompt = f"{self.system_prompt}\n\nUser message:\n{career_goal}\n\n{user_prompt}"
            # Prepare the message for Claude using Messages API
            messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": composed_prompt}
                        ],
                    }
                ]
            response = self.bedrock_runtime.invoke_model(
                modelId="arn:aws:bedrock:us-east-2:197496953075:inference-profile/global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": messages
                }),
            )

            # Parse standard Bedrock response shape
            body = response.get("body")
            if hasattr(body, "read"):
                body = body.read()
            response_body = json.loads(body)
            recommendation = response_body["content"][0]["text"]
            print("++++ Direct Sonnet invoke succeeded ++++")
            return recommendation

            # Parse response
            # response_body = json.loads(response['body'].read())
            # recommendation = response_body['content'][0]['text']
            # print("+++++++++++++++++ Successfully got response from Bedrock +++++++++++++++++")
            # return recommendation

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

    # def _get_fallback_recommendation(self, career_goal: str) -> str:
    #     """Provide fallback recommendations when Bedrock is unavailable."""
    #     fallback_recs = {
    #         "Data Scientist": """Data Scientist Career Path:
    #         • Core Skills: Python/R, SQL, Statistics, Machine Learning, Data Visualization
    #         • Learning Path: 
    #         - Python fundamentals and data manipulation (pandas, numpy)
    #         - Statistics and probability
    #         - Machine learning algorithms and frameworks (scikit-learn, TensorFlow)
    #         - Data visualization (matplotlib, seaborn, Tableau)
    #         • Projects: Kaggle competitions, personal data analysis projects
    #         • Certifications: Google Data Analytics, AWS Machine Learning Specialty
    #         • Timeline: 6-12 months for entry-level positions""",

    #                     "Software Engineer": """Software Engineer Career Path:
    #         • Core Skills: Programming languages (Python, Java, JavaScript), Data Structures, Algorithms, Git, System Design
    #         • Learning Path:
    #         - Master one primary language deeply
    #         - Learn data structures and algorithms
    #         - Understand software development lifecycle
    #         - Practice with version control (Git)
    #         • Projects: Build web applications, contribute to open source, create a portfolio
    #         • Certifications: AWS Certified Developer, Google Cloud Professional Developer
    #         • Timeline: 6-18 months depending on prior experience""",

    #                     "Cloud Engineer": """Cloud Engineer Career Path:
    #         • Core Skills: AWS/Azure/GCP, Docker, Kubernetes, CI/CD, Infrastructure as Code
    #         • Learning Path:
    #         - Cloud platform fundamentals (AWS, Azure, or GCP)
    #         - Containerization (Docker, Kubernetes)
    #         - Infrastructure as Code (Terraform, CloudFormation)
    #         - DevOps practices and CI/CD pipelines
    #         • Projects: Deploy applications to cloud, set up monitoring, automate deployments
    #         • Certifications: AWS Solutions Architect, Azure Administrator, Google Cloud Professional
    #         • Timeline: 3-12 months depending on prior experience"""
    #                 }

    #         return fallback_recs.get(career_goal, f"""Career Guidance for {career_goal}:
    #         • Research the specific skills and requirements for this role
    #         • Identify relevant courses and certifications
    #         • Build practical projects to demonstrate your skills
    #         • Network with professionals in the field
    #         • Consider internships or entry-level positions to gain experience
    #         • Stay updated with industry trends and technologies""")

    def check_aws_credentials(self) -> bool:
        """Check if AWS credentials are properly configured."""
        try:
            # Try to get caller identity to verify credentials
            sts_client = boto3.client('sts')
            sts_client.get_caller_identity()
            return True
        except:
            return False
