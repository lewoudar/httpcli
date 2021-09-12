from typing import TextIO

import asyncclick as click
from pydantic import AnyHttpUrl

from .commands.read_commands import get, head, options
from .commands.write_commands import delete, post, put, patch
from .configuration import Configuration
from .helpers import load_config_from_yaml, set_configuration_options
from .models import Auth
from .options import global_cli_options
from .version import __version__


@click.version_option(__version__, message='%(prog)s version %(version)s')
@click.group()
@global_cli_options
@click.option(
    '--cert',
    help='path to certificate used to authenticate hosts',
    type=click.Path(exists=True, dir_okay=False)
)
@click.pass_context
def https(
        context: click.Context,
        proxy: AnyHttpUrl,
        http_version: str,
        auth: Auth,
        follow_redirects: bool,
        timeout: float,
        config_file: TextIO,
        cert: str,
):
    """HTTP CLI with certificate validation."""
    if config_file:
        config = load_config_from_yaml(config_file)
        if cert:
            config.verify = cert
        context.obj = config
        return

    config = context.ensure_object(Configuration)
    set_configuration_options(config, proxy, http_version, auth, follow_redirects, timeout, verify=cert or True)


# add subcommands
for command in [get, post, put, patch, delete, head, options]:
    https.add_command(command)  # type: ignore
