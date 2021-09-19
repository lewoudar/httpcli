import anyio
import asyncclick as click
from pydantic import AnyHttpUrl

from httpcli.configuration import Configuration
from httpcli.options import http_query_options
from httpcli.parameters import URL
from httpcli.types import HttpProperty
from .helpers import perform_read_request, function_runner, signal_handler


@click.command()
@click.argument('url', type=URL)
@http_query_options
@click.pass_obj
async def get(
        config: Configuration, url: AnyHttpUrl, headers: HttpProperty, query_params: HttpProperty, cookies: HttpProperty
):
    """
    Performs http GET request.

    URL is the target url.
    """
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            function_runner, tg.cancel_scope, perform_read_request, 'GET', str(url), config, headers, query_params,
            cookies
        )
        tg.start_soon(signal_handler, tg.cancel_scope)


@click.command()
@click.argument('url', type=URL)
@http_query_options
@click.pass_obj
async def head(
        config: Configuration, url: AnyHttpUrl, headers: HttpProperty, query_params: HttpProperty, cookies: HttpProperty
):
    """
    Performs http HEAD request.

    URL is the target url.
    """
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            function_runner, tg.cancel_scope, perform_read_request, 'HEAD', str(url), config, headers, query_params,
            cookies
        )
        tg.start_soon(signal_handler, tg.cancel_scope)


@click.command()
@click.argument('url', type=URL)
@http_query_options
@click.pass_obj
async def options(
        config: Configuration, url: AnyHttpUrl, headers: HttpProperty, query_params: HttpProperty, cookies: HttpProperty
):
    """
    Performs http OPTIONS request.

    URL is the target url.
    """
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            function_runner, tg.cancel_scope, perform_read_request, 'OPTIONS', str(url), config, headers, query_params,
            cookies
        )
        tg.start_soon(signal_handler, tg.cancel_scope)
