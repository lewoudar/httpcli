from pathlib import Path
from typing import Dict, Any

import httpx

from httpcli.configuration import Configuration
from httpcli.models import BasicAuth, DigestAuth


def build_base_httpx_arguments(config: Configuration) -> Dict[str, Any]:
    arguments: Dict[str, Any] = {
        'allow_redirects': config.follow_redirects,
        'verify': str(config.verify) if isinstance(config.verify, Path) else config.verify,
        'http1': config.version == 'h1',
        'http2': config.version == 'h2'
    }
    if config.auth is not None:
        auth = config.auth
        if isinstance(auth, BasicAuth):
            arguments['auth'] = httpx.BasicAuth(auth.username, auth.password)
        elif isinstance(auth, DigestAuth):
            arguments['auth'] = httpx.DigestAuth(auth.username, auth.password)
        # todo: implement oauth2 password logic

    if config.proxy is not None:
        arguments['proxies'] = str(config.proxy)

    return arguments
