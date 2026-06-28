"""
LLM API Gateway — Custom interface for fine-tuned LLM API.
"""

import json
import time
import requests
from typing import Optional


class LLMGatewayError(Exception):
    """Custom exception for LLM Gateway errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class LLMGateway:
    """
    Custom LLM API Gateway.

    Integrates with the specific fine-tuned model endpoint.
    """

    def __init__(
        self,
        api_key: str,
        api_url: str,
        model: str = "qwen_14b_tuned",
        max_retries: int = 3,
        timeout: int = 900,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

    def _build_headers(self) -> dict:
        """Build request headers with authentication."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Connection": "close",
        }

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        few_shot_examples: Optional[list[dict]] = None,
        model: Optional[str] = None,
    ) -> dict:
        """
        Send a completion request to an OpenAI-compatible API (like LM Studio).

        Args:
            system_prompt: The system prompt for the agent.
            user_message: The user's message (typically the case JSON).
            few_shot_examples: Optional list of {"user": ..., "assistant": ...} dicts.

        Returns:
            dict with 'content' (str), 'model' (str), 'usage' (dict).

        Raises:
            LLMGatewayError: If the API call fails after retries.
        """
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if few_shot_examples:
            for example in few_shot_examples:
                messages.append({"role": "user", "content": example['user']})
                messages.append({"role": "assistant", "content": example['assistant']})
                
        messages.append({"role": "user", "content": user_message})

        headers = self._build_headers()
        payload = {
            "model": model if model else self.model,
            "messages": messages,
            "temperature": 0.3,
            "stream": False,
        }

        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    data = response.json()
                    content = ""
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0].get("message", {}).get("content", "")
                    elif "response" in data:
                        content = data["response"]
                        
                    return {
                        "content": content,
                        "model": data.get("model", model if model else self.model),
                        "usage": data.get("usage", {}),
                        "provider": "openai_compatible",
                    }

                # Handle specific error codes
                error_body = ""
                try:
                    error_data = response.json()
                    error_body = json.dumps(error_data)
                except (json.JSONDecodeError, KeyError):
                    error_body = response.text[:500]

                if response.status_code == 401 or response.status_code == 403:
                    # Provide a robust mock fallback for demo mode
                    agent_type = "AI Assistant"
                    if "summarizer" in system_prompt.lower() or "summary" in system_prompt.lower():
                        agent_type = "Case Summarizer"
                        mock_text = "This is a simulated summary. The case involves standard components and the non-resident parent has a steady income source."
                    elif "explain" in system_prompt.lower() or "calculat" in system_prompt.lower():
                        agent_type = "Calculation Explainer"
                        mock_text = "This is a simulated calculation explanation. The total monthly schedule is based on the gross weekly income, minus standard deductions."
                    elif "advis" in system_prompt.lower() or "action" in system_prompt.lower():
                        agent_type = "Action Advisor"
                        mock_text = "This is a simulated action advice. Proceed with standard collection procedures. If arrears exist, consider enforcement actions."
                    else:
                        mock_text = "This is a simulated response because the endpoint is currently offline."

                    return {
                        "content": f"⚠️ **Demo Mode Fallback ({agent_type})**\n\nThe actual API returned a {response.status_code} Authentication error. Here is a simulated response:\n\n{mock_text}",
                        "model": "qwen_14b_mock",
                        "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
                        "provider": "mock",
                    }

                if response.status_code == 429:
                    # Rate limited — wait and retry
                    wait_time = min(2**attempt, 30)
                    time.sleep(wait_time)
                    last_error = LLMGatewayError(
                        f"Rate limited. Retrying in {wait_time}s...",
                        status_code=429,
                    )
                    continue

                if response.status_code >= 500:
                    # Server error — retry
                    wait_time = min(2**attempt, 15)
                    time.sleep(wait_time)
                    last_error = LLMGatewayError(
                        f"Server error: {error_body}",
                        status_code=response.status_code,
                    )
                    continue

                # Other client errors — don't retry
                raise LLMGatewayError(
                    f"API error ({response.status_code}): {error_body}",
                    status_code=response.status_code,
                )

            except requests.exceptions.Timeout:
                last_error = LLMGatewayError(
                    f"Request timed out after {self.timeout}s."
                )
                continue

            except requests.exceptions.ConnectionError:
                last_error = LLMGatewayError(
                    "Could not connect to the API. Check your network."
                )
                if attempt < self.max_retries:
                    time.sleep(2)
                continue

            except LLMGatewayError:
                raise  # Re-raise authentication errors immediately

            except Exception as e:
                last_error = LLMGatewayError(
                    f"Unexpected error: {str(e)}"
                )
                continue

        # All retries exhausted
        raise last_error or LLMGatewayError(
            f"Failed to get a response after {self.max_retries} attempts."
        )
