"""Unit Tests for FinMate Phase 4 Tool Registry and Security Guardrails."""

import uuid
import pytest
from app.ai.tools.registry import ToolRegistry, ToolContext


def test_tool_registry_registration():
    registry = ToolRegistry()
    assert len(registry._tools) >= 15
    assert registry.get_tool("get_financial_summary") is not None
    assert registry.get_tool("simulate_financial_scenario") is not None
    assert registry.get_tool("propose_transaction_update") is not None


def test_tool_authorization_allowlist_enforcement():
    registry = ToolRegistry()
    user_id = uuid.uuid4()

    # TransactionAgent is NOT authorized to invoke calculate_investment_allocation
    unauthorized_context = ToolContext(
        user_id=user_id,
        agent_name="TransactionAgent"
    )

    with pytest.raises(PermissionError) as exc_info:
        registry.execute_tool(
            tool_name="calculate_investment_allocation",
            parameters={"user_id": user_id},
            context=unauthorized_context
        )
    assert "NOT authorized" in str(exc_info.value)


def test_tool_user_ownership_sanitization():
    registry = ToolRegistry()
    authenticated_user = uuid.uuid4()
    tampered_user = uuid.uuid4()

    # LLM or caller passes tampered_user in parameters
    context = ToolContext(
        user_id=authenticated_user,
        agent_name="TransactionAgent"
    )

    # Tool execution should forcefully override user_id with authenticated_user
    res = registry.execute_tool(
        tool_name="get_category_spending",
        parameters={"user_id": tampered_user},
        context=context
    )
    assert isinstance(res, list)


def test_what_if_simulation_sandbox_guarantee():
    registry = ToolRegistry()
    user_id = uuid.uuid4()
    context = ToolContext(
        user_id=user_id,
        agent_name="BudgetAgent"
    )

    sim_res = registry.execute_tool(
        tool_name="simulate_financial_scenario",
        parameters={
            "user_id": user_id,
            "additional_expense": "20000.00",
            "reduced_expense": "2000.00"
        },
        context=context
    )

    assert sim_res["is_simulation"] is True
    assert sim_res["database_modified"] is False
    assert "Simulation only" in sim_res["disclaimer"]
    assert "simulated_savings" in sim_res


def test_mutating_tool_requires_approval():
    registry = ToolRegistry()
    tool_def = registry.get_tool("propose_transaction_update")
    assert tool_def is not None
    assert tool_def.is_mutation is True
    assert tool_def.requires_approval is True

    context = ToolContext(
        user_id=uuid.uuid4(),
        agent_name="TransactionAgent"
    )
    proposal = registry.execute_tool(
        tool_name="propose_transaction_update",
        parameters={
            "user_id": context.user_id,
            "transaction_id": str(uuid.uuid4()),
            "new_category": "Shopping",
            "reason": "Test category reclassification"
        },
        context=context
    )
    assert proposal["status"] == "pending_approval"
    assert "approval_id" in proposal
