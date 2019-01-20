
import json
import os
import tempfile
import textwrap
from unittest import TestCase
from unittest.mock import call

import pytest

from lily_delivery.deployers import AngularCLIS3WebsiteDeployer


class AngularCLIS3WebsiteDeployerTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.conf = {
            'meta': {
                'cache-control': 'max-age=7200, no-transform, public',
            },
            'replacements': [],
            'dependencies': {
                'integration': {
                    'hosting_s3': {
                        '@type': 'S3',
                        'access_key_id': '3489348',
                        'secret_access_key': '382938',
                        'region': 'east-eu',
                        'bucket_name': 'my_bucket',
                    },
                    'hosting_cloudfront': {
                        '@type': 'CLOUDFRONT',
                        'access_key_id': '473843',
                        'secret_access_key': '291039',
                        'region': 'center-eu',
                        'distribution_id': '854956849F8DFD',
                    },
                },
            },
        }
        self.deployer = AngularCLIS3WebsiteDeployer(
            'integration',
            'fe-app',
            conf=self.conf)

    #
    # DEPLOY
    #
    def test_deploy__makes_the_right_calls(self):

        self.mocker.patch.object(
            self.deployer,
            'copy_build_dir_to_versioned'
        ).return_value = '/tmp/1278', 'index-1.4.56.html', '1.4.56'
        self.mocker.patch.object(
            self.deployer.s3, 'check_if_key_exists').return_value = False
        s3_upload_dir = self.mocker.patch.object(
            self.deployer.s3, 'upload_dir')
        s3_update_website_index = self.mocker.patch.object(
            self.deployer.s3, 'update_website_index')
        cloudfront_update_frontend_routing = self.mocker.patch.object(
            self.deployer.cloudfront, 'update_frontend_routing')
        cloudfront_invalidate_cache = self.mocker.patch.object(
            self.deployer.cloudfront, 'invalidate_cache')

        self.mocker.patch.object(
            AngularCLIS3WebsiteDeployer,
            'version',
            '1.4.56')

        self.deployer.deploy()

        assert s3_upload_dir.call_args_list == [
            call(
                '/tmp/1278',
                {'cache-control': 'max-age=7200, no-transform, public'}),
        ]
        assert (
            s3_update_website_index.call_args_list ==
            [call('index-1.4.56.html')])
        assert (
            cloudfront_update_frontend_routing.call_args_list ==
            [call('index-1.4.56.html')])
        assert cloudfront_invalidate_cache.call_args_list == [call()]

    #
    # BUILD_PATH
    #
    def test_build_path__fetches_path_from_angular_json(self):

        project_dir = self.tmpdir.mkdir('project')
        project_dir.join('angular.json').write(json.dumps({
            'projects': {
                'fe-app': {
                    'architect': {
                        'build': {
                            'options': {
                                'outputPath': 'dist/fe-app',
                            }
                        }
                    }
                }
            }
        }))
        self.mocker.patch.object(os, 'getcwd').return_value = str(project_dir)

        assert self.deployer.build_path == os.path.join(
            str(project_dir), 'dist/fe-app')

    #
    # VERSION
    #
    def test_version__fetches_version_from_package_json(self):

        project_dir = self.tmpdir.mkdir('project')
        project_dir.join('package.json').write(json.dumps({
            'name': 'fe-app',
            'version': '0.3.14',
        }))
        self.mocker.patch.object(os, 'getcwd').return_value = str(project_dir)

        assert self.deployer.version == '0.3.14'

    #
    # COPY_BUILD_DIR_TO_VERSIONED
    #
    def test_copy_build_dir_to_versioned__copy_dist_to_some_temp_dir(self):

        # -- source build dir
        build_dir = self.tmpdir.mkdir('build')
        build_dir.join('index.html').write('<html>INDEX</html>')
        build_dir.join('main.js').write('console.log("this is it");')
        assets_dir = build_dir.mkdir('assets')
        assets_dir.join('logo.svg').write('<svg></svg>')
        assets_dir.join('image.png').write('some.bytes')

        self.mocker.patch.object(
            AngularCLIS3WebsiteDeployer,
            'build_path',
            str(build_dir))
        self.mocker.patch.object(
            AngularCLIS3WebsiteDeployer,
            'version',
            '1.4.56')

        # -- target temp dir
        temp_dir = self.tmpdir.mkdir('temp')

        self.mocker.patch.object(
            tempfile,
            'mkdtemp'
        ).return_value = str(temp_dir)

        path, index_html_name, assets_name = (
            self.deployer.copy_build_dir_to_versioned())

        assert path == os.path.join(str(temp_dir), 'build')
        assert index_html_name == 'index-1.4.56.html'
        assert assets_name == '1.4.56'

        # -- assert structure
        assert (
            set(os.listdir(path)) ==
            set(['index-1.4.56.html', '1.4.56']))
        assert (
            set(os.listdir(os.path.join(path, '1.4.56'))) ==
            set(['assets', 'main.js']))
        assert (
            set(os.listdir(os.path.join(path, '1.4.56', 'assets'))) ==
            set(['logo.svg', 'image.png']))

        # -- assert content
        assert temp_dir.join(
            'build/index-1.4.56.html').read() == '<html>INDEX</html>'
        assert temp_dir.join(
            'build/1.4.56/main.js').read() == 'console.log("this is it");'
        assert temp_dir.join(
            'build/1.4.56/assets/logo.svg').read() == '<svg></svg>'
        assert temp_dir.join(
            'build/1.4.56/assets/image.png').read() == 'some.bytes'

    def test_copy_build_dir_to_versioned__with_replacements(self):

        deployer = AngularCLIS3WebsiteDeployer(
            'integration',
            'fe-app',
            {
                **self.conf,
                'replacements': [
                    {
                        'from': '/assets/monaco',
                        'to': '/{version}/assets/monaco',
                        'file_extensions': ['.js'],
                    }
                ],
            })

        # -- source build dir
        build_dir = self.tmpdir.mkdir('build')
        build_dir.join('index.html').write('<html>INDEX</html>')
        build_dir.join('main.js').write(textwrap.dedent('''
            console.log("/assets/monaco/logo.png");

            // whatever
            someFn.read("but_why/assets/monaco/nothing/1.jpg");

            // omit this one
            console.log("assets/monaco/nothing/1.jpg");
        '''))
        assets_dir = build_dir.mkdir('assets')
        assets_dir.join('image.png').write('some.bytes')
        assets_dir.join('logo.svg').write(
            '<svg>/assets/monaco/nothing/1.jpg</svg>')

        self.mocker.patch.object(
            AngularCLIS3WebsiteDeployer,
            'build_path',
            str(build_dir))
        self.mocker.patch.object(
            AngularCLIS3WebsiteDeployer,
            'version',
            '1.4.56')

        # -- target temp dir
        temp_dir = self.tmpdir.mkdir('temp')

        self.mocker.patch.object(
            tempfile,
            'mkdtemp'
        ).return_value = str(temp_dir)

        path, index_html_name, assets_name = (
            deployer.copy_build_dir_to_versioned())

        assert path == os.path.join(str(temp_dir), 'build')
        assert index_html_name == 'index-1.4.56.html'
        assert assets_name == '1.4.56'

        # -- assert structure
        assert (
            set(os.listdir(path)) ==
            set(['index-1.4.56.html', '1.4.56']))
        assert (
            set(os.listdir(os.path.join(path, '1.4.56'))) ==
            set(['assets', 'main.js']))
        assert (
            set(os.listdir(os.path.join(path, '1.4.56', 'assets'))) ==
            set(['logo.svg', 'image.png']))

        # -- assert content
        assert temp_dir.join(
            'build/index-1.4.56.html').read() == '<html>INDEX</html>'
        assert temp_dir.join(
            'build/1.4.56/main.js'
        ).read() == textwrap.dedent('''
            console.log("/1.4.56/assets/monaco/logo.png");

            // whatever
            someFn.read("but_why/1.4.56/assets/monaco/nothing/1.jpg");

            // omit this one
            console.log("assets/monaco/nothing/1.jpg");
        ''')
        assert temp_dir.join(
            'build/1.4.56/assets/logo.svg'
        ).read() == '<svg>/assets/monaco/nothing/1.jpg</svg>'
        assert temp_dir.join(
            'build/1.4.56/assets/image.png').read() == 'some.bytes'

    #
    # UPLOAD_TO_S3
    #
    def test_upload_to_s3__fails_release_already_exists(self):
        pass

    def test_upload_to_s3__success(self):
        pass

    #
    # REFRESH_S3_INDEX
    #
    def test_refresh_s3_index__applies_index_html_changes_to_website_hosting(
            self):
        pass

    #
    # REFRESH_CLOUDFRONT
    #
    def test_refresh_cloudfront__applies_invalidation_on_cloudfront(self):
        pass
