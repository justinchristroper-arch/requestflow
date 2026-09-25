"""Fulfillment ownership and append-only workflow audit history."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

action = postgresql.ENUM("REQUEST_CREATED", "REQUEST_CANCELLED", "MANAGER_APPROVED", "MANAGER_REJECTED",
    "FINANCE_APPROVAL_REQUIRED", "FINANCE_APPROVED", "FINANCE_REJECTED", "PROCESSING_STARTED",
    "REQUEST_COMPLETED", "HISTORY_BASELINE", name="audit_action", create_type=False)
status = postgresql.ENUM(name="request_status", create_type=False)


def upgrade():
    op.add_column("requests", sa.Column("processing_owner_id", sa.Integer(), nullable=True))
    op.add_column("requests", sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("requests", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_requests_processing_owner", "requests", "users", ["processing_owner_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_requests_processing_owner_id", "requests", ["processing_owner_id"])
    op.create_check_constraint("ck_requests_processing_fields", "requests",
        "(status IN ('PROCESSING', 'COMPLETED') AND processing_owner_id IS NOT NULL AND processing_started_at IS NOT NULL) OR (status NOT IN ('PROCESSING', 'COMPLETED') AND processing_owner_id IS NULL AND processing_started_at IS NULL)")
    op.create_check_constraint("ck_requests_completion_time", "requests",
        "(status = 'COMPLETED' AND completed_at IS NOT NULL) OR (status <> 'COMPLETED' AND completed_at IS NULL)")
    op.create_check_constraint("ck_requests_fulfillment_order", "requests", "completed_at IS NULL OR completed_at >= processing_started_at")
    action.create(op.get_bind(), checkfirst=True)
    op.create_table("audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("requests.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("action", action, nullable=False),
        sa.Column("previous_status", status),
        sa.Column("new_status", status),
        sa.Column("details", sa.String(3000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_request_order", "audit_logs", ["request_id", "created_at", "id"])
    # Do not fabricate actors or timestamps for actions that predate audit logging.
    op.execute("""INSERT INTO audit_logs (request_id, actor_id, action, previous_status, new_status, details)
        SELECT id, NULL, 'HISTORY_BASELINE', NULL, status,
        'Audit tracking enabled at this request state. Earlier actions were not logged; see approval records for existing decisions.'
        FROM requests ORDER BY id""")
    op.execute("""CREATE FUNCTION reject_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Audit history is append-only' USING ERRCODE = '23514';
        END;
        $$""")
    op.execute("CREATE TRIGGER audit_logs_no_update_delete BEFORE UPDATE OR DELETE ON audit_logs FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()")
    op.execute("CREATE TRIGGER audit_logs_no_truncate BEFORE TRUNCATE ON audit_logs FOR EACH STATEMENT EXECUTE FUNCTION reject_audit_mutation()")


def downgrade():
    if op.get_bind().execute(sa.text("SELECT 1 FROM requests WHERE status IN ('PROCESSING', 'COMPLETED') LIMIT 1")).first():
        raise RuntimeError("Cannot downgrade fulfillment while processing/completed requests exist. Use a backup or disposable database.")
    op.drop_table("audit_logs")
    op.execute("DROP FUNCTION reject_audit_mutation()")
    action.drop(op.get_bind(), checkfirst=True)
    for name in ("ck_requests_fulfillment_order", "ck_requests_completion_time", "ck_requests_processing_fields"):
        op.drop_constraint(name, "requests", type_="check")
    op.drop_index("ix_requests_processing_owner_id", table_name="requests")
    op.drop_constraint("fk_requests_processing_owner", "requests", type_="foreignkey")
    op.drop_column("requests", "completed_at")
    op.drop_column("requests", "processing_started_at")
    op.drop_column("requests", "processing_owner_id")
