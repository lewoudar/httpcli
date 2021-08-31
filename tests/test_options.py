import click

from httpcli.models import DigestAuth
from httpcli.options import global_cli_options, http_query_options


@click.command()
@global_cli_options
def debug_global_options(proxy, http_version, backend, auth, follow_redirects, timeout):
    click.echo(proxy)
    click.echo(http_version)
    click.echo(backend)
    click.echo(auth)
    click.echo(follow_redirects)
    click.echo(timeout)


@click.command()
@http_query_options
def debug_http_options(query_params, headers, cookies):
    click.echo(query_params)
    click.echo(headers)
    click.echo(cookies)


def test_global_cli_options_is_correctly_formed(runner):
    auth = DigestAuth(username='user', password='pass')
    proxy = 'http://proxy.com'
    arguments = ['--http-version', 'h2', '--auth', auth.json(), '--proxy', proxy, '-N', '--backend', 'trio', '-t', 3]
    result = runner.invoke(debug_global_options, arguments)

    assert result.exit_code == 0
    assert result.output == f'{proxy}\nh2\ntrio\n{auth}\nFalse\n3.0\n'


def test_http_query_options_is_correctly_formed(runner):
    result = runner.invoke(debug_http_options, ['--header', 'foo:bar', '--cookie', 'foo:bar', '--query', 'foo:bar'])

    assert result.exit_code == 0
    assert result.output == f'{(("foo", "bar"),)}\n' * 3
