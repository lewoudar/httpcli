import asyncclick as click

from httpcli.configuration import Configuration
from httpcli.main import http
from httpcli.models import OAuth2PasswordBearer, BasicAuth


@click.command()
@click.pass_obj
def debug(obj: Configuration):
    click.echo(obj)


http.add_command(debug)

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


async def test_should_print_default_configuration(runner):
    result = await runner.invoke(http, ['debug'])
    config = Configuration(verify=False)

    assert result.exit_code == 0
    assert result.output == f'{config}\n'


async def test_should_print_correct_configuration_with_env_variables_set(monkeypatch, runner):
    follow_redirects = False
    proxy_url = 'https://proxy.com'
    monkeypatch.setenv('http_cli_follow_redirects', str(follow_redirects))
    monkeypatch.setenv('http_cli_proxy', proxy_url)
    monkeypatch.setenv('http_cli_timeout', '3')
    config = Configuration(follow_redirects=follow_redirects, proxy=proxy_url, verify=False, timeout=3)
    result = await runner.invoke(http, ['debug'])

    assert result.exit_code == 0
    assert result.output == f'{config}\n'


async def test_should_print_correct_configuration_with_given_configuration_file(runner, tmp_path):
    config_file = tmp_path / 'config.yaml'
    config_file.write_text(YAML_DATA)
    auth = BasicAuth(username='foo', password='bar')
    config = Configuration(proxy='https://proxy.com', version='h2', timeout=None, auth=auth, verify=False)
    result = await runner.invoke(http, ['--config-file', f'{config_file}', '--http-version', 'h1', 'debug'])

    assert result.exit_code == 0
    assert result.output == f'{config}\n'


async def test_should_print_correct_information_given_user_input(runner):
    auth = OAuth2PasswordBearer(username='foo', password='bar', token_url='http://token.com')
    http_version = 'h2'
    config = Configuration(version=http_version, auth=auth, verify=False, timeout=None)
    result = await runner.invoke(http, ['--auth', auth.json(), '--http-version', http_version, '-t', -1, 'debug'])

    assert result.exit_code == 0
    assert result.output == f'{config}\n'
