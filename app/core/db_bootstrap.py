import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_CHECKS_COLUMNS = {
    "name_lookup_ms": "FLOAT",
    "connection_ms": "FLOAT",
    "tls_ms": "FLOAT",
    "transfer_ms": "FLOAT",
    "total_ms": "FLOAT",
    "breakdown_unavailable": "BOOLEAN",
}
_ensured = False


def ensure_checks_timing_columns(engine: Engine) -> None:
    """Best-effort ensure timing columns exist without manual migrations."""
    global _ensured
    if _ensured:
        return
    _ensured = True

    try:
        inspector = inspect(engine)
        if "checks" not in inspector.get_table_names():
            return
        existing = {col["name"] for col in inspector.get_columns("checks")}
        missing = [name for name in _CHECKS_COLUMNS if name not in existing]
        if not missing:
            return

        dialect = engine.dialect.name
        float_type = "DOUBLE PRECISION" if dialect == "postgresql" else "REAL"
        bool_type = "BOOLEAN"

        with engine.begin() as conn:
            for name in missing:
                column_type = float_type if _CHECKS_COLUMNS[name] == "FLOAT" else bool_type
                conn.execute(text(f"ALTER TABLE checks ADD COLUMN {name} {column_type}"))
        logger.info("Added missing checks timing columns: %s", ", ".join(missing))
    except Exception as exc:
        logger.warning("Failed to ensure checks timing columns: %s", exc)
