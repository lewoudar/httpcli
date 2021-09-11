import asyncclick as click

from httpcli.models import DigestAuth
from httpcli.options import global_cli_options, http_query_options


@click.command()
@global_cli_options
def debug_global_options(proxy, http_version, auth, follow_redirects, timeout, config_file):
    click.echo(proxy)
    click.echo(http_version)
    click.echo(auth)
    click.echo(follow_redirects)
    click.echo(timeout)
    click.echo(config_file)


@click.command()
@http_query_options
def debug_http_options(query_params, headers, cookies):
    click.echo(query_params)
    click.echo(headers)
    click.echo(cookies)


async def test_global_cli_options_is_correctly_formed(runner):
    auth = DigestAuth(username='user', password='pass')
    proxy = 'http://proxy.com'
    arguments = ['--http-version', 'h2', '--auth', auth.json(), '--proxy', proxy, '-N', '-t', 3]
    result = await runner.invoke(debug_global_options, arguments)

    assert result.exit_code == 0
    assert result.output == f'{proxy}\nh2\n{auth}\nFalse\n3.0\n\n'


async def test_http_query_options_is_correctly_formed(runner):
    arguments = ['--header', 'foo:bar', '--cookie', 'foo:bar', '--query', 'foo:bar']
    result = await runner.invoke(debug_http_options, arguments)

    assert result.exit_code == 0
    assert result.output == f'{(("foo", "bar"),)}\n' * 3
