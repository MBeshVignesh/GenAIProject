"""
Test script for the Career Path Recommender System
Tests the AWS Bedrock integration without requiring user input
"""

import asyncio
import os
from agents.simple_career_agent import SimpleCareerAgent


async def test_career_agent():
    print("=== Testing Career Path Recommender System ===")
    print("Powered by AWS Bedrock Claude 3.5 Sonnet\n")

    # Initialize agent
    agent = SimpleCareerAgent()

    # Check AWS credentials
    if not agent.check_aws_credentials():
        print("WARNING: AWS credentials not found or invalid.")
        print("Please set the following environment variables:")
        print("- AWS_ACCESS_KEY_ID")
        print("- AWS_SECRET_ACCESS_KEY")
        print("- AWS_DEFAULT_REGION (optional, defaults to us-east-1)")
        print("\nThe system will use fallback recommendations.\n")
    else:
        print("SUCCESS: AWS credentials found and valid!")

    # Test cases
    test_cases = [
        {
            "career_goal": "Data Scientist",
            "background": "Computer Science student with basic Python knowledge"
        },
        {
            "career_goal": "Software Engineer",
            "background": "Recent graduate with no professional experience"
        },
        {
            "career_goal": "Cloud Engineer",
            "background": "IT professional with 3 years experience"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST CASE {i}: {test_case['career_goal']}")
        print(f"{'='*60}")
        print(f"Background: {test_case['background']}")
        print("\nGenerating recommendations...\n")

        # Get recommendations
        result = await agent.analyze(test_case['career_goal'], test_case['background'])
        print("CAREER RECOMMENDATIONS:")
        print("-" * 40)
        print(result)
        print("-" * 40)

        if i < len(test_cases):
            print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_career_agent())
