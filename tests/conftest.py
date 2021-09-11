import pytest
from asyncclick.testing import CliRunner


@pytest.fixture()
def runner():
    """CLI test runner"""
    return CliRunner()
