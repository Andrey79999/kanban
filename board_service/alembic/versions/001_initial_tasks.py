"""Initial tasks table

Revision ID: 001_initial_tasks
Revises: 
Create Date:

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_tasks'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type first
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE taskstatus AS ENUM ('todo', 'in_progress', 'done');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$
    """)
    
    # Create table
    op.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            status taskstatus NOT NULL DEFAULT 'todo',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_id ON tasks(id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tasks_status")
    op.execute("DROP INDEX IF EXISTS ix_tasks_id")
    op.execute("DROP TABLE IF EXISTS tasks")
    op.execute("DROP TYPE IF EXISTS taskstatus")
