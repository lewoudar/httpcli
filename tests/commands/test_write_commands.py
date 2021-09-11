import httpx

from httpcli.main import http


async def test_should_print_delete_response_in_normal_cases(runner, respx_mock):
    respx_mock.delete('https://foo.com') % httpx.Response(status_code=204)
    result = await runner.invoke(http, ['delete', 'https://foo.com'])

    assert result.exit_code == 0
    assert 'HTTP/1.1 204 No Content' in result.output
