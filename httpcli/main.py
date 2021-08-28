import click


@click.command()
def http():
    """HTTP CLI"""
    click.echo('OK')


if __name__ == '__main__':
    http()
