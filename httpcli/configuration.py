import json
from typing import Optional, Union, List, Any
from typing_extensions import Literal
from pydantic import BaseSettings, BaseModel, AnyHttpUrl, validator


class Auth(BaseModel):
    type: str


class UserMixin(BaseModel):
    username: str
    password: str


class BasicAuth(UserMixin, Auth):
    type: Literal['basic']


class DigestAuth(UserMixin, Auth):
    type: Literal['digest']


class OAuth2(Auth):
    type: Literal['oauth2']
    flow: str


class OAuth2PasswordBearer(UserMixin, OAuth2):
    token_url: AnyHttpUrl
    flow: Literal['password']
    scopes: List[str] = []


class Configuration(BaseSettings):
    proxy: Optional[AnyHttpUrl] = None
    version: Literal['h1', 'h2'] = 'h1'
    backend: Literal['trio', 'asyncio', 'uvloop'] = 'trio'
    auth: Optional[Union[BasicAuth, DigestAuth, OAuth2PasswordBearer]] = None
    follow_redirects: bool = True

    @validator('auth', pre=True)
    def convert_str_to_dict(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f'{value} is not a valid json string')
        return value

    class Config:
        env_prefix = 'http_'
