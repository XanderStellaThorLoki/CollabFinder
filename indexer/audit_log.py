"""Audit trail: every read the indexer performs gets a record.

Backs the transparency story with something inspectable. Local JSONL by
default (always works, zero setup); mirrors to BigQuery when configured via
COLLABFINDER_BQ_TABLE (project.dataset.table). BigQuery failures never break
indexing — the local file is the source of truth for the demo.
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

DEFAULT_PATH = Path("audit_log.jsonl")


class AuditLog:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path or os.environ.get("COLLABFINDER_AUDIT_PATH", DEFAULT_PATH))
        self.bq_table = os.environ.get("COLLABFINDER_BQ_TABLE")
        self._bq_client = None
        if self.bq_table:
            try:
                from google.cloud import bigquery
                self._bq_client = bigquery.Client()
            except Exception:
                self._bq_client = None  # local file still records everything

    def record(self, api_method: str, scope: str, detail: str = "") -> None:
        row = {
            "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "api_method": api_method,
            "scope": scope,
            "detail": detail,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        if self._bq_client:
            try:
                self._bq_client.insert_rows_json(self.bq_table, [row])
            except Exception:
                pass
