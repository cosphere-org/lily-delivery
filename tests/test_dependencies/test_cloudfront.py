
from unittest import TestCase
from unittest.mock import call

from botocore.exceptions import EndpointConnectionError, ClientError
from freezegun import freeze_time
import click
import pytest

from lily_delivery.dependencies import Cloudfront


class CloudfrontTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):

        self.cloudfront = Cloudfront(
            access_key_id='3489348',
            secret_access_key='382938',
            region_name='east-eu',
            distribution_id='DS09D0S')

    #
    # IS_VALID
    #
    def test_is_valid(self):

        self.mocker.patch.object(
            self.cloudfront.client,
            'get_distribution'
        ).return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        assert self.cloudfront.is_valid() is True

    def test_is_valid__invalid(self):

        self.mocker.patch.object(
            self.cloudfront.client,
            'get_distribution'
        ).side_effect = [
            ClientError(
                operation_name='get_distribution',
                error_response={'ResponseMetadata': {'HTTPStatusCode': 403}}),
            ClientError(
                operation_name='get_distribution',
                error_response={'ResponseMetadata': {'HTTPStatusCode': 404}}),
        ]

        assert self.cloudfront.is_valid() is False
        assert self.cloudfront.is_valid() is False

    def test_is_valid__client_or_connection_problem(self):

        self.mocker.patch.object(
            self.cloudfront.client,
            'get_distribution'
        ).side_effect = [
            ClientError(
                operation_name='get_distribution',
                error_response={'ResponseMetadata': {'HTTPStatusCode': 500}}),
            EndpointConnectionError(endpoint_url='/some/url'),
        ]

        with pytest.raises(click.ClickException) as e:
            self.cloudfront.is_valid()

        assert (
            e.value.message ==
            'faced problems when connecting to AWS CLOUDFRONT')

        with pytest.raises(click.ClickException) as e:
            self.cloudfront.is_valid()

        assert (
            e.value.message ==
            'could not connect to the distribution specified')

    #
    # UPDATE_FRONTEND_ROUTING
    #
    def test_update_frontend_routing__makes_the_right_calls(self):

        get_distribution = self.mocker.patch.object(
            self.cloudfront.client, 'get_distribution')
        get_distribution.return_value = {
            'ETag': 's7f8sd7f',
            'Distribution': {
                'DistributionConfig': {
                    'some': 'config',
                    'CustomErrorResponses': 'no errors',
                }
            }
        }
        update_distribution = self.mocker.patch.object(
            self.cloudfront.client, 'update_distribution')

        self.cloudfront.update_frontend_routing('index-1.5.6.html')

        assert update_distribution.call_args_list == [
            call(
                DistributionConfig={
                    'some': 'config',
                    'CustomErrorResponses': {
                        'Quantity': 1,
                        'Items': [
                            {
                                'ErrorCode': 404,
                                'ResponsePagePath': '/index-1.5.6.html',
                                'ResponseCode': 200,
                                'ErrorCachingMinTTL': 300,
                            },
                        ],
                    },
                },
                Id='DS09D0S',
                IfMatch='s7f8sd7f',
            ),
        ]

    #
    # INVALIDATE_CACHE
    #
    @freeze_time('2018-11-23 15:56:18')
    def test_invalidate_cache__makes_the_right_calls(self):

        create_invalidation = self.mocker.patch.object(
            self.cloudfront.client, 'create_invalidation')

        self.cloudfront.invalidate_cache()

        assert create_invalidation.call_args_list == [
            call(
                DistributionId='DS09D0S',
                InvalidationBatch={
                    'Paths': {
                        'Quantity': 1,
                        'Items': ['/*'],
                    },
                    'CallerReference': '1542988578.0',
                }),
        ]
