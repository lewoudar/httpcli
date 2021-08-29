import json

import pytest
import pydantic

from httpcli.configuration import Configuration, BasicAuth, DigestAuth, OAuth2PasswordBearer


def test_default_configuration():
    config = Configuration()
    assert config.proxy is None
    assert config.version == 'h1'
    assert config.backend == 'trio'
    assert config.auth is None
    assert config.follow_redirects is True
    assert config.verify is True


@pytest.mark.parametrize('proxy_url', ['http://proxy.com', 'https://proxy.com'])
def test_proxy_configuration(proxy_url):
    config = Configuration(proxy=proxy_url)
    assert config.proxy == proxy_url


@pytest.mark.parametrize(('auth_config', 'auth_type'), [
    ({'type': 'basic', 'username': 'foo', 'password': 'bar'}, BasicAuth),
    ({'type': 'digest', 'username': 'foo', 'password': 'bar'}, DigestAuth),
    ({'type': 'oauth2', 'token_url': 'https://token.com', 'flow': 'password', 'username': 'foo', 'password': 'bar'},
     OAuth2PasswordBearer),
])
def test_auth_configurations(auth_config, auth_type):
    config = Configuration(auth=auth_config)
    assert isinstance(config.auth, auth_type)
    assert config.auth.type in ['basic', 'digest', 'oauth2']
    assert config.auth.username == 'foo'
    assert config.auth.password == 'bar'


def test_environment_config(monkeypatch):
    monkeypatch.setenv('http_cli_version', 'h2')
    monkeypatch.setenv('http_cli_proxy', 'http://proxy.com')
    monkeypatch.setenv('HTTP_CLI_FOLLOW_REDIRECTS', 'false')
    monkeypatch.setenv('HTTP_CLI_AUTH', json.dumps({'type': 'basic', 'username': 'foo', 'password': 'bar'}))

    config = Configuration()
    assert config.version == 'h2'
    assert config.proxy.host == 'proxy.com'
    assert config.follow_redirects is False
    assert isinstance(config.auth, BasicAuth)


def test_config_raises_error_when_auth_is_not_valid_json(monkeypatch):
    monkeypatch.setenv('http_cli_auth', str({'type': 'basic', 'username': 'foo', 'password': 'bar'}))
    with pytest.raises(pydantic.ValidationError) as exc_info:
        Configuration()

    assert 'is not a valid json string' in str(exc_info.value)
