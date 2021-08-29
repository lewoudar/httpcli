import click

from httpcli.configuration import Configuration, OAuth2PasswordBearer
from httpcli.main import http


@click.command()
@click.pass_obj
def debug(obj: Configuration):
    click.echo(obj)


http.add_command(debug)


def test_should_print_default_configuration(runner):
    result = runner.invoke(http, ['debug'])
    config = Configuration(verify=False)

    assert result.exit_code == 0
    assert result.output == f'{config}\n'


def test_should_print_correct_configuration_with_env_variables_set(monkeypatch, runner):
    follow_redirects = False
    proxy_url = 'https://proxy.com'
    monkeypatch.setenv('http_cli_follow_redirects', str(follow_redirects))
    monkeypatch.setenv('http_cli_proxy', proxy_url)
    config = Configuration(follow_redirects=follow_redirects, proxy=proxy_url, verify=False)
    result = runner.invoke(http, ['debug'])

    assert result.exit_code == 0
    assert result.output == f'{config}\n'


def test_should_print_correct_information_given_user_input(runner):
    auth = OAuth2PasswordBearer(
        type='oauth2', flow='password', username='foo', password='bar', token_url='http://token.com'
    )
    http_version = 'h2'
    config = Configuration(version=http_version, auth=auth, verify=False)
    result = runner.invoke(http, ['--auth', auth.json(), '--http-version', http_version, 'debug'])

    assert result.exit_code == 0
    assert result.output == f'{config}\n'
