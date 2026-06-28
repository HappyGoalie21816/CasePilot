"""
Action Advisor Agent.

Analyzes case context to classify enforcement risk,
suggest negotiation options, and recommend next steps
for the caseworker.
"""

import json
from typing import Optional
from llm.gateway import LLMGateway, LLMGatewayError
from prompts.system_prompts import get_agent_config


class ActionAdvisorAgent:
    """
    Agent that provides enforcement risk classification and
    actionable recommendations to caseworkers.

    Analyzes arrears levels, payment compliance, and case context
    to determine risk and suggest appropriate actions.
    """

    AGENT_NAME = "action_advisor"

    def __init__(self, gateway: LLMGateway):
        self.gateway = gateway
        config = get_agent_config(self.AGENT_NAME)
        self.system_prompt = config["system_prompt"]
        self.few_shot_examples = config["few_shot_examples"]

    def _prepare_payload(self, case_data: dict) -> str:
        """
        Extract enforcement-relevant data from the case JSON.

        Focuses on: arrears, payment history, compliance rates,
        contact details, income, and case stage.
        """
        master = case_data.get("masterCase", case_data)
        cases = master.get("cases", [])

        payload_parts = []

        for case in cases:
            contacts_summary = []
            for contact in case.get("contacts", []):
                contact_info = {
                    "role": contact.get("role"),
                    "name": contact.get("fullName"),
                }
                if "financialDetails" in contact:
                    contact_info["financialDetails"] = contact["financialDetails"]
                contacts_summary.append(contact_info)

            case_info = {
                "caseNumber": case.get("caseNumber", "Unknown"),
                "caseStage": case.get("caseStage"),
                "caseStatus": case.get("caseStatus"),
                "caseSubStatus": case.get("caseSubStatus"),
                "serviceType": case.get("serviceType"),
                "contacts": contacts_summary,
                "calculations": case.get("calculations", {}).get("outputs", {}),
                "arrearsDetails": case.get("arrearsDetails", {}),
                "methodOfPayment": case.get("methodOfPayment", {}),
                "serviceRequests": case.get("serviceRequests", []),
            }
            payload_parts.append(case_info)

        return json.dumps(
            {
                "masterCaseId": master.get("id", master.get("masterCaseNumber", "Unknown")),
                "nrpName": master.get("nrp", {}).get("name", "Unknown"),
                "grossWeeklyIncome": master.get("grossWeeklyIncome"),
                "incomeSource": master.get("incomeSource"),
                "weeklyLiability": master.get("weeklyLiabilityAmount"),
                "activeCases": master.get("activeCasesCount"),
                "cases": payload_parts,
            },
            indent=2,
        )

    def run(self, case_data: dict, model: Optional[str] = None) -> dict:
        """
        Run the Action Advisor agent.

        Args:
            case_data: The full case JSON payload.

        Returns:
            dict with 'content' (str), 'agent' (str), 'status' (str).
        """
        import requests
        try:
            user_message = self._prepare_payload(case_data)

            prompt_prefix = (
                "Analyze the following case data and provide enforcement risk "
                "classification with actionable recommendations. Base your analysis "
                "ONLY on the data provided.\n\n"
            )
            query_prefix = (
                "Analyze the following case data and provide enforcement risk "
                "classification with actionable recommendations. Base your analysis "
                "ONLY on the data provided.\n\n"
            )
            
            query = self._prepare_payload(case_data)
            query = query_prefix + query
             
            if (1 == 1):
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
