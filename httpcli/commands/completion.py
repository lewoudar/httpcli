import subprocess  # nosec
from pathlib import Path

import asyncclick as click
import shellingham

from httpcli.console import console

SHELLS = ['bash', 'zsh', 'fish']
COMPLETION_DIR = '.cli_completions'


def install_bash_zsh(bash: bool = True) -> None:
    home = Path.home()
    completion_dir = home / '.cli_completions'
    if bash:
        shell = 'bash'
        shell_config_file = home / '.bashrc'
    else:
        shell = 'zsh'
        shell_config_file = home / '.zshrc'

    if not completion_dir.exists():
        completion_dir.mkdir()

    for cli in ['http', 'https']:
        try:
            command = f'_{cli.upper()}_COMPLETE={shell}_source {cli}'
            # bandit complains for shell injection, but we are not using untrusted string here, so it is fine.
            result = subprocess.run(command, shell=True, capture_output=True, check=True)  # nosec
        except subprocess.CalledProcessError:
            console.print(f'[error]unable to get completion script for {cli} cli.')
            raise click.Abort()

        completion_script = completion_dir / f'{cli}-complete.{shell}'
        completion_script.write_text(result.stdout.decode())

        with shell_config_file.open('a') as f:
            f.write(f'\n. {completion_script.absolute()}\n')


def install_fish() -> None:
    home = Path.home()
    completion_dir = home / '.config/fish/completions'
    if not completion_dir.exists():
        completion_dir.mkdir(parents=True)

    for cli in ['http', 'https']:
        try:
            command = f'_{cli.upper()}_COMPLETE=fish_source {cli}'
            # bandit complains for shell injection, but we are not using untrusted string here, so it is fine.
            result = subprocess.run(command, shell=True, capture_output=True, check=True)  # nosec
        except subprocess.CalledProcessError:
            console.print(f'[error]unable to get completion script for {cli} cli.')
            raise click.Abort()

        completion_script = completion_dir / f'{cli}.fish'
        completion_script.write_text(result.stdout.decode())


def _install_completion(shell: str) -> None:
    if shell == 'bash':
        install_bash_zsh()
    elif shell == 'zsh':
        install_bash_zsh(bash=False)
    else:
        install_fish()


@click.command('install-completion')
def install_completion():
    """
    Install completion script for bash, zsh and fish shells.
    You will need to restart the shell for the changes to be loaded.
    You don't need to it twice for "http" and "https" cli. Doing it one one will install the other.
    """
    try:
        shell, _ = shellingham.detect_shell()
    except shellingham.ShellDetectionFailure:
        console.print('[error]unable to detect the current shell')
        raise click.Abort()
    except RuntimeError as e:
        click.echo(f'[error]{e}')
        raise click.Abort()

    if shell not in SHELLS:
        console.print(f'[error]Your shell is not supported. Shells supported are: {", ".join(SHELLS)}')
        raise click.Abort()

    _install_completion(shell)
