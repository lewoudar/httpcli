import pytest

from httpcli.http import http
from httpcli.https import https


@pytest.mark.parametrize('command', [http, https])
async def test_should_print_suggestion_when_user_makes_typo(runner, command):
    result = await runner.invoke(command, ['gett', 'https://example.com'])

    assert result.exit_code == 2
    assert '\n\nDid you mean one of these?\n' in result.output
    assert '    • get' in result.output
