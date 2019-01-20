
import json
import os
import re
import shutil
import tempfile

from ..describer import Describer
from ..dependencies import S3, Cloudfront


class AngularCLIS3WebsiteDeployer(Describer):

    def __init__(self, environment, project, conf):

        self.project = project
        self.replacements = conf.get('replacements', [])
        self.meta = conf['meta']

        # -- FIXME: this will be replaced by the calls to lily-delivery
        # -- also the dependencies would be already loaded as appropriate
        # -- instances!!!!
        dependencies = conf['dependencies'][environment]

        dep = dependencies['hosting_s3']
        self.s3 = S3(
            access_key_id=dep['access_key_id'],
            secret_access_key=dep['secret_access_key'],
            region_name=dep['region'],
            bucket_name=dep['bucket_name'])

        dep = dependencies['hosting_cloudfront']
        self.cloudfront = Cloudfront(
            access_key_id=dep['access_key_id'],
            secret_access_key=dep['secret_access_key'],
            region_name=dep['region'],
            distribution_id=dep['distribution_id'])

    def deploy(self):
        with self.header('performing a deployment'):

            with self.subheader('copying build directory to temp location'):
                # -- preparation of the directory/file structure to be
                # -- deployed
                path, index_html_name, assets_name = (
                    self.copy_build_dir_to_versioned())

            # -- final AWS steps
            if (not self.s3.check_if_key_exists(index_html_name) and
                    not self.s3.check_if_key_exists(assets_name)):

                with self.subheader(f's3: uploading "{path}"'):
                    self.s3.upload_dir(path, self.meta)

                with self.subheader(f's3: updating website index.html file'):
                    self.s3.update_website_index(index_html_name)

                with self.subheader('cloudfront: frontend routing'):
                    self.cloudfront.update_frontend_routing(index_html_name)

                with self.subheader('cloudfront: invalidate cache'):
                    self.cloudfront.invalidate_cache()

    @property
    def build_path(self):
        with open(os.path.join(os.getcwd(), 'angular.json'), 'r') as f:
            angular_json = json.loads(f.read())
            conf = angular_json['projects'][self.project]

        return os.path.join(
            os.getcwd(),
            conf['architect']['build']['options']['outputPath'])

    @property
    def version(self):
        with open(os.path.join(os.getcwd(), 'package.json'), 'r') as f:
            package_json = json.loads(f.read())
            return package_json['version']

    def copy_build_dir_to_versioned(self):

        build_path = os.path.join(tempfile.mkdtemp(), 'build')
        version_dir = os.path.join(build_path, self.version)

        shutil.copytree(
            self.build_path,
            version_dir,
            copy_function=self.copy_with_renames)

        shutil.move(
            os.path.join(version_dir, 'index.html'),
            os.path.join(build_path, f'index-{self.version}.html'))

        return build_path, f'index-{self.version}.html', self.version

    def copy_with_renames(self, src, dst, *args, **kwargs):

        content_replacements = []
        for replacement in self.replacements:
            _, ext = os.path.splitext(src)
            if ext in replacement['file_extensions']:
                content_replacements.append(replacement)

        if content_replacements:

            with open(src, 'r') as f:
                content = f.read()
                for replacement in content_replacements:
                    content = content.replace(
                        replacement['from'],
                        replacement['to'].format(version=self.version))

            with open(dst, 'w') as f:
                f.write(content)

            return dst

        else:
            return shutil.copy2(src, dst, *args, **kwargs)
