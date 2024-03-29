from pathlib import Path
from typing import Dict, Any, TextIO, Optional, Union

import anyio
import asyncclick as click
import httpx
import pydantic
import yaml

from httpcli.configuration import Configuration
from httpcli.console import console
from httpcli.models import BasicAuth, DigestAuth, Auth, OAuth2PasswordBearer
from httpcli.types import HttpProperty


def build_base_httpx_arguments(config: Configuration) -> Dict[str, Any]:
    arguments: Dict[str, Any] = {
        'allow_redirects': config.follow_redirects,
        'verify': str(config.verify) if isinstance(config.verify, Path) else config.verify,
        'http1': config.version == 'h1',
        'http2': config.version == 'h2'
    }
    if config.auth is not None:
        auth = config.auth
        if isinstance(auth, BasicAuth):
            arguments['auth'] = httpx.BasicAuth(auth.username, auth.password)
        elif isinstance(auth, DigestAuth):
            arguments['auth'] = httpx.DigestAuth(auth.username, auth.password)

    if config.proxy is not None:
        arguments['proxies'] = str(config.proxy)

    return arguments


def build_http_property_arguments(
        headers: Optional[HttpProperty] = None,
        cookies: Optional[HttpProperty] = None,
        query_params: Optional[HttpProperty] = None
) -> Dict[str, HttpProperty]:
    arguments = {}
    if headers is not None:
        arguments['headers'] = headers

    if cookies is not None:
        # we get tuple of tuples from click but httpx only handles list of tuples
        arguments['cookies'] = list(cookies)

    if query_params is not None:
        arguments['params'] = query_params

    return arguments


async def get_oauth2_bearer_token(auth: OAuth2PasswordBearer) -> str:
    # just decide to use of timeout of 5s because it seems reasonable..
    # this should probably be configurable but I will not do it in this POC
    with anyio.move_on_after(5) as scope:
        async with httpx.AsyncClient(base_url=auth.token_url, timeout=None) as client:
            response = await client.post('/', data={'username': auth.username, 'password': auth.password})
            if response.status_code >= 400:
                console.print(f'[error]unable to fetch token, reason: {response.text}')
                raise click.Abort()
            else:
                return response.json()['access_token']

    if scope.cancel_called:
        console.print('[error]the request timeout has expired')
        raise click.Abort()


async def build_read_method_arguments(
        config: Configuration,
        headers: Optional[HttpProperty] = None,
        cookies: Optional[HttpProperty] = None,
        query_params: Optional[HttpProperty] = None
) -> Dict[str, Any]:
    base_arguments = build_base_httpx_arguments(config)
    http_arguments = build_http_property_arguments(headers, cookies, query_params)

    if isinstance(config.auth, OAuth2PasswordBearer):
        token = await get_oauth2_bearer_token(config.auth)
        headers = list(http_arguments.get('headers', []))
        headers.append(('Authorization', f'Bearer {token}'))
        http_arguments['headers'] = headers  # type: ignore

    return {**base_arguments, **http_arguments}


async def build_write_method_arguments(
        config: Configuration,
        headers: Optional[HttpProperty] = None,
        cookies: Optional[HttpProperty] = None,
        query_params: Optional[HttpProperty] = None,
        form: Optional[HttpProperty] = None,
        json_data: Optional[HttpProperty] = None,
        raw: Optional[bytes] = None
) -> Dict[str, Any]:
    arguments = await build_read_method_arguments(config, headers, cookies, query_params)
    presence_info = [(data is not None and data != ()) for data in [form, json_data, raw]]
    if presence_info.count(True) > 1:
        raise click.UsageError(
            'you cannot mix different types of data, you must choose between one between form, json or raw'
        )

    if form:
        data = {}
        files = {}
        for key, value in form:
            if value.startswith('@'):
                files[key] = open(value[1:], 'rb')
            else:
                data[key] = value
        arguments['data'] = data
        arguments['files'] = files

    if json_data:
        arguments['json'] = dict(json_data)
    if raw:
        arguments['content'] = raw

    return arguments


def set_configuration_options(
        config: Configuration,
        proxy: Optional[pydantic.AnyHttpUrl] = None,
        http_version: Optional[str] = None,
        auth: Optional[Auth] = None,
        follow_redirects: Optional[bool] = None,
        timeout: Optional[float] = None,
        verify: Optional[Union[bool, str]] = True
) -> None:
    if http_version is not None:
        config.version = http_version

    if proxy is not None:
        config.proxy = proxy

    if auth is not None:
        config.auth = auth

    if follow_redirects is not None:
        config.follow_redirects = follow_redirects

    if timeout is not None:
        config.timeout = None if timeout < 0 else timeout
    config.verify = verify


def load_config_from_yaml(file: TextIO) -> Configuration:
    data = yaml.load(file, Loader=yaml.SafeLoader)
    try:
        return Configuration.parse_obj(data['httpcli'])
    except pydantic.ValidationError as e:
        raise click.UsageError(str(e))
