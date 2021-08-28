import click
from click_params import URL

from .configuration import Configuration, Auth
from .parameters import AUTH_PARAM


@click.version_option('0.1.0', message='%(prog)s version %(version)s')
@click.group()
@click.option('--proxy', type=URL, help='proxy url')
@click.option(
    '--http-version',
    type=click.Choice(['h1', 'h2']),
    help='version of http used to make the request',
)
@click.option(
    '--backend', type=click.Choice(['trio', 'asyncio', 'uvloop']),
    help='internal asynchronous backend used',
)
@click.option('--auth', type=AUTH_PARAM, help='a json string representing authentication information')
@click.option(
    '--follow-redirects/--no-follow-redirects', ' /-N',
    help='flag to decide if http redirections must be followed')
@click.pass_context
def http(context: click.Context, proxy: str, http_version: str, backend: str, auth: Auth, follow_redirects: bool):
    """HTTP CLI"""
    config = context.ensure_object(Configuration)
    if http_version is not None:
        config.version = http_version
    if backend is not None:
        config.backend = backend
    if proxy is not None:
        config.proxy = proxy
    if auth is not None:
        config.auth = auth
    if follow_redirects is not None:
        config.follow_redirects = follow_redirects
    click.echo(config)


@click.command()
def dummy():
    click.echo('dummy')


http.add_command(dummy)

if __name__ == '__main__':
    http()
