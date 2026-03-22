import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from logos_batch import LogosBatchReader

def test_volume_info():
    """Should return metadata for an encrypted volume."""
    reader = LogosBatchReader()
    try:
        info = reader.volume_info("FIGURATIVE-LANGUAGE.lbssd")
        assert info is not None, "volume_info returned None"
        assert "ResourceId" in info or "DriverName" in info
    finally:
        reader.close()

def test_query_dataset_tables():
    """Should list tables in an encrypted volume's database."""
    reader = LogosBatchReader()
    try:
        rows = reader.query_dataset(
            "FIGURATIVE-LANGUAGE.lbssd",
            "SupplementalData.db",
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        assert len(rows) > 0, "Expected at least one table"
        table_names = [r.get("name", "") for r in rows]
        assert any("Reference" in t or "Attachment" in t or "Resource" in t for t in table_names), \
            f"Expected study data tables, got {table_names}"
    finally:
        reader.close()

def test_query_dataset_content():
    """Should return actual data from a supplemental data query."""
    reader = LogosBatchReader()
    try:
        # First, discover the schema
        rows = reader.query_dataset(
            "FIGURATIVE-LANGUAGE.lbssd",
            "SupplementalData.db",
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        assert len(rows) > 0
        # Then query the first table for a few rows
        first_table = rows[0]["name"]
        data = reader.query_dataset(
            "FIGURATIVE-LANGUAGE.lbssd",
            "SupplementalData.db",
            f"SELECT * FROM [{first_table}] LIMIT 5"
        )
        assert len(data) > 0, f"Expected data from {first_table}"
    finally:
        reader.close()
