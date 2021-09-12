import httpx
import pytest

from httpcli.http import http
from httpcli.https import https


@pytest.mark.parametrize('command', [http, https])
async def test_should_get_print_response_in_normal_cases(runner, respx_mock, command):
    data = '<p>Hello world</p>'
    respx_mock.get('https://example.com') % httpx.Response(status_code=200, html=data)
    result = await runner.invoke(command, ['get', 'https://example.com'])

    assert result.exit_code == 0
    output = result.output
    assert 'content-type: text/html; charset=utf-8' in output
    assert f'content-length: {len(data)}' in output
    assert '<p>Hello' in output
    assert 'world</p>' in output


@pytest.mark.parametrize('command', [http, https])
async def test_should_print_head_response_in_normal_cases(runner, respx_mock, command):
    headers = {
        'content-encoding': 'gzip',
        'accept-ranges': 'bytes',
        'content-length': '648'
    }
    respx_mock.head('https://example.com') % httpx.Response(status_code=200, headers=headers)
    result = await runner.invoke(command, ['head', 'https://example.com'])

    assert result.exit_code == 0
    output = result.output
    assert 'HTTP/1.1 200 OK' in output
    assert 'content-encoding: gzip' in output
    assert 'accept-ranges: bytes' in output
    assert 'content-length: 648' in output


@pytest.mark.parametrize('command', [http, https])
async def test_should_print_options_response_in_normal_cases(runner, respx_mock, command):
    headers = {
        'allow': 'OPTIONS, GET, HEAD, POST',
        'content-type': 'text/html; charset=utf-8',
        'server': 'EOS (vny/0452)'
    }
    respx_mock.options('https://example.com') % httpx.Response(status_code=200, headers=headers)
    result = await runner.invoke(command, ['options', 'https://example.com'])

    assert result.exit_code == 0
    output = result.output
    assert 'HTTP/1.1 200 OK' in output
    assert 'allow: OPTIONS, GET, HEAD, POST' in output
    assert 'content-type: text/html; charset=utf-8' in output
    assert 'server: EOS (vny/0452)' in output
