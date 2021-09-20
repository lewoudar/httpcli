import json
import signal
import subprocess
import sys
from typing import AsyncIterator

import httpx
import pytest
import trio
from hypercorn.config import Config
from hypercorn.trio import serve

from httpcli.http import http
from httpcli.https import https
from tests.helpers import app

command_parametrize = pytest.mark.parametrize('command', [http, https])


@command_parametrize
async def test_should_print_error_when_redirection_is_not_allowed(runner, respx_mock, command):
    url = 'https://foo.com/sse'
    respx_mock.get(url) % 307
    result = await runner.invoke(command, ['sse', url])

    assert result.exit_code == 1
    lines = [
        'the request was interrupted because redirection was not followed',
        'Aborted!'
    ]
    assert result.output == '\n'.join(lines) + '\n'


@command_parametrize
async def test_should_print_error_when_request_failed(runner, respx_mock, command):
    url = 'https://foo.com/sse'
    message = 'request failed'
    respx_mock.get(url) % {'status_code': 400, 'text': message}
    result = await runner.invoke(command, ['sse', url])

    assert result.exit_code == 1
    lines = [
        f'unexpected error: {message}',
        'Aborted!'
    ]
    assert result.output == '\n'.join(lines) + '\n'


@command_parametrize
async def test_should_print_error_when_unexpected_error_happened(runner, respx_mock, command):
    url = 'https://foo.com/sse'
    message = 'just a test error'
    respx_mock.get(url).mock(side_effect=httpx.TransportError(message))
    result = await runner.invoke(command, ['sse', url])

    assert result.exit_code == 1
    lines = [
        f'unexpected error: {message}',
        'Aborted!'
    ]
    assert result.output == '\n'.join(lines) + '\n'


@command_parametrize
async def test_should_print_correct_output_for_json_data(runner, respx_mock, command):
    class NumberStream(httpx.AsyncByteStream):

        async def __aiter__(self) -> AsyncIterator[bytes]:
            for number in range(1, 6):
                yield b'event: number\n'
                yield f'data: {json.dumps({"number": number})}\n'.encode()
                yield b'\n\n'

    url = 'https://foo.com/sse'
    headers = {'content-type': 'text/event-stream'}
    respx_mock.get(url) % httpx.Response(200, headers=headers, stream=NumberStream())
    result = await runner.invoke(command, ['sse', url])

    assert result.exit_code == 0
    output = result.output
    assert 'HTTP/1.1 200 OK' in output
    assert 'content-type: text/event-stream' in output
    assert 'event: number' in output
    assert '{' in output
    assert '"number"' in output
    assert '}' in output
    for i in range(1, 6):
        assert str(i) in output


@command_parametrize
@pytest.mark.parametrize(('data', 'expected_output'), [
    (b'data: hello world\n', 'hello world'),
    (b'hello world\n', 'hello world')
])
async def test_should_print_correct_output_for_non_json_data(runner, respx_mock, command, data, expected_output):
    class HelloStream(httpx.AsyncByteStream):

        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield b'event: hello\n'
            yield data
            yield b'\n\n'

    url = 'https://foo.com/sse'
    headers = {'content-type': 'text/event-stream'}
    respx_mock.get(url) % httpx.Response(200, headers=headers, stream=HelloStream())
    result = await runner.invoke(command, ['sse', url])

    assert result.exit_code == 0
    output = result.output
    assert 'HTTP/1.1 200 OK' in output
    assert 'content-type: text/event-stream' in output
    assert 'event: hello' in output
    assert expected_output in output


async def terminate_process(proc: trio.Process, signal_number: int):
    await trio.sleep(1)
    proc.send_signal(signal_number)


async def test_should_handle_user_interruption_by_ctrl_c(nursery):
    config = Config()
    output = ''

    await nursery.start(serve, app, config)

    async with await trio.open_process(['http', 'sse', ':8000/sse'], stdout=subprocess.PIPE) as process:
        nursery.start_soon(terminate_process, process, signal.SIGINT)
        async for data in process.stdout:
            output += data.decode()

    assert 'Program was interrupted by Ctrl+C, good bye! 👋' in output


@pytest.mark.skipif(sys.platform == 'win32', reason='there is no signal SIGTERM on windows')
async def test_should_handle_user_interruption_by_sigterm(nursery):
    config = Config()
    output = ''

    await nursery.start(serve, app, config)

    async with await trio.open_process(['http', 'sse', ':8000/sse'], stdout=subprocess.PIPE) as process:
        nursery.start_soon(terminate_process, process, signal.SIGTERM)
        async for data in process.stdout:
            output += data.decode()

    assert 'Program was interrupted by the SIGTERM signal, good bye! 👋' in output
