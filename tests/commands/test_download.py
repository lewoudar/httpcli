import httpx
import pytest
from respx.patterns import M

from httpcli.commands.download import (
    get_filename_from_content_disposition, get_filename_from_url, get_filename
)
from httpcli.http import http
from httpcli.https import https


class TestGetFilenameFromContentDisposition:
    """Tests function get_filename_from_content_disposition"""

    def test_should_return_filename_when_content_disposition_sets_filename(self):
        response = httpx.Response(200, headers={'Content-Disposition': 'attachment; filename="filename.jpg"'})

        assert get_filename_from_content_disposition(response) == 'filename.jpg'

    def test_should_return_empty_filename_when_filename_not_present_in_content_disposition(self):
        response = httpx.Response(200, headers={'Content-Disposition': 'attachment'})

        assert get_filename_from_content_disposition(response) == ''

    def test_should_return_empty_filename_when_content_disposition_header_is_not_set(self):
        response = httpx.Response(200)

        assert get_filename_from_content_disposition(response) == ''


class TestGetFilenameFromUrl:
    """Tests get_filename_from_url"""

    def test_should_return_filename_with_extension_when_extension_present_in_url(self):
        request = httpx.Request('GET', 'https://download/image.png')
        response = httpx.Response(200, request=request)

        assert get_filename_from_url(response) == 'image.png'

    @pytest.mark.parametrize(('content_type', 'extension'), [
        ('image/png', 'png'),
        ('text/html', 'html'),
        ('text/plain', 'txt')
    ])
    def test_should_filename_with_extension_when_content_type_is_set(self, content_type, extension):
        request = httpx.Request('GET', 'https://download/image')
        response = httpx.Response(200, request=request, headers={'content-type': content_type})

        assert get_filename_from_url(response) == f'image.{extension}'

    def test_should_return_url_last_part_when_no_content_type_is_set(self):
        request = httpx.Request('GET', 'https://download/image')
        response = httpx.Response(200, request=request)

        assert get_filename_from_url(response) == 'image'

    def test_should_return_url_last_part_when_content_type_is_unknown(self):
        request = httpx.Request('GET', 'https://download/image')
        response = httpx.Response(200, request=request, headers={'content-type': 'text/unknown'})

        assert get_filename_from_url(response) == 'image'


class TestGetFilename:
    """Tests get_filename"""

    def test_should_return_filename_from_content_disposition_header(self, mocker):
        filename_from_url_mock = mocker.patch('httpcli.commands.download.get_filename_from_url')
        response = httpx.Response(200, headers={'Content-Disposition': 'attachment; filename="filename.jpg"'})

        assert get_filename(response) == 'filename.jpg'
        filename_from_url_mock.assert_not_called()

    def test_should_return_filename_from_url(self):
        request = httpx.Request('GET', 'https://download/image.png')
        response = httpx.Response(200, request=request)

        assert get_filename(response) == 'image.png'


class TestDownloadCommand:
    """Tests download command"""

    @pytest.mark.parametrize('command', [http, https])
    async def test_should_print_error_when_destination_is_not_a_directory(self, runner, tmp_path, command):
        path = tmp_path / 'file.txt'
        path.write_text('a file')
        result = await runner.invoke(command, ['download', '-d', f'{path}'])

        assert result.exit_code == 2
        assert 'is a file' in result.output

    @pytest.mark.parametrize('command', [http, https])
    async def test_should_print_error_when_destination_does_not_exist(self, runner, command):
        result = await runner.invoke(command, ['download', '-d', '/path/to/destination'])

        assert result.exit_code == 2
        assert 'does not exist' in result.output

    @pytest.mark.parametrize('command', [http, https])
    async def test_should_print_error_when_url_in_file_is_not_correct(self, runner, tmp_path, command):
        urls = ['https://foo.com/image.png', 'image2.png']
        path = tmp_path / 'file.txt'
        path.write_text('\n'.join(urls))

        result = await runner.invoke(command, ['download', '-f', f'{path}'])

        assert result.exit_code == 2
        assert 'validation error for FileModel' in result.output

    @pytest.mark.parametrize('command', [http, https])
    @pytest.mark.parametrize('status_code', [307, 400])
    async def test_should_print_correct_error_when_download_fail(
            self, runner, respx_mock, tmp_path, command, status_code
    ):
        respx_mock.route(method='GET', host='images.com') % status_code
        url = 'https://images.com/image.png'
        result = await runner.invoke(command, ['download', url, '-d', f'{tmp_path}'])

        assert result.exit_code == 0
        output = result.output
        assert f'❌ {url} (image.png)\n' in output
        assert 'Downloading ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00Downloads completed! 🌟\n' in output

    @pytest.mark.parametrize('command', [http, https])
    async def test_should_print_error_when_unexpected_error_happens(self, runner, respx_mock, tmp_path, command):
        respx_mock.route(method='GET', host='images.com').mock(side_effect=httpx.TransportError('boom!'))
        url = 'https://images.com/image.png'
        result = await runner.invoke(command, ['download', url, '-d', f'{tmp_path}'])

        assert result.exit_code == 0
        output = result.output
        assert f'unable to fetch {url}, reason: boom!\n' in output
        assert 'Downloading ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00Downloads completed! 🌟\n' in output

    @pytest.mark.parametrize('command', [http, https])
    @pytest.mark.parametrize('current_dir', [True, False])
    async def test_should_print_correct_output_when_downloads_are_ok(
            self, runner, respx_mock, tmp_path, command, current_dir
    ):
        path = tmp_path / 'urls.txt'
        # urls in file
        urls = ['https://dummy.com/file1', 'https://dummy.com/file2']
        path.write_text('\n'.join(urls))
        respx_mock.route(method='GET', host='dummy.com') % dict(headers={'content-type': 'text/plain'})

        # urls passed on the command line
        command_line_urls = ['https://images.com/image.png', 'https://foo.com/image1.png']
        hosts_pattern = M(host='images.com') | M(host='foo.com')
        respx_mock.route(hosts_pattern, method='GET') % 200

        dir_argument = [] if current_dir else ['-d', f'{tmp_path}']
        result = await runner.invoke(command, ['download', *command_line_urls, '-f', f'{path}', *dir_argument])

        assert result.exit_code == 0
        output = result.output
        assert '✅ https://dummy.com/file1 (file1.txt)\n' in output
        assert '✅ https://dummy.com/file2 (file2.txt)\n' in output
        assert '✅ https://images.com/image.png (image.png)\n' in output
        assert '✅ https://foo.com/image1.png (image1.png)\n' in output
        assert 'Downloading ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00Downloads completed! 🌟\n' in output

        # cleanup
        if current_dir:
            path = tmp_path.cwd()
            for file in path.glob('*.png'):
                file.unlink()
            for file in path.glob('*.txt'):
                file.unlink()
