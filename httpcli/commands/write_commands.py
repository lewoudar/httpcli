import asyncclick as click
from pydantic import AnyHttpUrl

from httpcli.configuration import Configuration
from httpcli.options import http_query_options, http_write_options
from httpcli.parameters import URL
from httpcli.types import HttpProperty
from .helpers import perform_read_request, perform_write_request


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
    await perform_read_request('DELETE', str(url), config, headers, query_params, cookies)


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
    await perform_write_request('POST', str(url), config, headers, query_params, cookies, form, json_data, raw)


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
    await perform_write_request('PATCH', str(url), config, headers, query_params, cookies, form, json_data, raw)


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
    await perform_write_request('PUT', str(url), config, headers, query_params, cookies, form, json_data, raw)
