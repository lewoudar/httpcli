import click


@click.command()
def cli():
    """HTTP CLI"""
    click.echo('OK')


if __name__ == '__main__':
    cli()