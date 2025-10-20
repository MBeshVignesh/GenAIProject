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


class SimpleCareerAgent:
    def __init__(self):
        """Initialize the career agent with AWS Bedrock client."""
        self.bedrock_client = None
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"  # Claude 3 Sonnet
        self._initialize_bedrock_client()

        # System prompt for career guidance
        self.system_prompt = """You are an expert career counselor and educational advisor with deep knowledge of:
- Current job market trends and salary expectations
- Required skills and qualifications for various roles
- Educational pathways and certification programs
- Industry-specific career progression opportunities
- Emerging technologies and their impact on careers

Your role is to provide comprehensive, personalized career guidance that includes:
1. Detailed skill requirements and learning paths
2. Recommended courses, certifications, and educational resources
3. Practical project suggestions to build experience
4. Industry insights and career progression opportunities
5. Salary expectations and job market outlook

Always provide actionable, specific advice tailored to the user's career goals."""

    def _initialize_bedrock_client(self):
        """Initialize AWS Bedrock client with proper error handling."""
        try:
            # Initialize Bedrock client
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name='us-east-1',  # Change to your preferred region
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                # Optional, for temporary credentials
                aws_session_token=os.getenv('AWS_SESSION_TOKEN')
            )
            print("AWS Bedrock client initialized successfully")
        except NoCredentialsError:
            print("Error: AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
            self.bedrock_client = None
        except Exception as e:
            print(f"Error initializing Bedrock client: {str(e)}")
            self.bedrock_client = None

    async def analyze(self, career_goal: str, user_background: str = "") -> str:
        """
        Analyze career goal and provide personalized recommendations using AWS Bedrock.

        Args:
            career_goal: The desired career path
            user_background: Optional background information about the user

        Returns:
            Personalized career recommendations
        """
        if not self.bedrock_client:
            return self._get_fallback_recommendation(career_goal)

        try:
            # Create user prompt
            user_prompt = f"""Career Goal: {career_goal}
            
Background: {user_background if user_background else "No specific background provided"}

Please provide a comprehensive career guidance plan including:
1. Required skills and technologies
2. Recommended learning path and timeline
3. Specific courses, certifications, or educational resources
4. Practical projects to build experience
5. Industry insights and career progression opportunities
6. Salary expectations and job market outlook

Format your response in a clear, actionable manner."""

            # Prepare the message for Claude using Messages API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{self.system_prompt}\n\n{user_prompt}"
                        }
                    ]
                }
            ]

            # Call Bedrock API with Messages API format
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "messages": messages
                })
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            recommendation = response_body['content'][0]['text']

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
            return self._get_fallback_recommendation(career_goal)

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return self._get_fallback_recommendation(career_goal)

    def _get_fallback_recommendation(self, career_goal: str) -> str:
        """Provide fallback recommendations when Bedrock is unavailable."""
        fallback_recs = {
            "Data Scientist": """Data Scientist Career Path:
• Core Skills: Python/R, SQL, Statistics, Machine Learning, Data Visualization
• Learning Path: 
  - Python fundamentals and data manipulation (pandas, numpy)
  - Statistics and probability
  - Machine learning algorithms and frameworks (scikit-learn, TensorFlow)
  - Data visualization (matplotlib, seaborn, Tableau)
• Projects: Kaggle competitions, personal data analysis projects
• Certifications: Google Data Analytics, AWS Machine Learning Specialty
• Timeline: 6-12 months for entry-level positions""",

            "Software Engineer": """Software Engineer Career Path:
• Core Skills: Programming languages (Python, Java, JavaScript), Data Structures, Algorithms, Git, System Design
• Learning Path:
  - Master one primary language deeply
  - Learn data structures and algorithms
  - Understand software development lifecycle
  - Practice with version control (Git)
• Projects: Build web applications, contribute to open source, create a portfolio
• Certifications: AWS Certified Developer, Google Cloud Professional Developer
• Timeline: 6-18 months depending on prior experience""",

            "Cloud Engineer": """Cloud Engineer Career Path:
• Core Skills: AWS/Azure/GCP, Docker, Kubernetes, CI/CD, Infrastructure as Code
• Learning Path:
  - Cloud platform fundamentals (AWS, Azure, or GCP)
  - Containerization (Docker, Kubernetes)
  - Infrastructure as Code (Terraform, CloudFormation)
  - DevOps practices and CI/CD pipelines
• Projects: Deploy applications to cloud, set up monitoring, automate deployments
• Certifications: AWS Solutions Architect, Azure Administrator, Google Cloud Professional
• Timeline: 3-12 months depending on prior experience"""
        }

        return fallback_recs.get(career_goal, f"""Career Guidance for {career_goal}:
• Research the specific skills and requirements for this role
• Identify relevant courses and certifications
• Build practical projects to demonstrate your skills
• Network with professionals in the field
• Consider internships or entry-level positions to gain experience
• Stay updated with industry trends and technologies""")

    def check_aws_credentials(self) -> bool:
        """Check if AWS credentials are properly configured."""
        try:
            # Try to get caller identity to verify credentials
            sts_client = boto3.client('sts')
            sts_client.get_caller_identity()
            return True
        except:
            return False
