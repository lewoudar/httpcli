import re
from typing import Any

import idna
from pydantic import BaseModel, validator, AnyHttpUrl


class UrlModel(BaseModel):
    url: AnyHttpUrl

    @validator('url', pre=True)
    def check_shortcut_url(cls, value: str) -> Any:
        value = idna.encode(value).decode()
        if re.match(r'^:\d+', value):
            return f'http://localhost{value}'
        return value
