"""Test cases for the __main__ module."""
import pytest
from click.testing import CliRunner

from api_reader import __main__


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()

def test_math():
    assert 1==1
