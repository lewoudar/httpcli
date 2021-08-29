import re
from typing import Any, List

import idna
from pydantic import BaseModel, validator, AnyHttpUrl
from typing_extensions import Literal


class UrlModel(BaseModel):
    url: AnyHttpUrl

    @validator('url', pre=True)
    def check_shortcut_url(cls, value: str) -> Any:
        value = idna.encode(value).decode()
        if re.match(r'^:\d+', value):
            return f'http://localhost{value}'
        return value


class Auth(BaseModel):
    type: str


class UserMixin(BaseModel):
    username: str
    password: str


class BasicAuth(UserMixin, Auth):
    type: Literal['basic'] = 'basic'


class DigestAuth(UserMixin, Auth):
    type: Literal['digest'] = 'digest'


class OAuth2(Auth):
    type: Literal['oauth2'] = 'oauth2'
    flow: str


class OAuth2PasswordBearer(UserMixin, OAuth2):
    token_url: AnyHttpUrl
    flow: Literal['password'] = 'password'
    scopes: List[str] = []
