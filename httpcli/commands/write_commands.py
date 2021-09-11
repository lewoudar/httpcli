import asyncclick as click
from pydantic import AnyHttpUrl

from httpcli.configuration import Configuration
from httpcli.options import http_query_options
from httpcli.parameters import URL
from httpcli.types import HttpProperty
from .helpers import perform_read_request


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
