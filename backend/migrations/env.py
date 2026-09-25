from alembic import context
from sqlalchemy import create_engine, pool

from app.config import DatabaseSettings
from app.database import Base
from app.models import User  # noqa: F401 -- registers the model metadata

config = context.config
target_metadata = Base.metadata


def migrate(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=DatabaseSettings().sqlalchemy_url(), target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
elif config.attributes.get("connection") is not None:
    migrate(config.attributes["connection"])
else:
    engine = create_engine(DatabaseSettings().sqlalchemy_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        migrate(connection)
    engine.dispose()
