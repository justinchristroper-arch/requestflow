"""Create users with roles and a self-referencing manager relationship."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

roles = postgresql.ENUM("EMPLOYEE", "MANAGER", "FINANCE", "PROCUREMENT", "ADMIN",
                        name="user_role", create_type=False)


def upgrade():
    roles.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", roles, nullable=False),
        sa.Column("manager_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("email = lower(trim(email))", name="ck_users_email_normalized"),
        sa.CheckConstraint("manager_id IS NULL OR manager_id <> id", name="ck_users_not_own_manager"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_manager_id", "users", ["manager_id"])


def downgrade():
    op.drop_table("users")
    roles.drop(op.get_bind(), checkfirst=True)
