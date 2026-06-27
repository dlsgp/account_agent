from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260627_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "expense_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("payment_amount", sa.Integer(), nullable=False),
        sa.Column("my_share", sa.Integer(), nullable=False),
        sa.Column("people_count", sa.Integer(), nullable=True),
        sa.Column("paid_by_me", sa.Boolean(), nullable=False),
        sa.Column("receivable_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payable_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("type", sa.String(length=20), nullable=False, server_default="expense"),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column("raw_input", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_expense_records_date", "expense_records", ["date"])
    op.create_index("ix_expense_records_category", "expense_records", ["category"])

    op.create_table(
        "receivables",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("expense_id", sa.Integer(), nullable=False),
        sa.Column("person_name", sa.String(length=80), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["expense_id"], ["expense_records.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_receivables_expense_id", "receivables", ["expense_id"])
    op.create_index("ix_receivables_person_name", "receivables", ["person_name"])
    op.create_index("ix_receivables_status", "receivables", ["status"])


def downgrade() -> None:
    op.drop_index("ix_receivables_status", table_name="receivables")
    op.drop_index("ix_receivables_person_name", table_name="receivables")
    op.drop_index("ix_receivables_expense_id", table_name="receivables")
    op.drop_table("receivables")
    op.drop_index("ix_expense_records_category", table_name="expense_records")
    op.drop_index("ix_expense_records_date", table_name="expense_records")
    op.drop_table("expense_records")
