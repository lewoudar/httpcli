from pathlib import Path
from typing import Dict, Any, TextIO, Optional, Union

import click
import httpx
import pydantic
import yaml

from httpcli.configuration import Configuration
from httpcli.models import BasicAuth, DigestAuth, Auth


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
        # todo: implement oauth2 password logic

    if config.proxy is not None:
        arguments['proxies'] = str(config.proxy)

    return arguments


def set_configuration_options(
        config: Configuration,
        proxy: Optional[pydantic.AnyHttpUrl] = None,
        http_version: Optional[str] = None,
        backend: Optional[str] = None,
        auth: Optional[Auth] = None,
        follow_redirects: Optional[bool] = None,
        timeout: Optional[float] = None,
        verify: Optional[Union[bool, Path]] = True
) -> None:
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

    if timeout is not None:
        config.timeout = None if timeout < 0 else timeout
    config.verify = verify


def load_config_from_yaml(file: TextIO) -> Configuration:
    data = yaml.load(file, Loader=yaml.SafeLoader)
    try:
        return Configuration.parse_obj(data['httpcli'])
    except pydantic.ValidationError as e:
        raise click.UsageError(str(e))
