import pytest
from pathlib import Path


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Return a bare project root with no files."""
    return tmp_path
