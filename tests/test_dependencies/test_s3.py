
import gzip
from unittest import TestCase
from unittest.mock import call

from botocore.exceptions import EndpointConnectionError, ClientError
import click
import pytest

from lily_delivery.dependencies import S3


class S3TestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):

        self.s3 = S3(
            access_key_id='3489348',
            secret_access_key='382938',
            region_name='east-eu',
            bucket_name='my_bucket')

    #
    # IS_VALID
    #
    def test_is_valid(self):

        self.mocker.patch.object(
            self.s3.client,
            'list_objects'
        ).return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        assert self.s3.is_valid() is True

    def test_is_valid__invalid(self):

        self.mocker.patch.object(
            self.s3.client,
            'list_objects'
        ).side_effect = [
            ClientError(
                operation_name='list_objects',
                error_response={'ResponseMetadata': {'HTTPStatusCode': 403}}),
            ClientError(
                operation_name='list_objects',
                error_response={'ResponseMetadata': {'HTTPStatusCode': 404}}),
        ]

        assert self.s3.is_valid() is False
        assert self.s3.is_valid() is False

    def test_is_valid__client_or_connection_problem(self):

        self.mocker.patch.object(
            self.s3.client,
            'list_objects'
        ).side_effect = [
            ClientError(
                operation_name='list_objects',
                error_response={'ResponseMetadata': {'HTTPStatusCode': 500}}),
            EndpointConnectionError(endpoint_url='/some/url'),
        ]

        with pytest.raises(click.ClickException) as e:
            self.s3.is_valid()

        assert e.value.message == 'faced problems when connecting to AWS S3'

        with pytest.raises(click.ClickException) as e:
            self.s3.is_valid()

        assert e.value.message == 'could not connect to the bucket specified'

    #
    # CHECK_IF_KEY_EXISTS
    #
    def test_check_if_key_exists__exists(self):

        get_object = self.mocker.patch.object(self.s3.client, 'get_object')
        get_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        assert self.s3.check_if_key_exists('index.html') is True
        assert get_object.call_args_list == [
            call(Bucket='my_bucket', Key='index.html'),
        ]

    def test_check_if_key_exists__does_not_exist(self):

        self.mocker.patch.object(
            self.s3.client,
            'get_object'
        ).side_effect = ClientError(
            operation_name='GET_OBJECT',
            error_response={'ResponseMetadata': {'HTTPStatusCode': 404}})

        assert self.s3.check_if_key_exists('index.html') is False

    def test_check_if_key_exists__connection_problem(self):

        self.mocker.patch.object(
            self.s3.client,
            'get_object'
        ).side_effect = [
            ClientError(
                operation_name='GET_OBJECT',
                error_response={'ResponseMetadata': {'HTTPStatusCode': 403}}),
            EndpointConnectionError(endpoint_url='/some/url'),
        ]

        with pytest.raises(click.ClickException) as e:
            self.s3.check_if_key_exists('index.html')

        assert e.value.message == 'faced problems when connecting to AWS S3'

        with pytest.raises(click.ClickException) as e:
            self.s3.check_if_key_exists('index.html')

        assert e.value.message == 'could not connect to bucket specified'

    #
    # UPLOAD_DIR
    #
    def test_upload_dir__makes_the_right_calls(self):

        put_object = self.mocker.patch.object(self.s3.client, 'put_object')

        build_dir = self.tmpdir.mkdir('build')
        build_dir.join('index.html').write('<html>')
        build_dir.join('logo.png').write('abc')
        build_dir.mkdir('assets').join('asset.gif').write('gif.it')

        self.s3.upload_dir(str(build_dir), {'cache-control': 'forever'})

        assert put_object.call_args_list == [
            call(
                ACL='public-read',
                Body=gzip.compress(b'<html>'),
                Bucket='my_bucket',
                CacheControl='forever',
                ContentEncoding='gzip',
                ContentType='text/html',
                Key='index.html'),
            call(
                ACL='public-read',
                Body=gzip.compress(b'abc'),
                Bucket='my_bucket',
                CacheControl='forever',
                ContentEncoding='gzip',
                ContentType='image/png',
                Key='logo.png'),
            call(
                ACL='public-read',
                Body=gzip.compress(b'gif.it'),
                Bucket='my_bucket',
                CacheControl='forever',
                ContentEncoding='gzip',
                ContentType='image/gif',
                Key='assets/asset.gif'),
        ]

    #
    # UPDATE_WEBSITE_INDEX
    #
    def test_update_website_index(self):

        put_bucket_website = self.mocker.patch.object(
            self.s3.client, 'put_bucket_website')
        put_bucket_website.return_value = (
            {'ResponseMetadata': {'HTTPStatusCode': 200}})

        self.s3.update_website_index('index-1.5.6.html')

        assert put_bucket_website.call_args_list == [
            call(
                Bucket='my_bucket',
                WebsiteConfiguration={
                    'IndexDocument': {'Suffix': 'index-1.5.6.html'},
                }),
        ]

    def test_update_website_index__error(self):

        put_bucket_website = self.mocker.patch.object(
            self.s3.client, 'put_bucket_website')
        put_bucket_website.side_effect = ClientError(
            operation_name='put_bucket_website',
            error_response={'ResponseMetadata': {'HTTPStatusCode': 403}})

        with pytest.raises(click.ClickException) as e:
            self.s3.update_website_index('index-1.5.6.html')

        assert e.value.message == 'failed to replace an index document'
