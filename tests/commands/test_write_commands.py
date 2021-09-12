import httpx
import pytest

from httpcli.http import http
from httpcli.https import https


@pytest.mark.parametrize('command', [http, https])
async def test_should_print_delete_response_in_normal_cases(runner, respx_mock, command):
    respx_mock.delete('https://foo.com') % 204
    result = await runner.invoke(command, ['delete', 'https://foo.com'])

    assert result.exit_code == 0
    assert 'HTTP/1.1 204 No Content' in result.output


@pytest.mark.parametrize('method', ['POST', 'PATCH', 'PUT'])
@pytest.mark.parametrize(('mock_argument', 'cli_argument'), [
    ({'data': {'foo': 'bar', 'hello': 'world'}}, ['-f', 'foo:bar', '-f', 'hello:world']),
    ({'json': {'foo': 'bar', 'hello': 'world'}}, ['-j', 'foo:bar', '-j', 'hello:world']),
    ({'content': b'pineapple'}, ['-r', 'pineapple'])
])
@pytest.mark.parametrize('command', [http, https])
async def test_should_print_response_in_normal_cases(runner, respx_mock, method, mock_argument, cli_argument, command):
    respx_mock.route(method=method, host='pie.dev', **mock_argument) % dict(json={'hello': 'world'})
    result = await runner.invoke(command, [method.lower(), 'https://pie.dev', *cli_argument])

    assert result.exit_code == 0
    output = result.output
    lines = [
        'content-length: 18',
        'content-type: application/json',
        '{',
        'hello',
        'world',
        '}'
    ]
    for line in lines:
        assert line in output


@pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH'])
@pytest.mark.parametrize('command', [http, https])
async def test_should_print_response_when_sending_file(runner, tmp_path, respx_mock, method, command):
    async def side_effect(request: httpx.Request) -> httpx.Response:
        assert request.headers['content-type'].startswith('multipart/form-data')
        return httpx.Response(200, json={'hello': 'world'})

    path = tmp_path / 'file.txt'
    path.write_text('hello')
    respx_mock.route(method=method, host='pie.dev').mock(side_effect=side_effect)
    result = await runner.invoke(command, [method.lower(), 'https://pie.dev', '-f', f'file:@{path}'])

    assert result.exit_code == 0
    output = result.output
    lines = [
        'content-length: 18',
        'content-type: application/json',
        '{',
        'hello',
        'world',
        '}'
    ]
    for line in lines:
        assert line in output
