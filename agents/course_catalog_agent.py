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
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('aws_credentials.env')



class CourseCatalogAgent:
    def __init__(self):
        """Initialize the career agent with AWS Bedrock clients (runtime + optional agent-runtime for KB)."""
        self.region = os.getenv("AWS_REGION", "us-east-2")  # keep consistent with where your profile/KB live
        self.inference_profile_arn = os.getenv("INFERENCE_PROFILE_ARN_SONNET")  # REQUIRED for Sonnet
        self.kb_id = os.getenv("BEDROCK_KB_ID")  # OPTIONAL: if set, we can do Retrieve&Generate (KB-backed)
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "10000"))
        self.kb_max_results = int(os.getenv("KB_MAX_RESULTS", "5"))
        self.kb_similarity_threshold = float(os.getenv("KB_SIMILARITY_THRESHOLD", "0.7"))

        if not self.inference_profile_arn:
            raise ValueError(
                "Missing INFERENCE_PROFILE_ARN_SONNET. Claude Sonnet 4.5 requires invoking via an inference profile."
            )

        # System prompt for career guidance (empathetic + scope-aware)
        self.system_prompt = (
            """
            You are a compassionate, practical course counselor.
            Read and understand ALL provided documents as a human would (course codes, descriptions). Rely only on these docs—no outside facts.
            From the docs, extract what the user needs: course names, course codes, brief descriptions, prerequisites/corequisites, credits, typical term/modality, key topics, and clear course outcomes (skills/competencies). 
            Include any explicitly mentioned course and closely related ones when relevant. If something isn’t in the docs, say it isn’t available.
            Be warm and concise. Give only what the user asks for (e.g., “descriptions only,” “only codes,” “only outcomes”) and follow any requested format exactly. Otherwise keep it short, factual, and helpful. If nothing relevant is found, say so plainly.
            """
        )

        self.bedrock_runtime = None
        self.bedrock_agent_runtime = None
        self._initialize_bedrock_clients()
        
        # Model information
        self.model_name = "Claude Sonnet 4.5"
        self.model_version = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"

    def _initialize_bedrock_clients(self):
        """Initialize AWS Bedrock runtime clients with proper error handling."""
        try:
            # bedrock-runtime for direct model/profile invocation
            self.bedrock_runtime = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            )            
            # bedrock-agent-runtime for Knowledge Bases (Retrieve & Generate)
            self.bedrock_agent_runtime = boto3.client(
                "bedrock-agent-runtime",
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            )
        except NoCredentialsError:
            raise RuntimeError(
                "AWS credentials not found. Set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (and AWS_SESSION_TOKEN if needed)."
            )
        except Exception as e:
            raise RuntimeError(f"Error initializing Bedrock clients: {e}") from e

    async def analyze(self, user_text: str) -> str:
        """
        Analyze free-text input from the user and return a career guidance response.
        If BEDROCK_KB_ID is set, uses Knowledge Base Retrieve&Generate (grounded, with citations).
        Otherwise, calls Sonnet directly via the inference profile.
        """
        if not user_text or not user_text.strip():
            raise ValueError("user_text must be a non-empty string.")

        # Build the empathetic, scope-aware task block
        task_block = (
            """Task:
            From the provided documents, write the course details, descriptions relevant to the user’s query.
            Rules:
            - Each description: 1–2 sentences, clear and factual, paraphrased from the docs.
            - If multiple courses apply, provide each description as its own short paragraph, separated by exactly one blank line.
            - If the user mentions a specific course, include its description if present in the docs.
            - If nothing relevant is found, reply exactly: No relevant description available.
            """
            )

        # Combine system + user content
        composed_prompt = f"{self.system_prompt}\n\nUser message:\n{user_text}\n\n{task_block}"

        try:
            if self.kb_id:
                payload = {
                    "input": {"text": composed_prompt},
                    "retrieveAndGenerateConfiguration": {
                        "type": "KNOWLEDGE_BASE",
                        "knowledgeBaseConfiguration": {
                            "knowledgeBaseId": self.kb_id,
                            "modelArn": self.inference_profile_arn,
                            "retrievalConfiguration": {
                                "vectorSearchConfiguration": {
                                    "numberOfResults": self.kb_max_results
                                }
                            }
                        },
                    },
                }
                resp = self.bedrock_agent_runtime.retrieve_and_generate(**payload)
                text = resp.get("output", {}).get("text", "")
                # If you want to append sources:
                citations = []
                for c in resp.get("citations", []):
                    for ref in c.get("retrievedReferences", []):
                        uri = (ref.get("location", {}).get("s3Location", {}) or {}).get("uri") or \
                              (ref.get("metadata", {}) or {}).get("source") or "unknown"
                        citations.append(uri)
                if citations:
                    text += "\n\nSources:\n" + "\n".join(f"- {u}" for u in citations)
                print("++++ KB Retrieve&Generate succeeded ++++")
                return text

            else:
                # --- Path B: Direct Sonnet invocation via inference profile ---
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

        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "Unknown")
            msg = e.response.get("Error", {}).get("Message", str(e))
            # Helpful diagnostics for common cases
            if "AccessDenied" in code or "AccessDeniedException" in msg:
                raise PermissionError(
                    f"Access denied invoking Bedrock. Check IAM permissions on inference profile {self.inference_profile_arn} "
                    f"and Knowledge Base {self.kb_id or '(none)'} in region {self.region}. "
                    f"Original: {code}: {msg}"
                ) from e
            if "ValidationException" in code or "on-demand throughput isn't supported" in msg:
                raise RuntimeError(
                    "Claude Sonnet 4.5 requires an inference profile. Ensure you set INFERENCE_PROFILE_ARN_SONNET and do not pass modelId."
                ) from e
            raise RuntimeError(f"Bedrock client error: {code}: {msg}") from e
        except (BotoCoreError, NoCredentialsError) as e:
            raise RuntimeError(f"Bedrock runtime error: {e}") from e
        except KeyError as e:
            raise RuntimeError(f"Unexpected Bedrock response format, missing key: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e

    def get_model_info(self) -> Dict[str, str]:
        """Get information about the current model configuration"""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "inference_profile_arn": self.inference_profile_arn,
            "knowledge_base_id": self.kb_id,
            "knowledge_base_enabled": bool(self.kb_id),
            "region": self.region,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

    def check_configuration(self) -> Dict[str, Any]:
        """Check if the agent is properly configured"""
        config_status = {
            "aws_credentials": bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")),
            "inference_profile": bool(self.inference_profile_arn),
            "knowledge_base": bool(self.kb_id),
            "region": self.region is not None,
            "clients_initialized": bool(self.bedrock_runtime and self.bedrock_agent_runtime)
        }
        
        config_status["ready"] = all([
            config_status["aws_credentials"],
            config_status["inference_profile"],
            config_status["region"],
            config_status["clients_initialized"]
        ])
        
        return config_status


async def main():
    course = input("How Can I Help You with your courses?: ").strip()
    agent = CourseCatalogAgent()
    result = await agent.analyze(course)
    print("=" * 60)
    print("COURSE RECOMMENDATIONS")
    print("=" * 60)
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())