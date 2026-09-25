"""Requests, approval stages, and concurrency-safe request numbering."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

category = postgresql.ENUM("HARDWARE", "SOFTWARE", "ACCESS", "REPAIR_MAINTENANCE", "OTHER", name="request_category", create_type=False)
priority = postgresql.ENUM("LOW", "MEDIUM", "HIGH", name="request_priority", create_type=False)
status = postgresql.ENUM("DRAFT", "PENDING_MANAGER_APPROVAL", "PENDING_FINANCE_APPROVAL", "APPROVED", "PROCESSING", "COMPLETED", "REJECTED", "CANCELLED", name="request_status", create_type=False)
approval_type = postgresql.ENUM("MANAGER", "FINANCE", name="approval_type", create_type=False)
approval_status = postgresql.ENUM("PENDING", "APPROVED", "REJECTED", "CANCELLED", name="approval_status", create_type=False)
enums = (category, priority, status, approval_type, approval_status)


def upgrade():
    for enum in enums:
        enum.create(op.get_bind(), checkfirst=True)
    op.execute(sa.schema.CreateSequence(sa.Sequence("request_number_seq")))
    op.create_table(
        "requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_number", sa.String(40), nullable=False),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category", category, nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("business_justification", sa.Text(), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(15, 2), nullable=False),
        sa.Column("priority", priority, nullable=False),
        sa.Column("status", status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("estimated_cost >= 0", name="ck_requests_cost_nonnegative"),
    )
    for column in ("request_number", "requester_id", "status", "created_at"):
        op.create_index(f"ix_requests_{column}", "requests", [column], unique=column == "request_number")
    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("requests.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("approval_type", approval_type, nullable=False),
        sa.Column("status", approval_status, nullable=False),
        sa.Column("comment", sa.String(2000)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("request_id", "approval_type", name="uq_approvals_request_stage"),
        sa.CheckConstraint("status <> 'REJECTED' OR (comment IS NOT NULL AND length(trim(comment)) > 0)", name="ck_approvals_reject_reason"),
        sa.CheckConstraint("(status = 'PENDING' AND decided_at IS NULL) OR (status <> 'PENDING' AND decided_at IS NOT NULL)", name="ck_approvals_decision_time"),
        sa.CheckConstraint("approval_type <> 'MANAGER' OR approver_id IS NOT NULL", name="ck_approvals_manager_assigned"),
        sa.CheckConstraint("status NOT IN ('APPROVED', 'REJECTED') OR approver_id IS NOT NULL", name="ck_approvals_decider_required"),
    )
    for column in ("request_id", "approver_id", "status"):
        op.create_index(f"ix_approvals_{column}", "approvals", [column])


def downgrade():
    op.drop_table("approvals")
    op.drop_table("requests")
    op.execute(sa.schema.DropSequence(sa.Sequence("request_number_seq")))
    for enum in reversed(enums):
        enum.drop(op.get_bind(), checkfirst=True)
