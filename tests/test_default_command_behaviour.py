"""In this module we test command behaviour to all http/https subcommands"""
import anyio
import httpx
import pytest

from httpcli.main import http


@pytest.mark.parametrize('method', ['GET', 'HEAD', 'OPTIONS', 'DELETE', 'POST', 'PATCH', 'PUT'])
async def test_should_print_error_when_request_timeout_expired(runner, respx_mock, autojump_clock, method):
    async def side_effect(_):
        await anyio.sleep(6)

    respx_mock.route(method=method, host='example.com').mock(side_effect=side_effect)
    result = await runner.invoke(http, [method.lower(), 'https://example.com'])

    assert result.exit_code == 1
    assert result.output == 'the request timeout has expired\nAborted!\n'


@pytest.mark.parametrize('method', ['GET', 'HEAD', 'OPTIONS', 'DELETE', 'POST', 'PATCH', 'PUT'])
async def test_should_print_error_when_unexpected_httpx_error_happened(runner, respx_mock, method):
    respx_mock.route(method=method, host='example.com').mock(side_effect=httpx.TransportError('just a test error'))
    result = await runner.invoke(http, [method.lower(), 'https://example.com'])

    assert result.exit_code == 1
    assert result.output == 'unexpected error: just a test error\nAborted!\n'
