from pathlib import Path
from typing import Optional, Union

import click
from pydantic import AnyHttpUrl

from .configuration import Configuration
from .models import Auth
from .options import global_cli_options


def set_configuration_options(
        config: Configuration,
        proxy: Optional[AnyHttpUrl] = None,
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


@click.version_option('0.1.0', message='%(prog)s version %(version)s')
@click.group()
@global_cli_options
@click.pass_context
def http(
        context: click.Context,
        proxy: AnyHttpUrl,
        http_version: str,
        backend: str, auth: Auth,
        follow_redirects: bool,
        timeout: float
):
    """HTTP CLI"""
    config = context.ensure_object(Configuration)
    set_configuration_options(config, proxy, http_version, backend, auth, follow_redirects, timeout, verify=False)


if __name__ == '__main__':
    http()
