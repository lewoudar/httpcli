import json

import anyio
import asyncclick as click
import httpx
from pygments.lexers import get_lexer_for_mimetype
from pygments.util import ClassNotFound
from rich.syntax import Syntax
from typing_extensions import Literal

from httpcli.configuration import Configuration
from httpcli.console import console
from httpcli.helpers import build_read_method_arguments
from httpcli.types import HttpProperty


def guess_lexer_name(response: httpx.Response) -> str:
    content_type = response.headers.get('Content-Type')
    if content_type is not None:
        mime_type, _, _ = content_type.partition(';')
        try:
            return get_lexer_for_mimetype(mime_type.strip()).name
        except ClassNotFound:
            pass
    return ''


def get_response_headers_text(response: httpx.Response) -> str:
    lines = [f'{response.http_version} {response.status_code} {response.reason_phrase}']
    for name, value in response.headers.items():
        lines.append(f'{name}: {value}')
    return '\n'.join(lines)


def print_delimiter() -> None:
    syntax = Syntax('', 'http')
    console.print(syntax)


def print_response(response: httpx.Response) -> None:
    http_headers = get_response_headers_text(response)
    syntax = Syntax(http_headers, 'http')
    console.print(syntax)
    print_delimiter()
    lexer = guess_lexer_name(response)
    if lexer:
        text = response.text
        if lexer.lower() == 'json':
            try:
                data = response.json()
                text = json.dumps(data, indent=4)
            except json.JSONDecodeError:
                pass
        syntax = Syntax(text, lexer)
        console.print(syntax)
    else:
        console.print(response.text)


# delete is not a read method but it takes the same http parameters as the read methods.
async def perform_read_request(
        method: Literal['GET', 'HEAD', 'OPTIONS', 'DELETE'],
        url: str,
        config: Configuration,
        headers: HttpProperty,
        query_params: HttpProperty,
        cookies: HttpProperty
):
    arguments = await build_read_method_arguments(config, headers, cookies, query_params)
    allow_redirects = arguments.pop('allow_redirects')

    with anyio.move_on_after(config.timeout) as scope:
        try:
            async with httpx.AsyncClient(**arguments, timeout=None) as client:
                response = await client.request(method, url, allow_redirects=allow_redirects)
                print_response(response)
        except httpx.HTTPError as e:
            console.print(f'[red]unexpected error: {e}')
            raise click.Abort()

    if scope.cancel_called:
        console.print('[red]the request timeout has expired')
        raise click.Abort()
