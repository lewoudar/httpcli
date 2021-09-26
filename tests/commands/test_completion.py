import os
import subprocess

import pytest
from shellingham import ShellDetectionFailure

from httpcli.commands.completion import SHELLS
from httpcli.http import http
from httpcli.https import https

command_parametrize = pytest.mark.parametrize('command', [http, https])


@command_parametrize
async def test_should_print_error_when_shell_is_not_detected(mocker, runner, command):
    mocker.patch('shellingham.detect_shell', side_effect=ShellDetectionFailure)
    result = await runner.invoke(command, ['install-completion'])

    assert result.exit_code == 1
    assert 'unable to detect the current shell\nAborted!\n' == result.output


@command_parametrize
async def test_should_print_error_when_os_name_is_unknown(monkeypatch, runner, command):
    os_name = 'foo'
    monkeypatch.setattr(os, 'name', os_name)
    result = await runner.invoke(command, ['install-completion'])

    assert result.exit_code == 1
    assert os_name in result.output
    assert 'Aborted!\n' in result.output


@command_parametrize
async def test_should_print_error_if_shell_is_not_supported(mocker, runner, command):
    mocker.patch('shellingham.detect_shell', return_value=('pwsh', 'C:\\bin\\pwsh'))
    result = await runner.invoke(command, ['install-completion'])

    assert result.exit_code == 1
    shells_string = ', '.join(SHELLS)
    assert f'Your shell is not supported. Shells supported are: {shells_string}\nAborted!\n' == result.output


@command_parametrize
@pytest.mark.parametrize('shell', [
    ('bash', '/bin/bash'),
    ('zsh', '/bin/zsh'),
    ('fish', '/bin/fish')
])
async def test_should_print_error_when_user_cannot_retrieve_completion_script(tmp_path, mocker, runner, command, shell):
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    mocker.patch('shellingham.detect_shell', return_value=shell)
    mocker.patch('subprocess.run', side_effect=subprocess.CalledProcessError(returncode=1, cmd='http'))
    result = await runner.invoke(command, ['install-completion'])

    assert result.exit_code == 1
    assert 'unable to get completion script for http cli.\nAborted!\n' == result.output


@command_parametrize
async def test_should_create_completion_file_and_install_it_for_bash_shell(tmp_path, mocker, runner, command):
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    mocker.patch('shellingham.detect_shell', return_value=('bash', '/bin/bash'))
    cli_completion_dir = tmp_path / '.cli_completions'
    completion_file = cli_completion_dir / f'{command.name}-complete.bash'
    bashrc_file = tmp_path / '.bashrc'

    result = await runner.invoke(command, ['install-completion'])

    assert result.exit_code == 0
    # completion files check
    assert cli_completion_dir.is_dir()
    assert completion_file.is_file()
    content = completion_file.read_text()

    assert content.startswith('_%s_completion() {' % command.name)
    assert content.endswith(f'_{command.name}_completion_setup;\n\n')

    # .bashrc check
    lines = [line for line in bashrc_file.read_text().split('\n') if line]
    expected = [f'. {cli_completion_dir / "http-complete.bash"}', f'. {cli_completion_dir / "https-complete.bash"}']
    assert lines == expected


@command_parametrize
async def test_should_create_completion_file_and_install_it_for_zsh_shell(tmp_path, mocker, runner, command):
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    mocker.patch('shellingham.detect_shell', return_value=('zsh', '/bin/zsh'))
    cli_completion_dir = tmp_path / '.cli_completions'
    completion_file = cli_completion_dir / f'{command.name}-complete.zsh'
    zshrc_file = tmp_path / '.zshrc'

    result = await runner.invoke(command, ['install-completion'])

    assert result.exit_code == 0
    # completion files check
    assert cli_completion_dir.is_dir()
    assert completion_file.is_file()
    content = completion_file.read_text()

    assert content.startswith(f'#compdef {command.name}')
    assert content.endswith(f'compdef _{command.name}_completion {command.name};\n\n')

    # .bashrc check
    lines = [line for line in zshrc_file.read_text().split('\n') if line]
    expected = [f'. {cli_completion_dir / "http-complete.zsh"}', f'. {cli_completion_dir / "https-complete.zsh"}']
    assert lines == expected


@command_parametrize
async def test_should_create_completion_file_and_install_it_for_fish_shell(tmp_path, mocker, runner, command):
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    mocker.patch('shellingham.detect_shell', return_value=('fish', '/bin/fish'))
    completion_dir = tmp_path / '.config/fish/completions'

    result = await runner.invoke(command, ['install-completion'])

    assert result.exit_code == 0
    assert completion_dir.is_dir()

    for cli in ['http', 'https']:
        completion_file = completion_dir / f'{cli}.fish'
        assert completion_file.is_file()
        content = completion_file.read_text()
        assert content.startswith(f'function _{cli}_completion')
        assert content.endswith(f'"(_{cli}_completion)";\n\n')
