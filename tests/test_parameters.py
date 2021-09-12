import json

import asyncclick as click
import pytest

from httpcli.models import BasicAuth
from httpcli.parameters import AUTH_PARAM, URL, QUERY, HEADER, COOKIE, JSON, FORM, RAW_PAYLOAD


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


@click.command()
@click.option('-f', '--form', type=FORM)
def debug_form_param(form):
    click.echo(form)


@click.command()
@click.option('-j', '--json', 'json_param', type=JSON)
def debug_json_param(json_param):
    click.echo(json_param)


@click.command()
@click.option('-r', '--raw', type=RAW_PAYLOAD)
def debug_raw_payload(raw):
    click.echo(raw)


class TestAuthParam:
    """Tests AuthParam class"""

    @pytest.mark.parametrize(('auth', 'error_message'), [
        ('4', 'authentication information is not valid'),
        (str({'type': 'basic', 'username': 'foo'}), 'is not a valid json string')
    ])
    async def test_should_print_error_given_wrong_input(self, runner, auth, error_message):
        result = await runner.invoke(debug_auth, ['--auth', auth])
        assert 2 == result.exit_code
        assert error_message in result.output

    async def test_should_print_auth_info_given_correct_input(self, runner):
        auth = BasicAuth(username='foo', password='bar')
        result = await runner.invoke(debug_auth, ['--auth', auth.json()])

        assert result.exit_code == 0
        assert result.output == f'{auth}\n'


class TestUrlParam:
    """Tests UrlParam class"""

    @pytest.mark.parametrize('url', ['4', 'hi://foo.com'])
    async def test_should_print_error_given_wrong_input(self, runner, url):
        result = await runner.invoke(debug_url, ['--url', url])

        assert result.exit_code == 2
        assert f'{url} is not a valid url' in result.output

    @pytest.mark.parametrize('url', ['http://url.com', 'https://url.com'])
    async def test_should_print_url_given_correct_input(self, runner, url):
        result = await runner.invoke(debug_url, ['--url', url])

        assert result.exit_code == 0
        assert result.output == f'{url}\n'


class TestHttpParam:
    """Tests HTTPParameter subclasses (query, cookie and header)"""

    @pytest.mark.parametrize('value', ['foo:bar:tar', 'foo'])
    @pytest.mark.parametrize('http_param', ['--header', '--cookie', '--query'])
    async def test_should_print_error_when_input_is_wrong(self, runner, value, http_param):
        result = await runner.invoke(debug_http_param, [http_param, value])

        assert result.exit_code == 2
        assert f"'{http_param}': {value} is not in the form key:value" in result.output

    async def test_should_print_http_params_given_correct_input(self, runner):
        arguments = ['--header', 'foo:bar', '--cookie', 'foo:bar', '--query', 'foo:bar']
        result = await runner.invoke(debug_http_param, arguments)

        assert result.exit_code == 0
        assert result.output == f'{("foo", "bar")}\n' * 3


class TestFormParam:
    """Tests FormParam class"""

    @pytest.mark.parametrize('value', ['a', 'a:b:c'])
    async def test_should_print_error_when_param_is_badly_formed(self, runner, value):
        result = await runner.invoke(debug_form_param, ['-f', value])

        assert result.exit_code == 2
        assert f'{value} is not in the form key:value' in result.output

    async def test_should_print_error_when_given_file_does_not_exist(self, runner):
        result = await runner.invoke(debug_form_param, ['-f', 'foo:@foo.txt'])

        assert result.exit_code == 2
        assert 'foo.txt file does not exist' in result.output

    async def test_should_print_correct_value_when_given_correct_filename(self, runner, tmp_path):
        path = tmp_path / 'file.txt'
        path.write_text('just a test file')
        result = await runner.invoke(debug_form_param, ['-f', f'foo:@{path}'])

        assert result.exit_code == 0
        assert result.output == str(('foo', f'@{path}')) + '\n'

    async def test_should_print_correct_value_when_given_correct_input(self, runner):
        result = await runner.invoke(debug_form_param, ['-f', 'foo:bar'])

        assert result.exit_code == 0
        assert result.output == str(('foo', 'bar')) + '\n'


class TestJsonParam:
    """Tests JsonParam class"""

    @pytest.mark.parametrize('value', ['a', 'a:b:c'])
    async def test_should_print_error_when_param_is_badly_formed(self, runner, value):
        result = await runner.invoke(debug_json_param, ['-j', value])

        assert result.exit_code == 2
        assert f'{value} is not in the form key:value' in result.output

    async def test_should_print_error_when_given_json_file_does_not_exist(self, runner):
        result = await runner.invoke(debug_json_param, ['-j', 'foo:@foo.json'])

        assert result.exit_code == 2
        assert 'foo.json file does not exist' in result.output

    async def test_should_print_error_when_given_value_is_not_valid_json(self, runner):
        value = [1, 2, '3']
        result = await runner.invoke(debug_json_param, ['-j', f'foo:={value}'])

        assert result.exit_code == 2
        assert f'{value} is not a valid json value' in result.output

    async def test_should_print_value_when_given_correct_json_file(self, runner, tmp_path):
        json_file = tmp_path / 'data.json'
        data = [1, 2, 3]
        output = ('a', data)
        with json_file.open('w') as f:
            json.dump(data, f)

        result = await runner.invoke(debug_json_param, ['-j', f'a:@{json_file}'])

        assert result.exit_code == 0
        assert result.output == f'{output}\n'

    @pytest.mark.parametrize(('value', 'output'), [
        ('foo:bar', f"{('foo', 'bar')}\n"),
        ("a:=2", f"{('a', 2)}\n"),
        ('foo:=[1, 2, "3"]', f"{('foo', [1, 2, '3'])}\n")
    ])
    async def test_should_print_value_when_given_correct_input(self, runner, value, output):
        result = await runner.invoke(debug_json_param, ['-j', value])

        assert result.exit_code == 0
        assert result.output == output


class TestRawPayloadParam:
    """Tests RawPayloadParam class"""

    async def test_should_print_error_when_given_file_does_not_exist(self, runner):
        result = await runner.invoke(debug_raw_payload, ['-r', '@foo.txt'])

        assert result.exit_code == 2
        assert 'foo.txt file does not exist' in result.output

    @pytest.mark.parametrize('value', ['Just some random data', b'Just some random data'])
    async def test_should_print_correct_output_given_a_file_as_input(self, runner, value, tmp_path):
        path = tmp_path / 'data.txt'
        if isinstance(value, str):
            path.write_text(value)
        else:
            path.write_bytes(value)
            value = value.decode()

        result = await runner.invoke(debug_raw_payload, ['-r', f'@{path}'])

        assert result.exit_code == 0
        assert result.output == f'{value}\n'

    async def test_should_print_correct_output_given_correct_input(self, runner):
        value = 'Just some random data'
        result = await runner.invoke(debug_raw_payload, ['-r', value])

        assert result.exit_code == 0
        assert result.output == f'{value}\n'
