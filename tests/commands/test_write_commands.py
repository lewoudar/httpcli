import pytest

from httpcli.main import http


async def test_should_print_delete_response_in_normal_cases(runner, respx_mock):
    respx_mock.delete('https://foo.com') % 204
    result = await runner.invoke(http, ['delete', 'https://foo.com'])

    assert result.exit_code == 0
    assert 'HTTP/1.1 204 No Content' in result.output


@pytest.mark.parametrize('method', ['POST'])
@pytest.mark.parametrize(('mock_argument', 'cli_argument'), [
    ({'data': {'foo': 'bar', 'hello': 'world'}}, ['-f', 'foo:bar', '-f', 'hello:world']),
    ({'json': {'foo': 'bar', 'hello': 'world'}}, ['-j', 'foo:bar', '-j', 'hello:world']),
    ({'content': b'pineapple'}, ['-r', 'pineapple'])
])
async def test_should_print_response_in_normal_cases(runner, respx_mock, method, mock_argument, cli_argument):
    respx_mock.route(method=method, host='pie.dev', **mock_argument) % dict(json={'hello': 'world'})
    result = await runner.invoke(http, [method.lower(), 'https://pie.dev', *cli_argument])

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
