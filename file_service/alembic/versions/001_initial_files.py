"""Initial files table

Revision ID: 001_initial_files
Revises: 
Create Date:

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_files'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL,
            filename VARCHAR(255) NOT NULL,
            file_key VARCHAR(500) NOT NULL UNIQUE,
            content_type VARCHAR(100) NOT NULL,
            size_bytes BIGINT NOT NULL,
            uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
            uploaded_by VARCHAR(100)
        )
    """)
    
    op.execute("CREATE INDEX IF NOT EXISTS ix_files_id ON files(id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_files_task_id ON files(task_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_files_task_id")
    op.execute("DROP INDEX IF EXISTS ix_files_id")
    op.execute("DROP TABLE IF EXISTS files")
