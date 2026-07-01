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
        import requests
        try:
            user_message = (
                "Summarize the following case data. Use ONLY the data provided. "
                "Highlight any items requiring attention.\n\n"
                + json.dumps(case_data, indent=2)
            )
            
            if model is not None and "qwen" in model.lower():
                url = "https://d9ym4p48160x5.cloudfront.net/api/query/generate"
                headers = {
                    "X-API-Key": "dwp-cmg-sec-key-7d9a1f8c",
                    "Content-Type": "application/json"
                }
                
                final_query = f"System:\n{self.system_prompt}\n\n"
                if self.few_shot_examples:
                    final_query += "Examples:\n"
                    for i, example in enumerate(self.few_shot_examples):
                        final_query += f"--- Example {i+1} ---\nUser: {example.get('user', '')}\nAssistant: {example.get('assistant', '')}\n\n"
                
                final_query += f"User:\n{user_message}"
                
                payload = {
                    "model": "qwen_14b_tuned",
                    "query": final_query,
                    "use_rag": True
                }

                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=None)
                    
                    if response.status_code == 504 or response.status_code >= 500:
                        error_body = response.text[:500]
                        return {
                            "content": f"⚠️ **Demo Mode Fallback (Case Summarizer)**\n\nThe Qwen API returned a Server Error ({response.status_code}).\n\n**Error Details:**\n```\n{error_body}\n```\n\nHere is a simulated response:\n\nThis is a simulated case summary. The case requires attention due to high arrears.",
                            "agent": self.AGENT_NAME,
                            "status": "success",
                            "model": "qwen_14b_mock",
                            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
                        }
                    response.raise_for_status()
                except requests.exceptions.ConnectionError:
                    return {
                        "content": "⚠️ **Demo Mode Fallback (Case Summarizer)**\n\nThe Qwen API connection failed. Here is a simulated response:\n\nThis is a simulated case summary. The case requires attention due to high arrears.",
                        "agent": self.AGENT_NAME,
                        "status": "success",
                        "model": "qwen_14b_mock",
                        "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
                    }
                data = response.json()

                content = data.get("response") or data.get("answer") or data.get("result") or data.get("content") or data.get("text")
                
                if not content and "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                    
                if not content:
                    content = f"Raw Response:\n```json\n{json.dumps(data, indent=2)}\n```"

                return {
                    "content": content,
                    "agent": self.AGENT_NAME,
                    "status": "success",
                    "model": "qwen_14b_tuned (custom api)",
                    "usage": {},
                }
            else:
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
