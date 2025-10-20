"""
Career Path Recommender System - Main Orchestrator
A multi-agent system using Strands Framework and AWS Bedrock Claude Sonnet 4.5
"""

import asyncio
from agents.simple_career_agent import SimpleCareerAgent


async def main():
    agent = SimpleCareerAgent()
    goal = input("Enter your career goal: ").strip() or "Data Scientist"
    result = await agent.analyze(goal)
    print("\nRecommendation:\n", result)

if __name__ == "__main__":
    asyncio.run(main())
