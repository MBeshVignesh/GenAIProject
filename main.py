"""
Career Path Recommender System - Main Orchestrator
A multi-agent system using Strands Framework and AWS Bedrock Claude Sonnet 4.5
"""

import asyncio
import os
from agents.simple_career_agent import SimpleCareerAgent


async def main():
    print("=== Career Path Recommender System ===")
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

    # Get user input
    goal = input("Enter your career goal: ").strip() or "Data Scientist"
    background = input("Enter your background (optional): ").strip()

    print(f"\nAnalyzing career path for: {goal}")
    if background:
        print(f"Background: {background}")
    print("\nGenerating recommendations...\n")

    # Get recommendations
    result = await agent.analyze(goal, background)
    print("=" * 60)
    print("CAREER RECOMMENDATIONS")
    print("=" * 60)
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
