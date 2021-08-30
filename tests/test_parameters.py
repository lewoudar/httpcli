import click
import pytest

from httpcli.models import BasicAuth
from httpcli.parameters import AUTH_PARAM, URL, QUERY, HEADER, COOKIE


@click.command()
@click.option('--auth', type=AUTH_PARAM)
def debug_auth(auth):
    click.echo(auth)


@click.command()
@click.option('--url', type=URL)
def debug_url(url):
    click.echo(url)


@click.command()
@click.option('--header', type=HEADER)
@click.option('--cookie', type=COOKIE)
@click.option('--query', type=QUERY)
def debug_http_param(header, cookie, query):
    click.echo(header)
    click.echo(cookie)
    click.echo(query)


class TestAuthParam:
    """Tests AuthParameter class"""

    @pytest.mark.parametrize(('auth', 'error_message'), [
        ('4', 'authentication information is not valid'),
        (str({'type': 'basic', 'username': 'foo'}), 'is not a valid json string')
    ])
    def test_should_print_error_given_wrong_input(self, runner, auth, error_message):
        result = runner.invoke(debug_auth, ['--auth', auth])
        assert 2 == result.exit_code
        assert error_message in result.output

    def test_should_print_auth_info_given_correct_input(self, runner):
        auth = BasicAuth(username='foo', password='bar')
        result = runner.invoke(debug_auth, ['--auth', auth.json()])

        assert result.exit_code == 0
        assert result.output == f'{auth}\n'


class TestUrlParam:
    """Tests UrlParameter class"""

    @pytest.mark.parametrize('url', ['4', 'hi://foo.com'])
    def test_should_print_error_given_wrong_input(self, runner, url):
        result = runner.invoke(debug_url, ['--url', url])

        assert result.exit_code == 2
        assert f'{url} is not a valid url' in result.output

    @pytest.mark.parametrize('url', ['http://url.com', 'https://url.com'])
    def test_should_print_url_given_correct_input(self, runner, url):
        result = runner.invoke(debug_url, ['--url', url])

        assert result.exit_code == 0
        assert result.output == f'{url}\n'


class TestHttpParam:
    """Tests HTTPParameter subclasses (query, cookie and header)"""

    @pytest.mark.parametrize('value', ['foo:bar:tar', 'foo'])
    @pytest.mark.parametrize('http_param', ['--header', '--cookie', '--query'])
    def test_should_print_error_when_input_is_wrong(self, runner, value, http_param):
        result = runner.invoke(debug_http_param, [http_param, value])

        assert result.exit_code == 2
        assert f"'{http_param}': {value} is not in the form key:value" in result.output

    def test_should_print_http_params_given_correct_input(self, runner):
        arguments = ['--header', 'foo:bar', '--cookie', 'foo:bar', '--query', 'foo:bar']
        result = runner.invoke(debug_http_param, arguments)

        assert result.exit_code == 0
        assert result.output == f'{("foo", "bar")}\n' * 3
