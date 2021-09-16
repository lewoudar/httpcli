import json
import re

import asyncclick as click
import httpx
from rich.markup import escape
from rich.syntax import Syntax

from httpcli.commands.helpers import print_response_headers
from httpcli.configuration import Configuration
from httpcli.console import console
from httpcli.helpers import build_base_httpx_arguments
from httpcli.parameters import URL


@click.command()
@click.argument('url', type=URL)
@click.pass_obj
# well, technically url is not a str but a pydantic.AnyHttpUrl object inheriting from str
# but it does not seem to bother httpx, so we can use the convenient str for signature
async def sse(config: Configuration, url: str):
    """
    Reads and print SSE events on a given url.

    URL is the url where SSE events will be read.
    """
    event_regex = re.compile(r'event:\s*(.+)')
    data_regex = re.compile(r'data:\s*(.+)')
    arguments = build_base_httpx_arguments(config)
    allow_redirects = arguments.pop('allow_redirects')
    try:
        async with httpx.AsyncClient(**arguments) as client:
            async with client.stream('GET', url, allow_redirects=allow_redirects) as response:
                if 300 < response.status_code < 400:
                    console.print('[warning]the request was interrupted because redirection was not followed')
                    raise click.Abort()

                elif response.status_code >= 400:
                    await response.aread()
                    console.print(f'[error]unexpected error: {response.text}')
                    raise click.Abort()

                else:
                    print_response_headers(response)
                    console.print()
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        match = event_regex.match(line)
                        if match:
                            console.print(f'[blue]event:[/] [green]{escape(match.group(1))}[/]')
                        else:
                            match = data_regex.match(line)
                            if match:
                                try:
                                    line = match.group(1)
                                    data = json.loads(line)
                                    console.print(Syntax(json.dumps(data, indent=4), 'json'))
                                except json.JSONDecodeError:
                                    # we print the line as it if it is not a json string
                                    console.print(line)
                            else:
                                console.print(line)
                        console.print()
    except httpx.HTTPError as e:
        console.print(f'[error]unexpected error: {e}')
        raise click.Abort()
