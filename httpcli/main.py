from typing import TextIO

import click
from pydantic import AnyHttpUrl

from .commands.read_commands import get
from .configuration import Configuration
from .helpers import load_config_from_yaml, set_configuration_options
from .models import Auth
from .options import global_cli_options


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
        timeout: float,
        config_file: TextIO
):
    """HTTP CLI"""
    if config_file:
        context.obj = load_config_from_yaml(config_file)
        return
    config = context.ensure_object(Configuration)
    set_configuration_options(config, proxy, http_version, backend, auth, follow_redirects, timeout, verify=False)


# add subcommands
http.add_command(get)  # type: ignore

if __name__ == '__main__':
    http()
