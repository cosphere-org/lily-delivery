
import click

from deployers import S3WebsiteDeployer


@click.group()
def cli():
    """Expose multiple commands allowing one to work with lily_deployer."""
    pass


@click.command()
@click.option(
    '--environment', default='integration')
def deploy(environment):

    S3WebsiteDeployer().deploy()


cli.add_command(deploy)
