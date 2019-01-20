
import os

import yaml
import click

from .deployers import AngularCLIS3WebsiteDeployer


@click.group()
def cli():
    """Expose multiple commands allowing one to work with lily_deployer."""
    pass


@click.command()
@click.option('--project')
@click.option(
    '--environment', default='integration')
def deploy_angular_cli_to_s3(project, environment):

    with open(os.path.join(os.getcwd(), '.lily_delivery.yaml'), 'r') as f:
        conf = yaml.load(f.read())

    AngularCLIS3WebsiteDeployer(
        environment=environment,
        project=project,
        conf=conf).deploy()


cli.add_command(deploy_angular_cli_to_s3)
