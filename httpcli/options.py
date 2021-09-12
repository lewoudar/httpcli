from typing import Callable, TypeVar, Any

import asyncclick as click

from .parameters import AUTH_PARAM, URL, HEADER, COOKIE, QUERY, FORM, JSON, RAW_PAYLOAD

# copying this from click code
FC = TypeVar("FC", Callable[..., Any], click.Command)


def proxy_option(f: FC) -> FC:
    return click.option('--proxy', type=URL, help='Proxy url.')(f)


def http_version_option(f: FC) -> FC:
    return click.option(
        '--http-version',
        type=click.Choice(['h1', 'h2']),
        help='Version of http used to make the request.',
    )(f)


def auth_option(f: FC) -> FC:
    return click.option('--auth', type=AUTH_PARAM, help='A json string representing authentication information.')(f)


def follow_redirects_option(f: FC) -> FC:
    return click.option(
        '--follow-redirects/--no-follow-redirects', ' /-N',
        help='flag to decide if http redirections must be followed',
        default=None
    )(f)


def timeout_option(f: FC) -> FC:
    return click.option(
        '-t', '--timeout',
        type=float,
        help='Time for request to complete, a negative value means there is no timeout.'
    )(f)


def config_file_option(f: FC) -> FC:
    return click.option(
        '--config-file',
        type=click.File(),
        help='A configuration file with options used to set the cli. '
             'Note that the file takes precedence over the other options.'
    )(f)


def global_cli_options(f: FC) -> FC:
    options = [
        proxy_option, http_version_option, auth_option, follow_redirects_option, timeout_option, config_file_option
    ]
    for callable_option in options:
        f = callable_option(f)
    return f


def query_option(f: FC) -> FC:
    return click.option(
        '-q', '--query', 'query_params',
        type=QUERY,
        multiple=True,
        help='Querystring argument passed to the request, can by passed multiple times.'
    )(f)


def header_option(f: FC) -> FC:
    return click.option(
        '-H', '--header', 'headers',
        type=HEADER,
        multiple=True,
        help='Header passed to the request, can by passed multiple times.'
    )(f)


def cookie_option(f: FC) -> FC:
    return click.option(
        '-c', '--cookie', 'cookies',
        type=COOKIE,
        multiple=True,
        help='Cookie passed to the request, can by passed multiple times.'
    )(f)


def http_query_options(f: FC) -> FC:
    for option in [query_option, header_option, cookie_option]:
        f = option(f)
    return f


def form_option(f: FC) -> FC:
    return click.option(
        '-f', '--form',
        type=FORM,
        multiple=True,
        help='Form data passed to the request, can be passed multiple times.'
    )(f)


def json_option(f: FC) -> FC:
    return click.option(
        '-j', '--json', 'json_data',
        type=JSON,
        multiple=True,
        help='Json data passed to the request, can be passed multiple times.'
    )(f)


def raw_payload_option(f: FC) -> FC:
    return click.option(
        '-r', '--raw',
        type=RAW_PAYLOAD,
        help='Raw data passed to the request. It cannot be used with --json and --form options.'
    )(f)


def http_write_options(f: FC) -> FC:
    for option in [form_option, json_option, raw_payload_option]:
        f = option(f)

    return f
