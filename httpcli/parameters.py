import json
import typing as t

import click
from pydantic import ValidationError

from .configuration import Configuration, Auth


class AuthParameter(click.ParamType):
    name = 'json_auth'

    def convert(self, value: t.Any, param: t.Optional[click.Parameter], ctx: t.Optional[click.Context]) -> Auth:
        try:
            auth_info = json.loads(value)
        except json.JSONDecodeError:
            raise click.BadParameter(f'{value} is not a valid json string')

        try:
            config = Configuration(auth=auth_info)
            return config.auth
        except ValidationError:
            raise click.BadParameter(f'authentication information is not valid')


AUTH_PARAM = AuthParameter()
