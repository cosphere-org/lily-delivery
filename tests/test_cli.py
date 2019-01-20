
from unittest import TestCase
from unittest.mock import call
import os

from click.testing import CliRunner
import pytest

from lily_delivery.cli import cli


class CLITestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.runner = CliRunner()

    #
    # DEPLOY_ANGULAR_CLI_TO_S3
    #
    def test_deploy_angular_cli_to_s3__makes_the_right_calls(self):

        cwd = self.tmpdir.mkdir('cwd')
        cwd.join('.lily_delivery.yaml').write('something')
        self.mocker.patch.object(os, 'getcwd').return_value = str(cwd)
        AngularCLIS3WebsiteDeployer = self.mocker.patch(  # noqa
            'lily_delivery.cli.AngularCLIS3WebsiteDeployer')

        result = self.runner.invoke(
            cli,
            [
                'deploy-angular-cli-to-s3',
                '--project',
                'my-project',
                '--environment',
                'integration'
            ])

        assert result.exit_code == 0
        assert result.output == ''
        assert AngularCLIS3WebsiteDeployer.call_args_list == [
            call(
                conf='something',
                environment='integration',
                project='my-project',
            ),
        ]
