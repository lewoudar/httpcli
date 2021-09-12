import secrets

import anyio
import asyncclick as click
import httpx
import mock
import pytest

from httpcli.configuration import Configuration, BasicAuth, DigestAuth, OAuth2PasswordBearer
from httpcli.helpers import (
    build_base_httpx_arguments, load_config_from_yaml, build_http_property_arguments, get_oauth2_bearer_token,
    build_read_method_arguments, build_write_method_arguments
)

CONFIGURATIONS = [
    Configuration(),
    Configuration(verify=False, version='h2'),
    Configuration(proxy='https://proxy.com', follow_redirects=False),  # type: ignore
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
        ({'cookies': HTTP_ARGUMENT}, {'cookies': list(HTTP_ARGUMENT)}),
        ({'query_params': HTTP_ARGUMENT}, {'params': HTTP_ARGUMENT}),
        ({'headers': HTTP_ARGUMENT, 'cookies': HTTP_ARGUMENT, 'query_params': HTTP_ARGUMENT},
         {'headers': HTTP_ARGUMENT, 'cookies': list(HTTP_ARGUMENT), 'params': HTTP_ARGUMENT})
    ])
    def test_should_return_correct_arguments_given_correct_input(self, input_arguments, output_arguments):
        assert build_http_property_arguments(**input_arguments) == output_arguments


BAD_YAML_DATA = """
httpcli:
  timeout: 2
  version: h4
"""

CORRECT_YAML_DATA = """
httpcli:
  timeout: 2
  version: h2
"""


class TestLoadConfigFromYaml:
    """Tests function load_config_from_yaml"""

    def test_should_raise_error_given_file_with_wrong_configuration(self, tmp_path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text(BAD_YAML_DATA)
        with pytest.raises(click.UsageError) as exc_info:
            with config_file.open() as f:
                load_config_from_yaml(f)

        assert 'version' in str(exc_info.value)

    def test_should_return_correct_configuration_given_correct_configuration_file(self, tmp_path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text(CORRECT_YAML_DATA)
        with config_file.open() as f:
            config = load_config_from_yaml(f)
            assert config.timeout == 2
            assert config.version == 'h2'


class TestGetOauth2BearerToken:
    """Tests function get_oauth2_bearer_token"""

    async def test_should_raise_error_when_receiving_errored_status_code(self, respx_mock, capsys):
        auth = OAuth2PasswordBearer(token_url='https://token.com', username='foo', password='bar')  # type: ignore
        json_response = {'detail': 'not allowed'}
        httpx_response = httpx.Response(400, json=json_response)
        respx_mock.post('https://token.com', data=auth.dict(include={'username', 'password'})) % httpx_response

        with pytest.raises(click.Abort):
            await get_oauth2_bearer_token(auth)

        output = capsys.readouterr().out
        # click changed quotes used when printing the json output, so I can't test the whole string directly
        assert f'unable to fetch token, reason:' in output
        assert 'detail' in output
        assert 'not allowed' in output

    async def test_should_raise_error_when_request_timeout_expired(self, capsys, respx_mock, autojump_clock):
        async def side_effect(_):
            await anyio.sleep(6)

        auth = OAuth2PasswordBearer(token_url='https://token.com', username='foo', password='bar')  # type: ignore
        route = respx_mock.post('https://token.com', data=auth.dict(include={'username', 'password'}))
        route.side_effect = side_effect

        with pytest.raises(click.Abort):
            await get_oauth2_bearer_token(auth)

        assert capsys.readouterr().out == 'the request timeout has expired\n'

    async def test_should_return_access_token(self, respx_mock):
        auth = OAuth2PasswordBearer(token_url='https://token.com', username='foo', password='bar')  # type: ignore
        access_token = secrets.token_hex(16)
        route = respx_mock.post('https://token.com', data=auth.dict(include={'username', 'password'}))
        route.return_value = httpx.Response(
            status_code=200, json={'token_type': 'bearer', 'access_token': access_token}
        )

        token = await get_oauth2_bearer_token(auth)
        assert access_token == token


class TestBuildReadMethodArguments:
    """Tests function build_read_method_arguments"""

    @pytest.mark.parametrize(('auth_argument', 'http_auth_class'), [
        (BasicAuth(username='foo', password='bar'), httpx.BasicAuth),
        (DigestAuth(username='foo', password='bar'), httpx.DigestAuth)
    ])
    async def test_should_return_httpx_config_given_basic_digest_auth(self, auth_argument, http_auth_class):
        proxy = 'http://proxy.com'
        config = Configuration(auth=auth_argument, proxy=proxy)  # type: ignore
        cookies = [('hello', 'world')]
        query_params = (('search', 'bar'),)

        arguments = await build_read_method_arguments(config, cookies=cookies, query_params=query_params)

        assert arguments['proxies'] == proxy
        assert isinstance(arguments['auth'], http_auth_class)
        assert arguments['cookies'] == cookies
        assert arguments['params'] == query_params

    async def test_should_return_httpx_given_oauth2_password_auth(self, respx_mock):
        token_url = 'https://token.com'
        access_token = secrets.token_hex(16)
        auth = OAuth2PasswordBearer(username='foo', password='bar', token_url=token_url)  # type: ignore
        config = Configuration(auth=auth)
        route = respx_mock.post(token_url, data=auth.dict(include={'username', 'password'}))
        route.return_value = httpx.Response(
            status_code=200, json={'token_type': 'bearer', 'access_token': access_token}
        )

        arguments = await build_read_method_arguments(config)

        assert arguments['http1'] is True
        assert arguments['http2'] is False
        assert arguments['headers'] == [('Authorization', f'Bearer {access_token}')]


class TestBuildWriteMethodArguments:
    """Tests function build_write_method_arguments"""

    async def test_should_call_function_build_read_method_arguments(self, mocker):
        build_read_mock = mocker.patch('httpcli.helpers.build_read_method_arguments', new=mock.AsyncMock())
        headers = cookies = query_params = [('foo', 'bar')]
        config = Configuration()
        await build_write_method_arguments(config, headers, cookies, query_params)

        build_read_mock.assert_awaited_once_with(config, headers, cookies, query_params)

    @pytest.mark.parametrize('arguments', [
        {'json_data': [('foo', 'bar')], 'form': [('foo', 'bar')]},
        {'json_data': [('foo', 'bar')], 'raw': b'boom'},
        {'raw': b'boom', 'form': [('foo', 'bar')]},
        {'json_data': [('foo', 'bar')], 'form': [('foo', 'bar')], 'raw': b'boom'},
    ])
    async def test_should_raise_error_when_setting_more_than_one_data_type(self, arguments):
        with pytest.raises(click.UsageError) as exc_info:
            await build_write_method_arguments(Configuration(), **arguments)

        message = 'you cannot mix different types of data, you must choose between one between form, json or raw'
        assert message == str(exc_info.value)

    async def test_should_return_data_dict_and_files_info_when_given_form_info_as_input(self, tmp_path):
        path = tmp_path / 'file.txt'
        message = 'just a text file'
        path.write_text('just a text file')
        form = (('foo', 'bar'), ('file', f'@{path}'))
        arguments = await build_write_method_arguments(Configuration(), form=form)

        assert arguments['data'] == {'foo': 'bar'}
        files = arguments['files']
        assert len(files) == 1
        assert files['file'].read() == message.encode()

    async def test_should_return_json_dict_when_given_json_data_as_input(self):
        json_data = (('foo', 'bar'),)
        arguments = await build_write_method_arguments(Configuration(), json_data=json_data)

        assert arguments['json'] == dict(json_data)

    async def test_should_return_raw_data_when_given_raw_data_as_input(self):
        raw = b'hello'
        arguments = await build_write_method_arguments(Configuration(), raw=raw)

        assert arguments['content'] == raw
