import json
import logging
from pathlib import Path

from sqlalchemy import create_engine

from ..config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, future=True)


def initialize_database() -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        logger.warning("schema.sql not found — skipping initialization.")
        return
    try:
        with engine.begin() as conn:
            for stmt in schema_path.read_text(encoding="utf-8").split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.exec_driver_sql(stmt)
        logger.info("Database initialized.")
    except Exception:
        logger.exception("Failed to initialize database.")
        raise


def get_schema_metadata() -> dict:
    path = Path(__file__).parent / "schema.json"
    if not path.exists():
        logger.warning("schema.json not found — returning empty metadata.")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
