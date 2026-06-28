"""
Agent Orchestrator.

Dispatches case data to all 3 specialized agents in parallel
using ThreadPoolExecutor, then merges the results.

Uses 'allSettled' semantics — if one agent fails, the others
still return their results.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from llm.gateway import LLMGateway
from agents.calculation_explainer import CalculationExplainerAgent
from agents.action_advisor import ActionAdvisorAgent
from agents.case_summarizer import CaseSummarizerAgent


class AgentOrchestrator:
    """
    Orchestrates the multi-agent system.

    Runs all 3 agents (Calculation Explainer, Action Advisor,
    Case Summarizer) in parallel and merges results.
    """

    AGENT_TIMEOUT = 900  # seconds per agent

    def __init__(self, gateway: LLMGateway):
        self.gateway = gateway
        self.agents = {
            "calculation_explainer": CalculationExplainerAgent(gateway),
            "action_advisor": ActionAdvisorAgent(gateway),
            "case_summarizer": CaseSummarizerAgent(gateway),
        }

    def run_single_agent(self, agent_name: str, case_data: dict, model: Optional[str] = None) -> dict:
        """
        Run a single named agent.

        Args:
            agent_name: One of 'calculation_explainer', 'action_advisor', 'case_summarizer'.
            case_data: The case JSON payload.
            model: Optional model override.

        Returns:
            Agent result dict.
        """
        if agent_name not in self.agents:
            return {
                "content": f"⚠️ Unknown agent: {agent_name}",
                "agent": agent_name,
                "status": "error",
            }

        return self.agents[agent_name].run(case_data, model=model)

    def run_all(
        self,
        case_data: dict,
        agents: Optional[list[str]] = None,
        agent_models: Optional[dict[str, str]] = None,
    ) -> dict:
        """
        Run multiple agents in parallel and merge results.

        Args:
            case_data: The case JSON payload.
            agents: Optional list of agent names to run. Defaults to all.
            agent_models: Optional dict mapping agent name to model string.

        Returns:
            dict with:
              'results': {agent_name: result_dict, ...}
              'timing': {agent_name: seconds, ...}
              'total_time': float
              'status': 'success' | 'partial' | 'error'
        """
        agent_names = agents or list(self.agents.keys())
        agent_models = agent_models or {}
        results = {}
        timing = {}
        start_total = time.time()

        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all agents
            futures = {}
            start_times = {}
            for name in agent_names:
                if name in self.agents:
                    start_times[name] = time.time()
                    model = agent_models.get(name)
                    futures[executor.submit(self.agents[name].run, case_data, model=model)] = name

            # Collect results as they complete
            try:
                for future in as_completed(futures, timeout=self.AGENT_TIMEOUT):
                    agent_name = futures[future]
                    agent_start = start_times[agent_name]
                    try:
                        result = future.result(timeout=self.AGENT_TIMEOUT)
                        results[agent_name] = result
                    except Exception as e:
                        results[agent_name] = {
                            "content": f"⚠️ **Agent '{agent_name}' failed:** {str(e)}",
                            "agent": agent_name,
                            "status": "error",
                            "error": str(e),
                        }
                    timing[agent_name] = round(time.time() - agent_start, 2)
            except TimeoutError:
                for future, agent_name in futures.items():
                    if agent_name not in results:
                        results[agent_name] = {
                            "content": f"⚠️ **Agent '{agent_name}' timed out after {self.AGENT_TIMEOUT} seconds.**",
                            "agent": agent_name,
                            "status": "error",
                            "error": "TimeoutError",
                        }
                        timing[agent_name] = self.AGENT_TIMEOUT

        total_time = round(time.time() - start_total, 2)

        # Determine overall status
        statuses = [r.get("status") for r in results.values()]
        if all(s == "success" for s in statuses):
            overall_status = "success"
        elif any(s == "success" for s in statuses):
            overall_status = "partial"
        else:
            overall_status = "error"

        return {
            "results": results,
            "timing": timing,
            "total_time": total_time,
            "status": overall_status,
        }
