import click
import httpx
import pytest

from httpcli.configuration import Configuration, BasicAuth, DigestAuth
from httpcli.helpers import (build_base_httpx_arguments, load_config_from_yaml, build_http_property_arguments)

CONFIGURATIONS = [
    Configuration(),
    Configuration(verify=False, version='h2'),
    Configuration(proxy='https://proxy.com', follow_redirects=False),
    Configuration(auth=DigestAuth(username='foo', password='bar'), follow_redirects=False)
]

DEFAULT_ARGUMENT = {
    'allow_redirects': True,
    'verify': True,
    'http1': True,
    'http2': False
}

ARGUMENTS = [
    DEFAULT_ARGUMENT,
    {**DEFAULT_ARGUMENT, 'verify': False, 'http1': False, 'http2': True},
    {**DEFAULT_ARGUMENT, 'proxies': 'https://proxy.com', 'allow_redirects': False},
]


class TestBuildBaseHttpxArguments:
    """Tests build_base_httpx_arguments function"""

    @pytest.mark.parametrize(('config', 'arguments'), [
        (CONFIGURATIONS[0], ARGUMENTS[0]),
        (CONFIGURATIONS[1], ARGUMENTS[1]),
        (CONFIGURATIONS[2], ARGUMENTS[2])
    ])
    def test_should_return_correct_arguments(self, config, arguments):
        assert build_base_httpx_arguments(config) == arguments

    @pytest.mark.parametrize(('auth_argument', 'httpx_auth_class'), [
        (DigestAuth(username='foo', password='bar'), httpx.DigestAuth),
        (BasicAuth(username='foo', password='bar'), httpx.BasicAuth)
    ])
    def test_should_return_correct_arguments_with_auth_configuration(self, auth_argument, httpx_auth_class):
        config = Configuration(auth=auth_argument)
        arguments = build_base_httpx_arguments(config)

        assert set(arguments.keys()) == {'allow_redirects', 'verify', 'http1', 'http2', 'auth'}
        assert arguments['allow_redirects'] is True
        assert arguments['verify'] is True
        assert arguments['http1'] is True
        assert arguments['http2'] is False
        auth = arguments['auth']
        assert isinstance(auth, httpx_auth_class)

    def test_should_return_correct_arguments_with_a_custom_certificate(self, tmp_path):
        fake_cert = tmp_path / 'cert.pem'
        fake_cert.write_bytes(b'fake cert')
        config = Configuration(verify=fake_cert)
        arguments = build_base_httpx_arguments(config)

        assert set(arguments.keys()) == {'allow_redirects', 'verify', 'http1', 'http2'}
        assert arguments['http1'] is True
        assert arguments['http2'] is False
        assert arguments['allow_redirects'] is True
        assert arguments['verify'] == str(fake_cert)


HTTP_ARGUMENT = (('foo', 'bar'),)


class TestBuildHttpPropertyArguments:
    """Tests function build_http_property_arguments"""

    @pytest.mark.parametrize(('input_arguments', 'output_arguments'), [
        ({'headers': HTTP_ARGUMENT}, {'headers': HTTP_ARGUMENT}),
        ({'cookies': HTTP_ARGUMENT}, {'cookies': HTTP_ARGUMENT}),
        ({'query_params': HTTP_ARGUMENT}, {'params': HTTP_ARGUMENT}),
        ({'headers': HTTP_ARGUMENT, 'cookies': HTTP_ARGUMENT, 'query_params': HTTP_ARGUMENT},
         {'headers': HTTP_ARGUMENT, 'cookies': HTTP_ARGUMENT, 'params': HTTP_ARGUMENT})
    ])
    def test_should_return_correct_arguments_given_correct_input(self, input_arguments, output_arguments):
        assert build_http_property_arguments(**input_arguments) == output_arguments


BAD_YAML_DATA = """
httpcli:
  timeout: 2
  backend: foo
"""

CORRECT_YAML_DATA = """
httpcli:
  timeout: 2
  backend: asyncio
"""


class TestLoadConfigFromYaml:
    """Tests function load_config_from_yaml"""

    def test_should_raise_error_given_file_with_wrong_configuration(self, tmp_path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text(BAD_YAML_DATA)
        with pytest.raises(click.UsageError) as exc_info:
            with config_file.open() as f:
                load_config_from_yaml(f)

        assert 'backend' in str(exc_info.value)

    def test_should_return_correct_configuration_given_correct_configuration_file(self, tmp_path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text(CORRECT_YAML_DATA)
        with config_file.open() as f:
            config = load_config_from_yaml(f)
            assert config.timeout == 2
            assert config.backend == 'asyncio'
