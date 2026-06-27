import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import Base


def test_models_import_builds_metadata():
    assert "opportunities" in Base.metadata.tables
    assert "quotations" in Base.metadata.tables
