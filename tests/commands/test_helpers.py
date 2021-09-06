import json

import anyio
import click
import httpx
import pytest

from httpcli.commands.helpers import guess_lexer_name, get_response_headers_text, print_response, perform_read_request
from httpcli.configuration import Configuration


class TestGuessLexerName:
    """Tests function guess_lexer_name"""

    def test_should_return_empty_lexer_name_when_no_content_type_is_given(self):
        response = httpx.Response(status_code=200, content='hello world')
        assert guess_lexer_name(response) == ''

    @pytest.mark.parametrize(('arguments', 'lexer'), [
        ({'content': 'print("hello world")', 'headers': {'Content-Type': 'application/x-python'}}, 'Python'),
        ({'json': {'hello': 'world'}}, 'JSON')
    ])
    def test_should_return_correct_lexer_name_given_content_type(self, arguments, lexer):
        response = httpx.Response(status_code=200, **arguments)

        assert guess_lexer_name(response) == lexer


class TestGetResponseHeadersText:
    """Tests function get_response_headers_text"""

    def test_should_return_correct_output(self):
        data = {'hello': 'world'}
        response = httpx.Response(status_code=200, json=data)
        output = (
            'HTTP/1.1 200 OK\n'
            'content-length: 18\n'
            'content-type: application/json'
        )
        assert get_response_headers_text(response) == output


class TestPrintResponse:
    """Tests function print_response"""

    @pytest.mark.parametrize(('arguments', 'output_lines'), [
        ({'content': 'print("hello world")', 'headers': {'Content-Type': 'application/x-python'}}, [
            'content-length: 20',
            'content-type: application/x-python',
            'print("hello world")'
        ]),
        ({'json': {'hello': 'world'}}, [
            'content-length: 18',
            'content-type: application/json',
            '{',
            'hello',
            'world',
            '}'
        ])
    ])
    def test_should_print_correct_output(self, capsys, arguments, output_lines):
        response = httpx.Response(status_code=200, **arguments)

        lines = [
            'HTTP/1.1 200 OK',
            *output_lines
        ]
        print_response(response)
        output = capsys.readouterr().out

        for line in lines:
            assert line in output

    def test_should_print_correct_output_when_json_is_badly_formed(self, capsys, mocker):
        data = {'hello': 'world'}
        mocker.patch('json.dumps', side_effect=json.JSONDecodeError('hum', str(data), 2))
        response = httpx.Response(status_code=200, json=data)
        print_response(response)

        output = capsys.readouterr().out
        lines = [
            'HTTP/1.1 200 OK',
            'content-length: 18',
            'content-type: application/json',
            '{"hello": "world"}'
        ]

        for line in lines:
            assert line in output


class TestPerformReadRequest:
    """Tests function perform_read_request"""

    @pytest.mark.parametrize('method', ['GET', 'HEAD', 'OPTIONS', 'DELETE'])
    async def test_should_raise_error_when_request_timeout_expired(self, capsys, respx_mock, autojump_clock, method):
        async def side_effect(_):
            await anyio.sleep(6)

        respx_mock.route(method=method, host='example.com').side_effect = side_effect

        with pytest.raises(click.Abort):
            # noinspection PyTypeChecker
            await perform_read_request(method, 'https://example.com', Configuration(), tuple(), tuple(), [])

        assert capsys.readouterr().out == 'the request timeout has expired\n'

    @pytest.mark.parametrize('method', ['GET', 'HEAD', 'OPTIONS', 'DELETE'])
    async def test_should_raise_click_error_when_unexpected_httpx_error_happens(self, capsys, respx_mock, method):
        respx_mock.route(method=method, host='example.com').side_effect = httpx.TransportError('just a test error')

        with pytest.raises(click.Abort):
            # noinspection PyTypeChecker
            await perform_read_request(method, 'https://example.com', Configuration(), tuple(), tuple(), [])

        assert capsys.readouterr().out == 'unexpected error: just a test error\n'

    # this is not a realistic example, but just prove the function works as expected
    @pytest.mark.parametrize('method', ['GET', 'HEAD', 'OPTIONS', 'DELETE'])
    async def test_should_print_response_given_correct_input(self, capsys, respx_mock, method):
        respx_mock.route(method=method, host='example.com') % dict(json={'hello': 'world'})
        # noinspection PyTypeChecker
        await perform_read_request(method, 'https://example.com', Configuration(), tuple(), tuple(), [])

        output = capsys.readouterr().out
        lines = [
            'HTTP/1.1 200 OK',
            'content-length: 18',
            'content-type: application/json',
            '{',
            'hello',
            'world',
            '}'
        ]
        for line in lines:
            assert line in output
