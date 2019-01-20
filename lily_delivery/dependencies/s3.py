
import gzip
import os

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
import click

from ..content_type import get_content_type
from ..describer import Describer


class S3(Describer):

    def __init__(
            self,
            access_key_id,
            secret_access_key,
            region_name,
            bucket_name):

        self.client = boto3.client(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name)
        self.bucket_name = bucket_name

    def is_valid(self):
        """Validate if connection credentials are correct.

        It will perform it by simple attempting to read the content of the
        bucket.

        """
        try:
            response = self.client.list_objects(
                Bucket=self.bucket_name, MaxKeys=1)

            return response['ResponseMetadata']['HTTPStatusCode'] == 200

        except ClientError as e:
            if e.response['ResponseMetadata']['HTTPStatusCode'] in [403, 404]:
                return False

            else:
                raise click.ClickException(
                    'faced problems when connecting to AWS S3')

        except EndpointConnectionError:
            raise click.ClickException(
                'could not connect to the bucket specified')

    def check_if_key_exists(self, key):
        try:
            response = self.client.get_object(
                Key=key,
                Bucket=self.bucket_name)

            return response['ResponseMetadata']['HTTPStatusCode'] == 200

        except ClientError as e:
            if e.response['ResponseMetadata']['HTTPStatusCode'] == 404:
                return False

            else:
                raise click.ClickException(
                    'faced problems when connecting to AWS S3')

        except EndpointConnectionError:
            raise click.ClickException(
                'could not connect to bucket specified')

    def upload_dir(self, path, meta):

        for subdir, dirs, files in os.walk(path):
            for file in files:
                filepath = os.path.join(subdir, file)

                with open(filepath, 'rb') as f:

                    key = filepath[len(path) + 1:]
                    with self.text(f'uploading: {key}'):
                        self.client.put_object(
                            ACL='public-read',
                            Key=key,
                            Bucket=self.bucket_name,
                            Body=gzip.compress(f.read()),
                            ContentType=get_content_type(filepath),
                            CacheControl=meta['cache-control'],
                            ContentEncoding='gzip')

    def update_website_index(self, index_html_key):

        try:
            response = self.client.put_bucket_website(
                Bucket=self.bucket_name,
                WebsiteConfiguration={
                    'IndexDocument': {
                        'Suffix': index_html_key,
                    },
                })

        except ClientError as e:
            raise click.ClickException('failed to replace an index document')
