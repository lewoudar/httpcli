import asyncclick as click
import pytest

from httpcli.configuration import Configuration
from httpcli.http import http
from httpcli.https import https
from httpcli.models import OAuth2PasswordBearer, BasicAuth


@click.command()
@click.pass_obj
def debug(obj: Configuration):
    click.echo(obj)


http.add_command(debug)
https.add_command(debug)

YAML_DATA = """
httpcli:
  version: h2
  proxy: https://proxy.com
  timeout: null
  auth:
    type: basic
    username: foo
    password: bar
"""

command_parametrize = pytest.mark.parametrize(('command', 'verify'), [
    (http, False),
    (https, True)
])


@command_parametrize
async def test_should_print_default_configuration(runner, command, verify):
    result = await runner.invoke(command, ['debug'])
    config = Configuration(verify=verify)

    assert result.exit_code == 0
    assert result.output == f'{config}\n'


@command_parametrize
async def test_should_print_correct_configuration_with_env_variables_set(monkeypatch, runner, command, verify):
    follow_redirects = False
    proxy_url = 'https://proxy.com'
    monkeypatch.setenv('http_cli_follow_redirects', str(follow_redirects))
    monkeypatch.setenv('http_cli_proxy', proxy_url)
    monkeypatch.setenv('http_cli_timeout', '3')
    config = Configuration(follow_redirects=follow_redirects, proxy=proxy_url, verify=verify, timeout=3)  # type: ignore
    result = await runner.invoke(command, ['debug'])

    assert result.exit_code == 0
    assert result.output == f'{config}\n'


@command_parametrize
async def test_should_print_correct_configuration_with_given_configuration_file(runner, tmp_path, command, verify):
    config_file = tmp_path / 'config.yaml'
    config_file.write_text(YAML_DATA)
    auth = BasicAuth(username='foo', password='bar')
    config = Configuration(proxy='https://proxy.com', version='h2', timeout=None, auth=auth, verify=verify)
    result = await runner.invoke(command, ['--config-file', f'{config_file}', '--http-version', 'h1', 'debug'])

    assert result.exit_code == 0
    assert result.output == f'{config}\n'


@command_parametrize
async def test_should_print_correct_information_given_user_input(runner, command, verify):
    auth = OAuth2PasswordBearer(username='foo', password='bar', token_url='http://token.com')  # type: ignore
    http_version = 'h2'
    config = Configuration(version=http_version, auth=auth, verify=verify, timeout=None)  # type: ignore
    result = await runner.invoke(command, ['--auth', auth.json(), '--http-version', http_version, '-t', -1, 'debug'])

    assert result.exit_code == 0
    assert result.output == f'{config}\n'


# https cert option tests

async def test_should_print_error_when_given_certificate_does_not_exist(runner):
    file = '/path/to/file'
    result = await runner.invoke(https, ['--cert', file, 'debug'])

    assert result.exit_code == 2
    assert f"'{file}' does not exist" in result.output


async def test_should_print_correct_info_when_given_certificate_exist(runner, tmp_path):
    path = tmp_path / 'cert.pem'
    path.write_text('fake certificate')
    config = Configuration()
    config.verify = str(path)
    result = await runner.invoke(https, ['--cert', str(path), 'debug'])

    assert result.exit_code == 0
    assert result.output == f'{config}\n'
