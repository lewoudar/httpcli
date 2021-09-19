import anyio
import asyncclick as click
from pydantic import AnyHttpUrl

from httpcli.configuration import Configuration
from httpcli.options import http_query_options, http_write_options
from httpcli.parameters import URL
from httpcli.types import HttpProperty
from .helpers import perform_read_request, perform_write_request, function_runner, signal_handler


@click.command()
@click.argument('url', type=URL)
@http_query_options
@click.pass_obj
async def delete(
        config: Configuration, url: AnyHttpUrl, headers: HttpProperty, query_params: HttpProperty, cookies: HttpProperty
):
    """
    Performs http DELETE request.

    URL is the target url.
    """
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            function_runner, tg.cancel_scope, perform_read_request, 'DELETE', str(url), config, headers, query_params,
            cookies
        )
        tg.start_soon(signal_handler, tg.cancel_scope)


@click.command()
@click.argument('url', type=URL)
@http_query_options
@http_write_options
@click.pass_obj
async def post(
        config: Configuration,
        url: AnyHttpUrl, headers: HttpProperty,
        query_params: HttpProperty,
        cookies: HttpProperty,
        form: HttpProperty,
        json_data: HttpProperty,
        raw: bytes
):
    """
    Performs http POST request.

    URL is the target url.
    """
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            function_runner, tg.cancel_scope, perform_write_request, 'POST', str(url), config, headers, query_params,
            cookies, form, json_data, raw
        )
        tg.start_soon(signal_handler, tg.cancel_scope)


@click.command()
@click.argument('url', type=URL)
@http_query_options
@http_write_options
@click.pass_obj
async def patch(
        config: Configuration,
        url: AnyHttpUrl, headers: HttpProperty,
        query_params: HttpProperty,
        cookies: HttpProperty,
        form: HttpProperty,
        json_data: HttpProperty,
        raw: bytes
):
    """
    Performs http PATCH request.

    URL is the target url.
    """
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            function_runner, tg.cancel_scope, perform_write_request, 'PATCH', str(url), config, headers, query_params,
            cookies, form, json_data, raw
        )
        tg.start_soon(signal_handler, tg.cancel_scope)


@click.command()
@click.argument('url', type=URL)
@http_query_options
@http_write_options
@click.pass_obj
async def put(
        config: Configuration,
        url: AnyHttpUrl, headers: HttpProperty,
        query_params: HttpProperty,
        cookies: HttpProperty,
        form: HttpProperty,
        json_data: HttpProperty,
        raw: bytes
):
    """
    Performs http PUT request.

    URL is the target url.
    """
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            function_runner, tg.cancel_scope, perform_write_request, 'PUT', str(url), config, headers, query_params,
            cookies, form, json_data, raw
        )
        tg.start_soon(signal_handler, tg.cancel_scope)
