import json
import typing as t
from pathlib import Path

import asyncclick as click
from pydantic import ValidationError, AnyHttpUrl

from .configuration import Configuration
from .models import Auth
from .models import UrlModel


class AuthParam(click.ParamType):
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


class UrlParam(click.ParamType):
    name = 'url'

    def convert(self, value: t.Any, param: t.Optional[click.Parameter], ctx: t.Optional[click.Context]) -> AnyHttpUrl:
        try:
            url_model = UrlModel(url=value)
            return url_model.url
        except ValidationError:
            self.fail(f'{value} is not a valid url')


class HTTPParameter(click.ParamType):

    def convert(
            self, value: str, param: t.Optional[click.Parameter], ctx: t.Optional[click.Context]
    ) -> t.Tuple[str, str]:
        parts = value.split(':')
        if len(parts) != 2:
            self.fail(f'{value} is not in the form key:value')
        return parts[0], parts[1]


class QueryParam(HTTPParameter):
    name = 'query'


class CookieParam(HTTPParameter):
    name = 'cookie'


class HeaderParam(HTTPParameter):
    name = 'header'


class FormParam(HTTPParameter):
    name = 'form'

    def convert(
            self, value: str, param: t.Optional[click.Parameter], ctx: t.Optional[click.Context]
    ) -> t.Tuple[str, str]:
        field_name, field_value = super().convert(value, param, ctx)

        if field_value.startswith('@'):
            path = Path(field_value[1:])
            if not path.is_file():
                self.fail(f'{field_value[1:]} file does not exist')

        return field_name, field_value


class JsonParam(HTTPParameter):
    name = 'json'

    def convert(
            self, value: str, param: t.Optional[click.Parameter], ctx: t.Optional[click.Context]
    ) -> t.Tuple[str, str]:
        field_name, field_value = super().convert(value, param, ctx)

        if field_value.startswith('@'):
            path = Path(field_value[1:])
            if not path.is_file():
                self.fail(f'{field_value[1:]} file does not exist')
            with path.open() as f:
                try:
                    field_value = json.load(f)
                except json.JSONDecodeError:
                    self.fail(f'{field_value[1:]} is not a valid json file')
        elif field_value.startswith('='):
            try:
                field_value = json.loads(field_value[1:])
            except json.JSONDecodeError:
                self.fail(f'{field_value} is not a valid json value')

        return field_name, field_value


class RawPayloadParam(click.ParamType):
    name = 'RAW_PAYLOAD'

    def convert(
            self, value: str, param: t.Optional[click.Parameter], ctx: t.Optional[click.Context]
    ) -> bytes:
        if value.startswith('@'):
            path = Path(value[1:])
            if not path.is_file():
                self.fail(f'{value[1:]} file does not exist')

            return path.read_bytes()
        return value.encode()


AUTH_PARAM = AuthParam()
URL = UrlParam()
QUERY = QueryParam()
COOKIE = CookieParam()
HEADER = HeaderParam()
FORM = FormParam()
JSON = JsonParam()
RAW_PAYLOAD = RawPayloadParam()
