"""Automated Evaluation Runner for FinMate Phase 4 Agent Tasks Benchmark."""

import json
import os
import uuid
import pytest
from app.ai.orchestrator.orchestrator import AIOrchestrator

EVALUATION_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "app", "ai", "data", "evaluation", "agent_tasks.json"
)


def load_evaluation_tasks():
    with open(EVALUATION_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["tasks"]


@pytest.mark.asyncio
async def test_agent_benchmark_evaluation_suite():
    tasks = load_evaluation_tasks()
    assert len(tasks) >= 10

    orchestrator = AIOrchestrator()
    user_id = uuid.uuid4()

    passed_count = 0
    evaluation_report = []

    for task in tasks:
        query = task["query"]
        expected_intent = task["expected_intent"]
        expected_primary_agent = task["expected_primary_agent"]
        requires_approval = task["requires_approval"]

        res = await orchestrator.execute_task(query, user_id)

        # Check Intent
        intent_match = (res["intent"] == expected_intent)

        # Check Agent Selection
        agent_match = any(agent in res["agents_used"] for agent in task["allowed_agents"])

        # Check Approval Requirement
        if requires_approval:
            approval_match = (res["status"] == "waiting_for_user" and res["pending_approval"] is not None)
        else:
            approval_match = True

        task_passed = intent_match and agent_match and approval_match
        if task_passed:
            passed_count += 1

        evaluation_report.append({
            "task_id": task["id"],
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": res["intent"],
            "agents_used": res["agents_used"],
            "status": res["status"],
            "passed": task_passed
        })

    accuracy = (passed_count / len(tasks)) * 100.0
    print(f"\nPhase 4 Agent Benchmark Accuracy: {passed_count}/{len(tasks)} ({accuracy:.1f}%)")
    assert accuracy >= 90.0, f"Agent evaluation accuracy was {accuracy}%, expected >= 90%"
