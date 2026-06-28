"""
Case Summarizer Agent.

Generates a concise, scannable overview of the case
that a caseworker can read in under 30 seconds.
"""

import json
from typing import Optional
from llm.gateway import LLMGateway, LLMGatewayError
from prompts.system_prompts import get_agent_config


class CaseSummarizerAgent:
    """
    Agent that generates concise case summaries.

    Produces a structured overview highlighting key metrics,
    contacts, statuses, and red flags for quick caseworker review.
    """

    AGENT_NAME = "case_summarizer"

    def __init__(self, gateway: LLMGateway):
        self.gateway = gateway
        config = get_agent_config(self.AGENT_NAME)
        self.system_prompt = config["system_prompt"]
        self.few_shot_examples = config["few_shot_examples"]

    def run(self, case_data: dict, model: Optional[str] = None) -> dict:
        """
        Run the Case Summarizer agent.

        Args:
            case_data: The full case JSON payload.

        Returns:
            dict with 'content' (str), 'agent' (str), 'status' (str).
        """
        try:
            user_message = (
                "Summarize the following case data. Use ONLY the data provided. "
                "Highlight any items requiring attention.\n\n"
                + json.dumps(case_data, indent=2)
            )

            result = self.gateway.chat(
                system_prompt=self.system_prompt,
                user_message=user_message,
                few_shot_examples=self.few_shot_examples,
                model=model,
            )

            return {
                "content": result["content"],
                "agent": self.AGENT_NAME,
                "status": "success",
                "model": result.get("model", ""),
                "usage": result.get("usage", {}),
            }

        except LLMGatewayError as e:
            return {
                "content": f"⚠️ **Case Summarizer Error:** {e.message}",
                "agent": self.AGENT_NAME,
                "status": "error",
                "error": e.message,
            }

        except Exception as e:
            return {
                "content": f"⚠️ **Unexpected Error:** {str(e)}",
                "agent": self.AGENT_NAME,
                "status": "error",
                "error": str(e),
            }
