"""enums, cascade delete, indexes

Каскадное удаление алертов (A1), индексы под сортировку и джойн (Б7) и проверка
значений статусов на стороне базы (Б5).

Ограничения CHECK и параметр ``ondelete`` у внешнего ключа alembic сравнивать не умеет,
поэтому обе части дописаны руками поверх автогенерации.

Revision ID: 18c18e2d3bf6
Revises: 0d6439d2e79f
Create Date: 2026-09-03 20:57:33.566302

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "18c18e2d3bf6"
down_revision: str | Sequence[str] | None = "0d6439d2e79f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROCESSING_STATUSES = ("uploaded", "processing", "processed", "failed")
SCAN_STATUSES = ("clean", "suspicious", "failed")
ALERT_LEVELS = ("info", "warning", "critical")


def _in_list(column: str, values: tuple[str, ...]) -> str:
    return "{} IN ({})".format(column, ", ".join(f"'{value}'" for value in values))


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f("ix_alerts_created_at"), "alerts", ["created_at"], unique=False)
    op.create_index(op.f("ix_alerts_file_id"), "alerts", ["file_id"], unique=False)
    op.create_index(op.f("ix_files_created_at"), "files", ["created_at"], unique=False)

    op.drop_constraint(op.f("alerts_file_id_fkey"), "alerts", type_="foreignkey")
    op.create_foreign_key(
        "alerts_file_id_fkey",
        "alerts",
        "files",
        ["file_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_check_constraint(
        "ck_files_processing_status", "files", _in_list("processing_status", PROCESSING_STATUSES)
    )
    op.create_check_constraint(
        "ck_files_scan_status", "files", _in_list("scan_status", SCAN_STATUSES)
    )
    op.create_check_constraint("ck_alerts_level", "alerts", _in_list("level", ALERT_LEVELS))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_alerts_level", "alerts", type_="check")
    op.drop_constraint("ck_files_scan_status", "files", type_="check")
    op.drop_constraint("ck_files_processing_status", "files", type_="check")

    op.drop_constraint("alerts_file_id_fkey", "alerts", type_="foreignkey")
    op.create_foreign_key(op.f("alerts_file_id_fkey"), "alerts", "files", ["file_id"], ["id"])

    op.drop_index(op.f("ix_files_created_at"), table_name="files")
    op.drop_index(op.f("ix_alerts_file_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_created_at"), table_name="alerts")
