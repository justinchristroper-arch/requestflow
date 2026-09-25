from alembic import command
from sqlalchemy import inspect, text

from conftest import isolated_schema, migration_config


def test_fresh_upgrade_downgrade_and_upgrade():
    with isolated_schema() as connection:
        config = migration_config(connection)
        command.upgrade(config, "head")
        assert "users" in inspect(connection).get_table_names()
        assert {"users", "requests", "approvals", "audit_logs"} <= set(inspect(connection).get_table_names())
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0003"
        command.check(config)
        command.downgrade(config, "0002")
        assert "audit_logs" not in inspect(connection).get_table_names()
        assert "processing_owner_id" not in {column["name"] for column in inspect(connection).get_columns("requests")}
        command.upgrade(config, "head")
        command.downgrade(config, "0001")
        assert "users" in inspect(connection).get_table_names()
        assert "requests" not in inspect(connection).get_table_names()
        assert connection.scalar(text("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relname='request_number_seq' AND n.nspname=current_schema()")) == 0
        command.upgrade(config, "head")
        command.downgrade(config, "base")
        assert "users" not in inspect(connection).get_table_names()
        assert connection.scalar(text("SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE t.typname='user_role' AND n.nspname=current_schema()")) == 0
        command.upgrade(config, "head")
        assert "users" in inspect(connection).get_table_names()
