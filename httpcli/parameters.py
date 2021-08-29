import json
import typing as t

import click
from pydantic import ValidationError, AnyHttpUrl

from .configuration import Configuration, Auth
from .models import UrlModel


class AuthParameter(click.ParamType):
    name = 'json_auth'

    def convert(self, value: t.Any, param: t.Optional[click.Parameter], ctx: t.Optional[click.Context]) -> Auth:
        try:
            auth_info = json.loads(value)
        except json.JSONDecodeError:
            self.fail(f'{value} is not a valid json string')

        try:
            config = Configuration(auth=auth_info)
            return config.auth
        except ValidationError:
            self.fail('authentication information is not valid')


class UrlParameter(click.ParamType):
    name = 'url'

    def convert(self, value: t.Any, param: t.Optional[click.Parameter], ctx: t.Optional[click.Context]) -> AnyHttpUrl:
        try:
            url_model = UrlModel(url=value)
            return url_model.url
        except ValidationError:
            self.fail(f'{value} is not a valid url')


AUTH_PARAM = AuthParameter()
URL = UrlParameter()
