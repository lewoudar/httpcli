import httpx

from httpcli.main import http


async def test_should_get_print_response_in_normal_cases(runner, respx_mock):
    data = '<p>Hello world</p>'
    respx_mock.get('https://example.com') % httpx.Response(status_code=200, html=data)
    result = await runner.invoke(http, ['get', 'https://example.com'])

    assert result.exit_code == 0
    output = result.output
    assert 'content-type: text/html; charset=utf-8' in output
    assert f'content-length: {len(data)}' in output
    assert '<p>Hello' in output
    assert 'world</p>' in output


async def test_should_print_head_response_in_normal_cases(runner, respx_mock):
    headers = {
        'content-encoding': 'gzip',
        'accept-ranges': 'bytes',
        'content-length': '648'
    }
    respx_mock.head('https://example.com') % httpx.Response(status_code=200, headers=headers)
    result = await runner.invoke(http, ['head', 'https://example.com'])

    assert result.exit_code == 0
    output = result.output
    assert 'HTTP/1.1 200 OK' in output
    assert 'content-encoding: gzip' in output
    assert 'accept-ranges: bytes' in output
    assert 'content-length: 648' in output


async def test_should_print_options_response_in_normal_cases(runner, respx_mock):
    headers = {
        'allow': 'OPTIONS, GET, HEAD, POST',
        'content-type': 'text/html; charset=utf-8',
        'server': 'EOS (vny/0452)'
    }
    respx_mock.options('https://example.com') % httpx.Response(status_code=200, headers=headers)
    result = await runner.invoke(http, ['options', 'https://example.com'])

    assert result.exit_code == 0
    output = result.output
    assert 'HTTP/1.1 200 OK' in output
    assert 'allow: OPTIONS, GET, HEAD, POST' in output
    assert 'content-type: text/html; charset=utf-8' in output
    assert 'server: EOS (vny/0452)' in output
