
from time import time

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
import click


class Cloudfront:

    def __init__(
            self,
            access_key_id,
            secret_access_key,
            region_name,
            distribution_id):

        self.client = boto3.client(
            'cloudfront',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name)
        self.distribution_id = distribution_id

    def is_valid(self):
        """Validate if connection credentials are correct.

        It will perform it by simple attempting to read the content of the
        distribution.

        """
        try:
            response = self.client.get_distribution(Id=self.distribution_id)

            return response['ResponseMetadata']['HTTPStatusCode'] == 200

        except ClientError as e:
            if e.response['ResponseMetadata']['HTTPStatusCode'] in [403, 404]:
                return False

            else:
                raise click.ClickException(
                    'faced problems when connecting to AWS CLOUDFRONT')

        except EndpointConnectionError:
            raise click.ClickException(
                'could not connect to the distribution specified')

    def update_frontend_routing(self, index_html_key):

        response = self.client.get_distribution(
            Id=self.distribution_id)

        etag = response['ETag']
        current_config = response['Distribution']['DistributionConfig']

        return self.client.update_distribution(
            Id=self.distribution_id,
            IfMatch=etag,
            DistributionConfig={
                **current_config,
                'CustomErrorResponses': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'ErrorCode': 404,
                            'ResponsePagePath': f'/{index_html_key}',
                            'ResponseCode': '200',
                            'ErrorCachingMinTTL': 300
                        },
                    ]
                },
            })

    def invalidate_cache(self):

        self.client.create_invalidation(
            DistributionId=self.distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/*'],
                },
                'CallerReference': str(time())
            })
