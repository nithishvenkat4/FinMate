"""Unit Tests for FinMate Phase 4 Human-in-the-Loop Approval Engine."""

import datetime
from decimal import Decimal
import uuid
import pytest
from sqlalchemy.orm import Session

from app.models.agent import AgentApproval, AgentTask
from app.models.transaction import Transaction
from app.models.user import User
from app.ai.orchestrator.approval_engine import ApprovalEngine


def test_approval_flow_approve(db_session: Session):
    # 1. Create User and Transaction
    user = User(email="approval_test@finmate.local", name="Approval Tester")
    db_session.add(user)
    db_session.commit()

    tx = Transaction(
        user_id=user.id,
        description="Amazon Prime Subscription",
        amount=Decimal("1499.00"),
        transaction_type="expense",
        category="Other",
        transaction_date=datetime.date.today()
    )
    db_session.add(tx)
    db_session.commit()

    # 2. Create AgentTask and Pending Approval
    task = AgentTask(
        user_id=user.id,
        query="Change Amazon Prime category to Subscriptions",
        intent="MUTATION_PROPOSAL",
        status="waiting_for_user"
    )
    db_session.add(task)
    db_session.commit()

    approval = AgentApproval(
        task_id=task.id,
        user_id=user.id,
        agent_name="TransactionAgent",
        action_type="update_transaction_category",
        target_id=str(tx.id),
        current_value={"category": "Other"},
        proposed_value={"category": "Subscriptions"},
        reason="Amazon Prime is a digital recurring subscription.",
        status="pending",
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    )
    db_session.add(approval)
    db_session.commit()

    engine = ApprovalEngine(db_session)

    # 3. Before approval, verify database is UNCHANGED
    db_session.refresh(tx)
    assert tx.category == "Other"

    # 4. User Approves Action
    res = engine.approve_action(task.id, approval.id, user.id)
    assert res["status"] == "approved"

    # 5. Verify database was mutated to approved state
    db_session.refresh(tx)
    assert tx.category == "Subscriptions"
    db_session.refresh(approval)
    assert approval.status == "approved"
    assert approval.resolved_at is not None


def test_approval_flow_reject(db_session: Session):
    # 1. Create User and Transaction
    user = User(email="reject_test@finmate.local", name="Reject Tester")
    db_session.add(user)
    db_session.commit()

    tx = Transaction(
        user_id=user.id,
        description="Coffee Shop",
        amount=Decimal("300.00"),
        transaction_type="expense",
        category="Food & Dining",
        transaction_date=datetime.date.today()
    )
    db_session.add(tx)
    db_session.commit()

    task = AgentTask(
        user_id=user.id,
        query="Change category",
        intent="MUTATION_PROPOSAL",
        status="waiting_for_user"
    )
    db_session.add(task)
    db_session.commit()

    approval = AgentApproval(
        task_id=task.id,
        user_id=user.id,
        agent_name="TransactionAgent",
        action_type="update_transaction_category",
        target_id=str(tx.id),
        current_value={"category": "Food & Dining"},
        proposed_value={"category": "Entertainment"},
        reason="Test rejection",
        status="pending",
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    )
    db_session.add(approval)
    db_session.commit()

    engine = ApprovalEngine(db_session)

    # User Rejects Action
    res = engine.reject_action(task.id, approval.id, user.id)
    assert res["status"] == "rejected"
    assert res["database_changed"] is False

    # Verify database remains UNCHANGED
    db_session.refresh(tx)
    assert tx.category == "Food & Dining"
    db_session.refresh(approval)
    assert approval.status == "rejected"


def test_approval_expiration_blocking(db_session: Session):
    user = User(email="expire_test@finmate.local", name="Expire Tester")

    db_session.add(user)
    db_session.commit()

    task = AgentTask(user_id=user.id, query="Test expire", intent="MUTATION_PROPOSAL")
    db_session.add(task)
    db_session.commit()

    # Expired 20 minutes ago
    expired_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=20)
    approval = AgentApproval(
        task_id=task.id,
        user_id=user.id,
        agent_name="TransactionAgent",
        action_type="update_transaction_category",
        target_id=str(uuid.uuid4()),
        current_value={"category": "Old"},
        proposed_value={"category": "New"},
        reason="Expired test",
        status="pending",
        expires_at=expired_time
    )
    db_session.add(approval)
    db_session.commit()

    engine = ApprovalEngine(db_session)

    with pytest.raises(TimeoutError) as exc_info:
        engine.approve_action(task.id, approval.id, user.id)
    assert "expired" in str(exc_info.value).lower()
