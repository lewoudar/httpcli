import anyio
import httpx

from httpcli.main import http


async def test_should_print_error_when_request_timeout_expired(runner, respx_mock, autojump_clock):
    async def side_effect(_):
        await anyio.sleep(6)

    respx_mock.route(method='GET', host='example.com').mock(side_effect=side_effect)
    result = runner.invoke(http, ['get', 'https://example.com'])

    assert result.exit_code == 1
    print(result.exception)
    assert result.output == 'the request timeout has expired\nAborted!\n'


async def test_should_print_error_when_unexpected_httpx_error_happened(runner, respx_mock):
    respx_mock.route(method='GET', host='example.com').mock(side_effect=httpx.TransportError('just a test error'))
    result = runner.invoke(http, ['get', 'https://example.com'])

    assert result.exit_code == 1
    print(result.exception)
    print(result.output)
