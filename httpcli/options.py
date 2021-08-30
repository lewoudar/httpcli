from typing import Callable, TypeVar, Any

import click

from .parameters import AUTH_PARAM, URL, HEADER, COOKIE, QUERY

# copying this from click code
FC = TypeVar("FC", Callable[..., Any], click.Command)


def proxy_option(f: FC) -> FC:
    return click.option('--proxy', type=URL, help='proxy url')(f)


def http_version_option(f: FC) -> FC:
    return click.option(
        '--http-version',
        type=click.Choice(['h1', 'h2']),
        help='version of http used to make the request',
    )(f)


def backend_option(f: FC) -> FC:
    return click.option(
        '--backend', type=click.Choice(['trio', 'asyncio', 'uvloop']),
        help='internal asynchronous backend used',
    )(f)


def auth_option(f: FC) -> FC:
    return click.option('--auth', type=AUTH_PARAM, help='a json string representing authentication information')(f)


def follow_redirects_option(f: FC) -> FC:
    return click.option(
        '--follow-redirects/--no-follow-redirects', ' /-N',
        help='flag to decide if http redirections must be followed',
        default=None
    )(f)


def global_cli_options(f: FC) -> FC:
    for callable_option in [proxy_option, http_version_option, backend_option, auth_option, follow_redirects_option]:
        f = callable_option(f)
    return f


def query_option(f: FC) -> FC:
    return click.option(
        '-q', '--query', 'query_params',
        type=QUERY,
        multiple=True,
        help='querystring argument passed to the request, can by passed multiple times'
    )(f)


def header_option(f: FC) -> FC:
    return click.option(
        '-H', '--header', 'headers',
        type=HEADER,
        multiple=True,
        help='header passed to the request, can by passed multiple times'
    )(f)


def cookie_option(f: FC) -> FC:
    return click.option(
        '-c', '--cookie', 'cookies',
        type=COOKIE,
        multiple=True,
        help='cookie passed to the request, can by passed multiple times'
    )(f)


def http_query_options(f: FC) -> FC:
    for option in [query_option, header_option, cookie_option]:
        f = option(f)
    return f
