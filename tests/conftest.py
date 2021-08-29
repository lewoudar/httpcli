from click.testing import CliRunner
import pytest


@pytest.fixture()
def runner():
    """CLI test runner"""
    return CliRunner()
