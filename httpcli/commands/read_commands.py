import anyio
import click
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
def get(obj: Configuration, url: AnyHttpUrl, headers: HttpProperty, query_params: HttpProperty, cookies: HttpProperty):
    """
    Performs http GET request.

    URL is the target url.
    """
    anyio.run(perform_read_request, 'GET', str(url), obj, headers, query_params, cookies, backend=obj.backend)
