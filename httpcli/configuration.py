import json
from typing import Optional, Union, Any

from pydantic import BaseSettings, AnyHttpUrl, validator, FilePath
from typing_extensions import Literal

from .models import BasicAuth, DigestAuth, OAuth2PasswordBearer


class Configuration(BaseSettings):
    proxy: Optional[AnyHttpUrl] = None
    version: Literal['h1', 'h2'] = 'h1'
    backend: Literal['trio', 'asyncio', 'uvloop'] = 'trio'
    auth: Optional[Union[BasicAuth, DigestAuth, OAuth2PasswordBearer]] = None
    follow_redirects: bool = True
    verify: Union[bool, FilePath] = True
    timeout: Optional[float] = 5.0

    @validator('auth', pre=True)
    def convert_str_to_dict(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f'{value} is not a valid json string')
        return value

    class Config:
        env_prefix = 'http_cli_'
