"""
Calculation Explainer Agent.

Explains OGM, Non-OGM, arrears, and collection date calculations
in plain English. Never recalculates — only translates the numbers
from the case JSON payload.
"""

import json
from typing import Optional
from llm.gateway import LLMGateway, LLMGatewayError
from prompts.system_prompts import get_agent_config


class CalculationExplainerAgent:
    """
    Agent that explains financial calculations to caseworkers.

    Takes case JSON data containing calculation inputs/outputs
    and produces a plain-English explanation using an LLM with
    strict guardrails against recalculation or hallucination.
    """

    AGENT_NAME = "calculation_explainer"

    def __init__(self, gateway: LLMGateway):
        self.gateway = gateway
        config = get_agent_config(self.AGENT_NAME)
        self.system_prompt = config["system_prompt"]
        self.few_shot_examples = config["few_shot_examples"]

    def _prepare_payload(self, case_data: dict) -> str:
        """
        Extract and structure the calculation-relevant data from the case JSON.

        Focuses on: calculations, arrears, method of payment, and service requests.
        """
        payload_parts = []

        master = case_data.get("masterCase", case_data)
        cases = master.get("cases", [])

        if not cases:
            # If no cases array, treat the whole thing as a single case
            return json.dumps(case_data, indent=2)

        for case in cases:
            case_info = {
                "caseNumber": case.get("caseNumber", "Unknown"),
                "serviceType": case.get("serviceType", "Unknown"),
                "caseStatus": case.get("caseStatus", "Unknown"),
                "calculations": case.get("calculations", {}),
                "methodOfPayment": case.get("methodOfPayment", {}),
                "arrearsDetails": case.get("arrearsDetails", {}),
            }
            payload_parts.append(case_info)

        return json.dumps(
            {
                "masterCaseId": master.get("id", master.get("masterCaseNumber", "Unknown")),
                "nrpGrossWeeklyIncome": master.get("grossWeeklyIncome"),
                "incomeSource": master.get("incomeSource"),
                "cases": payload_parts,
            },
            indent=2,
        )

    def run(self, case_data: dict, model: Optional[str] = None) -> dict:
        """
        Run the Calculation Explainer agent.

        Args:
            case_data: The full case JSON payload.

        Returns:
            dict with 'content' (str), 'agent' (str), 'status' (str).
        """
        import requests
        try:
            user_message = self._prepare_payload(case_data)

            # Construct query including system prompt and formatting examples
            query = f"System Instruction:\n{self.system_prompt}\n\n"
            prompt_prefix = f"System Instruction:\n{self.system_prompt}\n\n"
            
            if self.few_shot_examples:
                query += "Here are some examples of the formatting and tone expected:\n"
                prompt_prefix += "Here are some examples of the formatting and tone expected:\n"
                for i, ex in enumerate(self.few_shot_examples, 1):
                    query += f"--- Example {i} ---\nInput:\n{ex['user']}\nOutput:\n{ex['assistant']}\n\n"
                    prompt_prefix += f"--- Example {i} ---\nInput:\n{ex['user']}\nOutput:\n{ex['assistant']}\n\n"
            
            query += (
                "--- Current Task ---\n"
                "Please explain the following case calculations in plain English using clear markdown formatting (bolding, bullet points, and proper paragraph breaks). "
                "Remember: use ONLY the exact figures from the data below. "
                "Do NOT recalculate or verify any numbers.\n"
                "Also, please provide a detailed explanation of the rules for calculating Ongoing Maintenance (OGM).\n\n"
                f"Case Data:\n{user_message}"
            )
            prompt_prefix +=  (
                "--- Current Task ---\n"
                "Please explain the following case calculations in plain English using clear markdown formatting (bolding, bullet points, and proper paragraph breaks). "
                "Remember: use ONLY the exact figures from the data below. "
                "Do NOT recalculate or verify any numbers.\n"
                "Also, please provide a detailed explanation of the rules for calculating Ongoing Maintenance (OGM).\n\n"
                f"Case Data:\n{user_message}"
            )
            
            
            if (1 == 2):
                url = "https://d9ym4p48160x5.cloudfront.net/api/query/generate"
                headers = {
                    "X-API-Key": "dwp-cmg-sec-key-7d9a1f8c",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "qwen_14b_tuned",
                    "query": query,
                    "use_rag": True
                }

                response = requests.post(url, headers=headers, json=payload, timeout=900)
                response.raise_for_status()
                data = response.json()

                # Attempt to extract text from various common backend response formats
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
                    user_message=prompt_prefix + user_message,
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
            
        except requests.exceptions.RequestException as e:
            return {
                "content": f"⚠️ **Calculation Explainer API Error:** {str(e)}",
                "agent": self.AGENT_NAME,
                "status": "error",
                "error": str(e),
            }
        except Exception as e:
            return {
                "content": f"⚠️ **Unexpected Error:** {str(e)}",
                "agent": self.AGENT_NAME,
                "status": "error",
                "error": str(e),
            }
            
        except LLMGatewayError as e:
            return {
                "content": f"⚠️ **Action Advisor Error:** {e.message}",
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

